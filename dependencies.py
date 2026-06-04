from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Generator
from contextlib import contextmanager

from auth import AuthHandler
from database import Database


# Security схемы
security = HTTPBearer(auto_error=False)


# Функция для получения экземпляра БД
def get_db() -> Generator[Database, None, None]:
    """
    Dependency для получения соединения с БД.
    Использует генератор для автоматического закрытия соединения.
    """
    db = Database()
    try:
        yield db
    finally:
        db.close()


# ========== ОСНОВНЫЕ DEPENDENCIES ==========

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Database = Depends(get_db)
) -> Dict:
    """
    Получение текущего пользователя из JWT токена.
    Возвращает 401 если токен невалидный.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    user_id = AuthHandler.get_user_id_from_token(token)
    
    user = db.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account disabled",
        )
    
    return user


async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Database = Depends(get_db)
) -> int:
    """Получение только user_id из токена"""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    token = credentials.credentials
    user_id = AuthHandler.get_user_id_from_token(token)
    
    # Проверяем, существует ли пользователь
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user_id


async def get_current_active_user(
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """Проверка, что пользователь активен"""
    if not current_user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return current_user


# ========== RBAC DEPENDENCIES ==========

async def require_admin(
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """
    Проверка прав администратора.
    Возвращает 403 Forbidden для обычных пользователей.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


async def require_premium(
    current_user_id: int = Depends(get_current_user_id),
    db: Database = Depends(get_db)
) -> int:
    """
    Проверка премиум статуса.
    Возвращает 403 если нет премиума.
    """
    is_premium = db.is_premium(current_user_id)
    if not is_premium:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium subscription required",
        )
    return current_user_id


async def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Database = Depends(get_db)
) -> Optional[Dict]:
    """
    Опциональная аутентификация - не требует токен,
    но если он есть, то проверяет его валидность.
    """
    if credentials is None:
        return None
    
    try:
        token = credentials.credentials
        user_id = AuthHandler.get_user_id_from_token(token)
        user = db.get_user_by_id(user_id)
        return user
    except HTTPException:
        return None


# ========== DEPENDENCY ДЛЯ ПРОВЕРКИ ВЛАДЕНИЯ РЕСУРСОМ ==========

class OwnershipChecker:
    """Класс для проверки владения ресурсами"""
    
    @staticmethod
    async def check_transaction_owner(
        transaction_id: int,
        current_user_id: int = Depends(get_current_user_id),
        db: Database = Depends(get_db)
    ) -> int:
        """
        Проверка, что транзакция принадлежит текущему пользователю.
        Возвращает user_id если проверка пройдена.
        """
        transaction = db.get_transaction(transaction_id, current_user_id)
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found or access denied",
            )
        return current_user_id
    
    @staticmethod
    async def check_goal_owner(
        goal_id: int,
        current_user_id: int = Depends(get_current_user_id),
        db: Database = Depends(get_db)
    ) -> int:
        """
        Проверка, что цель принадлежит текущему пользователю.
        """
        goal = db.get_goal(goal_id, current_user_id)
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Goal not found or access denied",
            )
        return current_user_id
    
    @staticmethod
    async def check_shared_goal_member(
        goal_id: int,
        current_user_id: int = Depends(get_current_user_id),
        db: Database = Depends(get_db)
    ) -> int:
        """
        Проверка, что пользователь является участником общей цели.
        """
        shared_goals = db.get_user_shared_goals(current_user_id)
        if not any(g["id"] == goal_id for g in shared_goals):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this shared goal",
            )
        return current_user_id


# Альтернативный вариант без генератора (если не нужен контекстный менеджер)
def get_db_simple() -> Database:
    """
    Простой вариант без генератора.
    Внимание: соединение нужно закрывать вручную!
    """
    return Database()