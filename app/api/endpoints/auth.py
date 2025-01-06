from fastapi import APIRouter, HTTPException, Depends
from app.db.mongodb import Database
from app.core.security import verify_password, hash_password, create_access_token
from pydantic import BaseModel
from app.models.user import UserLogin, UserRegister, UserSchema
from datetime import datetime
router = APIRouter()


@router.post("/register", summary="Register a new user")
async def register_user(user: UserRegister):
    db = Database.client["heart-disease-db"]
    users_collection = db["users"]

    # Check if email is already registered
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email is already registered")

    # Hash password and insert user
    hashed_password = hash_password(user.password)
    user_data = {
        "email": user.email,
        "password": hashed_password,
        "role": "user",
        "createdBy": None,
        "isBlocked": False,
        "createdAt": datetime.utcnow(),
    }
    result = await users_collection.insert_one(user_data)
    return {"id": str(result.inserted_id), "email": user.email}

@router.post("/login", summary="Authenticate and get JWT token")
async def login_user(user: UserLogin):
    db = Database.client["heart-disease-db"]
    users_collection = db["users"]

    # Check if user exists
    db_user = await users_collection.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Generate token
    token = create_access_token({"user_id": str(db_user["_id"]), "role": db_user["role"]})
    return {"access_token": token, "token_type": "bearer"}
 