from fastapi import APIRouter, HTTPException, Depends
from app.db.mongodb import Database
from bson.objectid import ObjectId
from pydantic import BaseModel
from datetime import datetime
from app.core.auth_middleware import is_admin
from app.models.mlmodel import ModelSchema

router = APIRouter()

# CRUD Operations

@router.post("/", summary="Create a new ML model", dependencies=[Depends(is_admin)])
async def create_ml_model(model: ModelSchema):
    db = Database.client["heart-disease-db"]
    models_collection = db["mlmodels"]

    model_data = model.dict()
    model_data["createdAt"] = datetime.utcnow()

    result = await models_collection.insert_one(model_data)
    return {"id": str(result.inserted_id), **model_data}

@router.get("/", summary="Get all ML models", dependencies=[Depends(is_admin)])
async def get_all_ml_models():
    db = Database.client["heart-disease-db"]
    models_collection = db["mlmodels"]

    models = await models_collection.find({}).to_list(length=100)
    return [
        {
            "id": str(model["_id"]),
            "version": model["version"],
            "status": model["status"],
            "accuracy": model["accuracy"],
            "createdAt": model["createdAt"],
        }
        for model in models
    ]

@router.get("/{model_id}", summary="Get details of a specific ML model", dependencies=[Depends(is_admin)])
async def get_ml_model(model_id: str):
    db = Database.client["heart-disease-db"]
    models_collection = db["mlmodels"]

    if not ObjectId.is_valid(model_id):
        raise HTTPException(status_code=400, detail="Invalid model ID")

    model = await models_collection.find_one({"_id": ObjectId(model_id)})
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return {
        "id": str(model["_id"]),
        "version": model["version"],
        "status": model["status"],
        "accuracy": model["accuracy"],
        "parameters": model["parameters"],
        "performance_metrics": model["performance_metrics"],
        "description": model["description"],
        "createdAt": model["createdAt"],
    }

@router.put("/{model_id}", summary="Update an ML model", dependencies=[Depends(is_admin)])
async def update_ml_model(model_id: str, model: ModelSchema):
    db = Database.client["heart-disease-db"]
    models_collection = db["mlmodels"]

    if not ObjectId.is_valid(model_id):
        raise HTTPException(status_code=400, detail="Invalid model ID")

    result = await models_collection.update_one(
        {"_id": ObjectId(model_id)}, {"$set": model.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"message": "Model updated successfully"}

@router.delete("/{model_id}", summary="Delete an ML model", dependencies=[Depends(is_admin)])
async def delete_ml_model(model_id: str):
    db = Database.client["heart-disease-db"]
    models_collection = db["mlmodels"]

    if not ObjectId.is_valid(model_id):
        raise HTTPException(status_code=400, detail="Invalid model ID")

    result = await models_collection.delete_one({"_id": ObjectId(model_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"message": "Model deleted successfully"}
