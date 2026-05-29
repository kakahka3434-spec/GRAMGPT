"""
Authentication service for GRAMGPT.
Handles JWT token generation, verification, and password hashing.
"""

import os
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
import sqlite3
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)

# ============ CONFIGURATION ============
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
except Exception:
    logger.warning("bcrypt unavailable — password hashing disabled")
    pwd_context = None

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


class AuthService:
    """Service for authentication operations."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt."""
        if pwd_context is None:
            raise RuntimeError("Password hashing unavailable (bcrypt not loaded)")
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        """Verify plain password against hashed version."""
        if pwd_context is None:
            raise RuntimeError("Password hashing unavailable (bcrypt not loaded)")
        return pwd_context.verify(plain, hashed)
    
    @staticmethod
    def create_tokens(user_id: str, email: str) -> tuple:
        """
        Create access and refresh tokens for user.
        
        Returns:
            tuple: (access_token, refresh_token)
        """
        # Access token (15 minutes)
        access_data = {
            "sub": user_id,
            "email": email,
            "type": "access",
            "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        }
        access_token = jwt.encode(access_data, SECRET_KEY, algorithm=ALGORITHM)
        
        # Refresh token (7 days)
        refresh_data = {
            "sub": user_id,
            "type": "refresh",
            "exp": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        }
        refresh_token = jwt.encode(refresh_data, SECRET_KEY, algorithm=ALGORITHM)
        
        logger.info(f"✅ Tokens created for user {user_id}")
        return access_token, refresh_token
    
    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """
        Verify JWT token and return payload if valid.
        
        Returns:
            dict: Token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # Check if token type is "access"
            if payload.get("type") != "access":
                logger.warning("❌ Token type is not 'access'")
                return None
            
            return payload
        except JWTError as e:
            logger.warning(f"❌ JWT verification failed: {str(e)}")
            return None


# Singleton instance
auth_service = AuthService()
