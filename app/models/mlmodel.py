from pydantic import BaseModel
from datetime import datetime

class ModelParameters(BaseModel):
    learning_rate: float
    epochs: int
    batch_size: int

class PerformanceMetrics(BaseModel):
    precision: float
    recall: float
    f1_score: float

class ModelSchema(BaseModel):
    version: str
    model_url: str
    accuracy: float
    parameters: ModelParameters
    performance_metrics: PerformanceMetrics
    status: str  # "active" or "archived"
    description: str
    createdAt: datetime | None
