from fastapi import FastAPI
from app.db.mongodb import Database
from app.core.config import settings
from app.api.routes import api_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Heart Disease Prediction API")


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

@app.on_event("shutdown")
async def shutdown_event():
    await Database.close_mongo_connection()

app.include_router(api_router)
