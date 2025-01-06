from pydantic import BaseModel, Field
from datetime import datetime
from app.models.pydantic_objectid import PydanticObjectId

class Diagnosis(BaseModel):
    result: str = Field(..., description="Result string response")
    confidence: float = Field(..., description="ML model confidence (0-1)")

class PredictionSchema(BaseModel):
    userId: PydanticObjectId
    imageUrl: str
    prediction: Diagnosis
    notes: str | None
    createdAt: datetime
    model_config = {
        "arbitrary_types_allowed": True,
    }