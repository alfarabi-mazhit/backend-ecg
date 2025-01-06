from pydantic import BaseModel, EmailStr
from datetime import datetime
from enum import Enum
from app.models.pydantic_objectid import PydanticObjectId

class UserLogin(BaseModel):
    email: str
    password: str

class UserRegister(UserLogin):
    pass

class UserRole(str, Enum):
    USER = "user"
    MODERATOR = "moderator"

class UserSchema(BaseModel):
    email: EmailStr
    password: str
    role: UserRole
    createdBy: PydanticObjectId | None
    isBlocked: bool
    createdAt: datetime
    model_config = {
        "arbitrary_types_allowed": True,
    }
