from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer
from app.core.security import decode_access_token
from bson import ObjectId
from app.db.mongodb import Database

auth_scheme = HTTPBearer()

async def get_current_user(token: str = Depends(auth_scheme)):
    # Decode the token to get the payload
    payload = decode_access_token(token.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("user_id")
    if not user_id or not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=401, detail="Invalid token payload")

    # Fetch the user from the database
    db = Database.client["heart-disease-db"]
    users_collection = db["users"]
    user = await users_collection.find_one({"_id": ObjectId(user_id)})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
 
    return user

async def is_moderator(user: dict = Depends(get_current_user)):
    if user.get("role") != "moderator":
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return user

async def is_admin(user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return user
