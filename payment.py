import os
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

# Создаём роутер один раз (без префикса, он добавится в bot.py)
router = APIRouter()

# Берем секреты из .env
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
PAYPAL_BASE_URL = "https://api-m.sandbox.paypal.com"


# ===== МОДЕЛИ ДЛЯ ЗАПРОСОВ =====

class OrderRequest(BaseModel):
    amount: Optional[str] = "2.90"
    currency: Optional[str] = "USD"
    description: Optional[str] = "CoinMind Premium"

class ActivatePremiumRequest(BaseModel):
    user_id: int
    order_id: str


# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

async def get_paypal_access_token() -> str:
    """Получение токена от PayPal"""
    url = f"{PAYPAL_BASE_URL}/v1/oauth2/token"
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en_US",
    }
    data = {"grant_type": "client_credentials"}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url, 
            headers=headers, 
            data=data, 
            auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET)
        )
        
    if response.status_code != 200:
        print(f"❌ Ошибка авторизации PayPal: {response.text}")
        raise HTTPException(status_code=401, detail="PayPal Auth Failed")
        
    return response.json().get("access_token")


# ===== ЭНДПОИНТЫ =====

@router.post("/api/orders")
async def create_order(payload: OrderRequest):
    """Создание заказа в PayPal"""
    try:
        access_token = await get_paypal_access_token()
        
        # Конвертация KZT → USD
        currency = payload.currency
        amount = payload.amount
        
        if currency in ["KZT", "₸", "kzt"]:
            currency = "USD"
            amount = "0.65"  # 290 тенге ≈ $0.65
            
        url = f"{PAYPAL_BASE_URL}/v2/checkout/orders"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        
        body = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {
                    "currency_code": currency,
                    "value": amount
                },
                "description": payload.description
            }],
            "application_context": {
                "return_url": "https://mycashbot.online/success.html",
                "cancel_url": "https://mycashbot.online/cancel.html"
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=body)
            
        if response.status_code != 201:
            print(f"❌ PayPal API Error: {response.text}")
            raise HTTPException(
                status_code=response.status_code, 
                detail=f"PayPal error: {response.text}"
            )
            
        order_data = response.json()
        return {"id": order_data.get("id")}
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/api/activate-premium")
async def activate_premium(request_data: ActivatePremiumRequest):
    """Активация премиум-подписки после оплаты"""
    from database import db
    from analytics import capture_event  # 👈 ДОБАВЛЯЕМ ИМПОРТ
    
    try:
        await db.add_premium(request_data.user_id, days=30)
        
        # ========== 🚀 POSTHOG: ОПЛАТА УСПЕШНА ==========
        capture_event(request_data.user_id, "payment_completed", {
            "amount": 2.90,
            "currency": "USD",
            "plan": "premium",
            "gateway": "paypal"
        })
        # ==============================================
        
        print(f"✅ Премиум активирован для пользователя {request_data.user_id}")
        return {"status": "success", "message": "Premium activated"}
    except Exception as e:
        print(f"❌ Ошибка активации премиума: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")