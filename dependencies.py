# dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Generator
import jwt
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-me")
ALGORITHM = "HS256"

security = HTTPBearer(auto_error=False)


def get_db() -> Generator:
    """Dependency для получения БД"""
    from database import Database
    db = Database()
    try:
        yield db
    finally:
        pass  # Не закрываем сразу, т.к. нужно для всего запроса


async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> int:
    """Получение user_id из JWT токена"""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return int(user_id)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")