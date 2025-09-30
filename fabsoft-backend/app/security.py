# app/security.py

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from .config import settings

# Create password context with fallback options
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    # Test if bcrypt actually works by trying a simple hash
    test_hash = pwd_context.hash("test")
    pwd_context.verify("test", test_hash)
except Exception as e:
    # If bcrypt fails during initialization or testing, fall back to scrypt
    print(f"Warning: bcrypt failed ({e}), falling back to scrypt")
    pwd_context = CryptContext(schemes=["scrypt"], deprecated="auto")

def _truncate_password_safely(password: str, max_bytes: int = 72) -> str:
    """
    Safely truncate a password to fit within the byte limit while preserving UTF-8 encoding.
    """
    password_bytes = password.encode('utf-8')
    if len(password_bytes) <= max_bytes:
        return password
    
    # Truncate to max_bytes and ensure we don't break UTF-8 encoding
    password_bytes = password_bytes[:max_bytes]
    
    # Try to decode, and if it fails due to incomplete character, remove bytes until it works
    while len(password_bytes) > 0:
        try:
            return password_bytes.decode('utf-8')
        except UnicodeDecodeError:
            password_bytes = password_bytes[:-1]
    
    # Fallback if everything fails (should never happen with reasonable input)
    return password[:max_bytes]

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Safely truncate password if it's too long for bcrypt
    plain_password = _truncate_password_safely(plain_password)
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    # Safely truncate password if it's too long for bcrypt
    password = _truncate_password_safely(password)
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt