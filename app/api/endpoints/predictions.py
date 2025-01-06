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
from app.core.auth_middleware import is_admin, get_current_user
from app.models.prediction import PredictionSchema
# from app.ml.model import get_prediction
import shutil
from pathlib import Path

router = APIRouter()
UPLOAD_DIRECTORY = "uploaded_images"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

# Load the trained model (preloaded when the app starts)
# MODEL_PATH = "path_to_your_model/model.h5"
# model = tf.keras.models.load_model(MODEL_PATH)

# Helper function to preprocess image
def preprocess_image(image: Image.Image) -> np.ndarray:
    image = image.resize((224, 224))  # Adjust size as per your model input
    image_array = np.array(image) / 255.0  # Normalize pixel values
    if len(image_array.shape) == 2:  # If grayscale, expand dims
        image_array = np.expand_dims(image_array, axis=-1)
    return np.expand_dims(image_array, axis=0)  # Add batch dimension

@router.post("/upload", summary="Upload an ECG image and get prediction")
async def upload_ecg_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),  # Get user from token
):
    # Validate file type
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG/PNG allowed.")
    
    user_id = str(current_user["_id"])
    
    # Open the uploaded file as an image
    # try:
    #     image = Image.open(io.BytesIO(await file.read()))
    # except Exception:
    #     raise HTTPException(status_code=400, detail="Unable to process the uploaded image.")
    file_path = os.path.join(UPLOAD_DIRECTORY, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    # Preprocess image and predict
    # preprocessed_image = preprocess_image(image)
    # predictions = model.predict(preprocessed_image)
    # predicted_class = np.argmax(predictions[0])  # Assuming classification model
    # confidence = predictions[0][predicted_class]

    # Store the prediction in the database
    db = Database.client["heart-disease-db"]
    predictions_collection = db["predictions"]
    prediction = PredictionSchema(
        userId=user_id,
        imageUrl=file_path,
        prediction={"result": "MockResult", "confidence": 0.98},
        notes=None,
        createdAt=datetime.utcnow(),
    )
    result = await predictions_collection.insert_one(prediction.dict())

    return JSONResponse(
        status_code=200,
        content={
            "predictionId": str(result.inserted_id),
            "result": prediction.prediction.result ,
            "confidence": prediction.prediction.confidence,
        },
    )

@router.get("/", summary="Get all predictions", dependencies=[Depends(is_admin)])
async def get_all_predictions():
    db = Database.client["heart-disease-db"]
    predictions_collection = db["predictions"]

    predictions = await predictions_collection.find({}).to_list(length=100)
    return predictions

@router.get("/image/{filename}", summary="Retrieve uploaded image")
async def get_uploaded_image(filename: str):
    file_path = os.path.join(UPLOAD_DIRECTORY, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path)

@router.delete("/image/{filename}", summary="Delete an uploaded image", dependencies=[Depends(is_admin)])
async def delete_uploaded_image(filename: str):
    file_path = os.path.join(UPLOAD_DIRECTORY, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    os.remove(file_path)
    return {"message": f"File '{filename}' deleted successfully"}

@router.get("/images", summary="List all uploaded images", dependencies=[Depends(is_admin)])
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