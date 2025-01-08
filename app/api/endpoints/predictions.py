from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse, FileResponse
from app.db.mongodb import Database
from bson.objectid import ObjectId
from datetime import datetime
from PIL import Image
import numpy as np
import tensorflow as tf
import io
import os
from app.core.auth_middleware import is_moderator, get_current_user
from app.models.prediction import PredictionSchema, NoteUpdate
import shutil
from pathlib import Path
from keras.utils import load_img

router = APIRouter()
UPLOAD_DIRECTORY = Path("uploaded_images")
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)

# Load the trained model (preloaded when the app starts)
MODEL_PATH = "ResNet50ecg50epoch.h5"
classnames = ['History of MI', 'Myocardial Infarction', 'Normal', 'abnormal heartbeat']
try:
    model = tf.keras.models.load_model(MODEL_PATH)
    print("Model loaded successfully.")
except Exception as e:
    raise RuntimeError(f"Failed to load model from {MODEL_PATH}: {e}")

# Helper function to preprocess image
def preprocess_image(image: Image.Image) -> np.ndarray:
    # Ensure the image is RGB (3 channels)
    image = image.resize((224, 224))  # Resize to model's expected input dimensions
    # image_array = np.array(image) / 255.0  # Normalize pixel values to [0, 1]
    # return np.expand_dims(image_array, axis=0)
    # img1 = load_img('PMI(11).jpg', target_size=(224,224))
    img1 = np.asarray(image)
    img1 = np.expand_dims(image, axis=0)  # Add batch dimension
    return img1


@router.post("/upload", summary="Upload an ECG image and get prediction")
async def upload_ecg_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    # Validate file type
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG/PNG allowed.")
    
    user_id = str(current_user["_id"])
    
    # Save file
    file_path = os.path.join(UPLOAD_DIRECTORY, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Open and preprocess the image
    try:
        image = Image.open(file_path)
        preprocessed_image = preprocess_image(image)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {e}")

    # Predict using the model
    try:
        predictions = model.predict(preprocessed_image)
        predicted_class = int(np.argmax(predictions[0]))  # Convert to Python int
        confidence = int(round(predictions[0][predicted_class]))  # Convert to Python float
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {e}")

    # Store the prediction in the database
    db = Database.client["heart-disease-db"]
    predictions_collection = db["predictions"]
    prediction = PredictionSchema(
        userId=user_id,
        imageUrl=file.filename,
        prediction={
            "result": classnames[predicted_class],  # Ensure this is a string
            "confidence": confidence
        },
        notes=None,
        createdAt=datetime.utcnow(),
    )
    result = await predictions_collection.insert_one(prediction.dict())

    # Return the response
    return JSONResponse(
        status_code=200,
        content={
            "predictionId": str(result.inserted_id),
            "result": classnames[predicted_class],
            "confidence": confidence,
        },
    )

@router.get("/", summary="Get all predictions", dependencies=[Depends(is_moderator)])
async def get_all_predictions():
    db = Database.client["heart-disease-db"]
    predictions_collection = db["predictions"]

    predictions = await predictions_collection.find({}).to_list(length=100)
    # Format predictions to ensure JSON serializability
    formatted_predictions = [
        {
            "id": str(pred["_id"]),
            "userId": str(pred["userId"]),
            "imageUrl": pred["imageUrl"],
            "prediction": pred["prediction"],
            "notes": pred.get("notes"),
            "createdAt": pred["createdAt"].isoformat() if "createdAt" in pred else None,
        }
        for pred in predictions
    ]
    return formatted_predictions

@router.get("/image/{filename}", summary="Retrieve uploaded image")
async def get_uploaded_image(filename: str):
    file_path = os.path.join(UPLOAD_DIRECTORY, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path)

@router.delete("/image/{filename}", summary="Delete an uploaded image", dependencies=[Depends(is_moderator)])
async def delete_uploaded_image(filename: str):
    file_path = os.path.join(UPLOAD_DIRECTORY, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    os.remove(file_path)
    return {"message": f"File '{filename}' deleted successfully"}

@router.get("/images", summary="List all uploaded images", dependencies=[Depends(is_moderator)])
async def list_uploaded_images():
    files = os.listdir(UPLOAD_DIRECTORY)
    return {"files": files}

@router.get("/{user_id}", summary="Get all predictions for a user")
async def get_user_predictions(user_id: str):
    # Ensure the user_id is valid
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")

    db = Database.client["heart-disease-db"]
    predictions_collection = db["predictions"]

    # Fetch predictions from the database
    predictions = await predictions_collection.find({"userId": ObjectId(user_id)}).to_list(length=100)

    # Format the response
    formatted_predictions = [
        {
            "id": str(pred["_id"]),
            "userId": str(pred["userId"]),
            "imageUrl": pred["imageUrl"],
            "notes": pred["notes"],
            "prediction": pred["prediction"],
            "createdAt": pred["createdAt"],
        }
        for pred in predictions
    ]
    return formatted_predictions

@router.patch("/{prediction_id}", summary="Update notes for a prediction")
async def update_prediction_notes(prediction_id: str,note_update: NoteUpdate,current_user: dict = Depends(get_current_user)):
    db = Database.client["heart-disease-db"]
    predictions_collection = db["predictions"]

    # Ensure the prediction ID is valid
    if not ObjectId.is_valid(prediction_id):
        raise HTTPException(status_code=400, detail="Invalid prediction ID.")

    # Find the prediction and ensure the current user is authorized
    prediction = await predictions_collection.find_one({"_id": ObjectId(prediction_id)})
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found.")
    if str(prediction["userId"]) != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Unauthorized to update this prediction.")

    # Update the notes field
    result = await predictions_collection.update_one(
        {"_id": ObjectId(prediction_id)},
        {"$set": {"notes": note_update.notes}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Prediction not found.")
    
    return {"message": "Notes updated successfully."}