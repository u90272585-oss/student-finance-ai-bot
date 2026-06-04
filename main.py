from fastapi import FastAPI, Depends, HTTPException, status
from typing import List
from database import Database
from auth import AuthHandler
from dependencies import (
    get_db, get_current_user, get_current_user_id,
    require_admin, require_premium, OwnershipChecker
)
from schemas import (
    UserRegister, UserLogin, TokenResponse,
    TransactionCreate, TransactionResponse,
    GoalCreate, GoalProgress
)


app = FastAPI(title="Finance Bot API")


# ========== АУТЕНТИФИКАЦИЯ ==========

@app.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserRegister, db: Database = Depends(get_db)):
    """Регистрация пользователя с валидацией пароля"""
    # Проверка уникальности
    existing = db.get_user_by_username(user_data.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    existing_email = db.get_user_by_email(user_data.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Хеширование пароля
    hashed_password = AuthHandler.hash_password(user_data.password)
    
    # Создание пользователя
    user_id = db.create_user(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password
    )
    
    # Создание токенов
    access_token = AuthHandler.create_access_token({"sub": str(user_id)})
    refresh_token = AuthHandler.create_refresh_token({"sub": str(user_id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 1800
    }


@app.post("/auth/login", response_model=TokenResponse)
async def login(user_data: UserLogin, db: Database = Depends(get_db)):
    """Логин пользователя"""
    user = db.get_user_by_username(user_data.username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not AuthHandler.verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Обновляем время последнего входа
    db.update_last_login(user["user_id"])
    
    # Создание токенов
    access_token = AuthHandler.create_access_token({"sub": str(user["user_id"])})
    refresh_token = AuthHandler.create_refresh_token({"sub": str(user["user_id"])})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 1800
    }


# ========== ТРАНЗАКЦИИ (С ПРОВЕРКОЙ ВЛАДЕНИЯ) ==========

@app.post("/transactions", response_model=dict)
async def create_transaction(
    transaction: TransactionCreate,
    user_id: int = Depends(get_current_user_id),
    db: Database = Depends(get_db)
):
    """Создание транзакции"""
    transaction_id = db.add_transaction(
        user_id=user_id,
        trans_type=transaction.type,
        amount=transaction.amount,
        category=transaction.category,
        note=transaction.note or ""
    )
    return {"id": transaction_id, "message": "Transaction created"}


@app.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    user_id: int = Depends(get_current_user_id),
    db: Database = Depends(get_db)
):
    """Получение всех транзакций пользователя"""
    transactions = db.get_all_transactions(user_id)
    return transactions


@app.delete("/transactions/{transaction_id}")
async def delete_transaction(
    transaction_id: int,
    _: int = Depends(OwnershipChecker.check_transaction_owner),
    db: Database = Depends(get_db)
):
    """Удаление транзакции с проверкой владения"""
    # Проверка владения уже выполнена в OwnershipChecker
    db.delete_transaction(transaction_id, _)  # _ содержит user_id
    return {"message": "Transaction deleted"}


# ========== АДМИНКА (ТОЛЬКО ДЛЯ АДМИНОВ) ==========

@app.get("/admin/users")
async def get_all_users(
    _: dict = Depends(require_admin),  # Только админы!
    db: Database = Depends(get_db),
    admin_id: int = Depends(get_current_user_id)
):
    """Получение всех пользователей - ТОЛЬКО ДЛЯ АДМИНОВ"""
    users = db.get_all_users(admin_id)
    return {"users": users}


@app.post("/admin/users/{target_user_id}/role")
async def set_user_role(
    target_user_id: int,
    role: str,
    _: dict = Depends(require_admin),  # Только админы!
    db: Database = Depends(get_db),
    admin_id: int = Depends(get_current_user_id)
):
    """Изменение роли пользователя - ТОЛЬКО ДЛЯ АДМИНОВ"""
    success = db.set_user_role(admin_id, target_user_id, role)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to set role")
    return {"message": f"Role updated to {role}"}


# ========== ПРЕМИУМ КОНТЕНТ ==========

@app.get("/premium/content")
async def get_premium_content(
    _: int = Depends(require_premium)  # Только премиум!
):
    """Эндпоинт только для премиум пользователей"""
    return {
        "message": "This is premium content",
        "tips": ["Специальные советы для премиум пользователей"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)