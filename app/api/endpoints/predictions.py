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
from app.models.prediction import PredictionSchema
import shutil
from pathlib import Path
from app.ml.model import AttentionModule 

router = APIRouter()
UPLOAD_DIRECTORY = Path("uploaded_images")
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)

# Load the trained model (preloaded when the app starts)
MODEL_PATH = "ecg_attention_cnn.h5"
classnames = ['History of MI', 'Myocardial Infarction', 'Normal', 'abnormal heartbeat']
try:
    model = tf.keras.models.load_model(MODEL_PATH, custom_objects={"AttentionModule": AttentionModule})
    print("Model loaded successfully.")
except Exception as e:
    raise RuntimeError(f"Failed to load model from {MODEL_PATH}: {e}")

# Helper function to preprocess image
def preprocess_image(image: Image.Image) -> np.ndarray:
    # Resize image to match the model's expected size
    image = image.resize((128, 128))  # Change to match model's input shape

    # Convert image to grayscale if it's not already
    if image.mode != "L":  # "L" mode is for grayscale
        image = image.convert("L")

    # Normalize pixel values and add batch dimension
    image_array = np.array(image) / 255.0  # Normalize to [0, 1]
    image_array = np.expand_dims(image_array, axis=-1)  # Add channel dimension
    return np.expand_dims(image_array, axis=0)  # Add batch dimension


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
        confidence = float(predictions[0][predicted_class])  # Convert to Python float
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
            "prediction": pred["prediction"],
            "createdAt": pred["createdAt"],
        }
        for pred in predictions
    ]
    return formatted_predictions