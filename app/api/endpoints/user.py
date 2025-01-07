from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from bson.objectid import ObjectId
from app.db.mongodb import Database
from app.core.auth_middleware import is_moderator, get_current_user

router = APIRouter()

# Pydantic models
class UserUpdate(BaseModel):
    email: str = None
    role: str = None  # Enum: 'user', 'moderator', 'admin'
    isBlocked: bool = None

@router.get("/me", summary="Get current user details")
async def get_current_user_details(current_user: dict = Depends(get_current_user)):
    return {
        "id": str(current_user["_id"]),
        "email": current_user["email"],
        "role": current_user["role"],
    }

@router.get("/{user_id}", summary="Get user details", dependencies=[Depends(is_moderator)])
async def get_user(user_id: str):
    db = Database.client["heart-disease-db"]
    users_collection = db["users"]

    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "role": user["role"],
        "isBlocked": user["isBlocked"],
        "createdAt": user["createdAt"],
    }

@router.patch("/{user_id}", summary="Update user details", dependencies=[Depends(is_moderator)])
async def update_user(user_id: str, updates: UserUpdate):
    db = Database.client["heart-disease-db"]
    users_collection = db["users"]

    # Filter out None values to only update provided fields
    update_data = {k: v for k, v in updates.dict().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided.")

    result = await users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User updated successfully", "updated_fields": update_data}

@router.delete("/{user_id}", summary="Delete user", dependencies=[Depends(is_moderator)])
async def delete_user(user_id: str):
    db = Database.client["heart-disease-db"]
    users_collection = db["users"]

    result = await users_collection.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

@router.get("/", summary="Get all users", dependencies=[Depends(is_moderator)])
async def get_all_users():
    db = Database.client["heart-disease-db"]
    users_collection = db["users"]

    users = await users_collection.find({}).to_list(length=100)
    return [
        {
            "id": str(user["_id"]),
            "email": user["email"],
            "role": user["role"],
            "isBlocked": user["isBlocked"],
            "createdAt": user["createdAt"],
        }
        for user in users
    ]

@router.patch("/{user_id}/block", summary="Block or unblock a user", dependencies=[Depends(is_moderator)])
async def block_unblock_user(user_id: str, block: bool):
    db = Database.client["heart-disease-db"]
    users_collection = db["users"]

    result = await users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"isBlocked": block}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    action = "blocked" if block else "unblocked"
    return {"message": f"User {action} successfully"}