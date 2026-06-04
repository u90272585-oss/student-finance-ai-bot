from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional
from datetime import datetime
import re


# ========== ВАЛИДАЦИЯ ПАРОЛЕЙ (OWASP A07) ==========

class PasswordValidator:
    """Строгая валидация паролей по OWASP A07"""
    
    @staticmethod
    def validate(password: str) -> tuple[bool, str]:
        """
        Проверка сложности пароля:
        - Минимум 8 символов
        - Максимум 64 символа
        - Хотя бы одна заглавная буква
        - Хотя бы одна строчная буква
        - Хотя бы одна цифра
        - Хотя бы один спецсимвол (!@#$%^&*)
        - Без пробелов
        """
        if len(password) < 8:
            return False, "Пароль должен содержать минимум 8 символов"
        
        if len(password) > 64:
            return False, "Пароль не должен превышать 64 символа"
        
        if " " in password:
            return False, "Пароль не должен содержать пробелов"
        
        if not re.search(r"[A-Z]", password):
            return False, "Пароль должен содержать хотя бы одну заглавную букву"
        
        if not re.search(r"[a-z]", password):
            return False, "Пароль должен содержать хотя бы одну строчную букву"
        
        if not re.search(r"\d", password):
            return False, "Пароль должен содержать хотя бы одну цифру"
        
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False, "Пароль должен содержать хотя бы один спецсимвол (!@#$%^&*)"
        
        return True, "OK"


# ========== СХЕМЫ ДЛЯ АУТЕНТИФИКАЦИИ ==========

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=64)
    
    @validator('password')
    def validate_password(cls, v):
        is_valid, message = PasswordValidator.validate(v)
        if not is_valid:
            raise ValueError(message)
        return v
    
    @validator('username')
    def validate_username(cls, v):
        if v.lower() in ['admin', 'root', 'system']:
            raise ValueError('Недопустимое имя пользователя')
        return v


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# ========== СХЕМЫ ДЛЯ ТРАНЗАКЦИЙ ==========

class TransactionCreate(BaseModel):
    type: str = Field(..., pattern=r"^(income|expense)$")
    amount: float = Field(..., gt=0, le=1_000_000_000)
    category: str = Field(..., min_length=1, max_length=50)
    note: Optional[str] = Field(None, max_length=500)
    
    @validator('category')
    def validate_category(cls, v):
        allowed = ['food', 'transport', 'housing', 'entertainment', 'healthcare', 
                   'education', 'shopping', 'bills', 'other']
        if v.lower() not in allowed:
            raise ValueError(f'Категория должна быть одной из: {", ".join(allowed)}')
        return v.lower()


class TransactionUpdate(BaseModel):
    type: Optional[str] = Field(None, pattern=r"^(income|expense)$")
    amount: Optional[float] = Field(None, gt=0, le=1_000_000_000)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    note: Optional[str] = Field(None, max_length=500)


class TransactionResponse(BaseModel):
    id: int
    user_id: int
    type: str
    amount: float
    category: str
    note: Optional[str]
    date: datetime


# ========== СХЕМЫ ДЛЯ ЦЕЛЕЙ ==========

class GoalCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    target: float = Field(..., gt=0, le=1_000_000_000)


class GoalUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    target: Optional[float] = Field(None, gt=0, le=1_000_000_000)
    current: Optional[float] = Field(None, ge=0)


class GoalProgress(BaseModel):
    amount: float = Field(..., gt=0, le=1_000_000_000)


# ========== СХЕМЫ ДЛЯ ОБЩИХ ЦЕЛЕЙ ==========

class SharedGoalCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    target: float = Field(..., gt=0, le=1_000_000_000)


class SharedGoalJoin(BaseModel):
    invite_code: str = Field(..., min_length=6, max_length=20)


class SharedGoalContribute(BaseModel):
    amount: float = Field(..., gt=0, le=1_000_000_000)


# ========== СХЕМЫ ДЛЯ ОШИБОК ==========

class ErrorResponse(BaseModel):
    detail: str
    status_code: int


class ValidationErrorResponse(BaseModel):
    detail: dict
    status_code: int = 422