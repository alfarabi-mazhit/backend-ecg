# app/core/security.py
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# JWT token creation
def create_access_token(data: dict, expires_delta: int = settings.jwt_expires_in):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=expires_delta)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm="HS256")

# JWT token decoding
def decode_access_token(token: str):
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.JWTError:
        return None
