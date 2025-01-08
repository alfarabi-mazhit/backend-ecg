from fastapi import FastAPI
from app.db.mongodb import Database
from app.core.config import settings
from app.api.routes import api_router
from app.ml.model import ModelManager
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="Heart Disease Prediction API")

MODEL_PATH = os.path.join(os.path.dirname(__file__), "../ResNet50ecg50epoch.h5")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    await Database.connect_to_mongo(settings.mongodb_uri)
    ModelManager.load_model(MODEL_PATH)

@app.on_event("shutdown")
async def shutdown_event():
    await Database.close_mongo_connection()

app.include_router(api_router) 
