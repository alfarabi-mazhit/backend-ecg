import sys
from pathlib import Path
from bson.objectid import ObjectId
from passlib.hash import bcrypt
from datetime import datetime
import asyncio

# Add the root directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from mongodb import Database

async def seed_moderator():
    try:
        # Connect to the MongoDB database
        await Database.connect_to_mongo("mongodb://localhost:27017")  # Replace with your MongoDB URI

        db = Database.client["heart-disease-db"]
        users_collection = db["users"]

        # Moderator details
        moderator_data = {
            "_id": ObjectId(),
            "email": "moderator@example.com",
            "password": bcrypt.hash("password123"),  # Replace with a secure password
            "role": "moderator",
            "isBlocked": False,
            "createdAt": datetime.utcnow(),
        }

        # Check if the moderator already exists
        existing_user = await users_collection.find_one({"email": moderator_data["email"]})
        if existing_user:
            print("Moderator already exists.")
        else:
            await users_collection.insert_one(moderator_data)
            print("Moderator created successfully.")
    finally:
        # Close the MongoDB connection
        await Database.close_mongo_connection()

# Run the seeding script
if __name__ == "__main__":
    asyncio.run(seed_moderator())
