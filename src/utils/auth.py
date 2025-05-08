"""Authentication Utilities

This module provides authentication utilities for the VidID API.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.db.models import User

logger = logging.getLogger(__name__)

# Constants for JWT authentication
SECRET_KEY = "YOUR_SECRET_KEY_HERE"  # Should be loaded from environment variables
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.
    
    Args:
        plain_password: Plain password to verify
        hashed_password: Hashed password to compare against
        
    Returns:
        True if the password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate a password hash.
    
    Args:
        password: Password to hash
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional time delta for token expiration
        
    Returns:
        JWT token as a string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate a user by username and password.
    
    Args:
        db: Database session
        username: Username to authenticate
        password: Password to verify
        
    Returns:
        User object if authentication succeeds, None otherwise
    """
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        return None
        
    if not verify_password(password, user.password_hash):
        return None
        
    return user


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends()) -> User:
    """Get the current user from a JWT token.
    
    Args:
        token: JWT token
        db: Database session
        
    Returns:
        User object if token is valid
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise credentials_exception
            
    except InvalidTokenError:
        logger.warning("Invalid token provided")
        raise credentials_exception
        
    user = db.query(User).filter(User.username == username).first()
    
    if user is None:
        logger.warning(f"User {username} not found")
        raise credentials_exception
        
    # Update last login time
    user.last_login = datetime.utcnow()
    db.commit()
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current user and verify that they are active.
    
    Args:
        current_user: Current user from get_current_user
        
    Returns:
        User object if user is active
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    return current_user


async def get_current_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Get the current user and verify that they are an admin.
    
    Args:
        current_user: Current user from get_current_active_user
        
    Returns:
        User object if user is an admin
        
    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return current_user


async def get_optional_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends()) -> Optional[User]:
    """Get the current user from a JWT token, but don't require authentication.
    
    This is useful for endpoints that can be accessed both by authenticated and anonymous users.
    
    Args:
        token: JWT token (optional)
        db: Database session
        
    Returns:
        User object if token is valid, None otherwise
    """
    if token is None:
        return None
        
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except (InvalidTokenError, jwt.PyJWTError):
        return None
        
    user = db.query(User).filter(User.username == username).first()
    return user
