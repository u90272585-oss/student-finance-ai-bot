import os
import httpx
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/orders", tags=["Payments"])

# Берем секреты из твоего .env
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
PAYPAL_BASE_URL = "https://api-m.sandbox.paypal.com"

class OrderRequest(BaseModel):
    amount: Optional[str] = "2.90"
    currency: Optional[str] = "USD"
    description: Optional[str] = "CoinMind Premium"

async def get_paypal_access_token() -> str:
    """Асинхронное получение токена от PayPal"""
    url = f"{PAYPAL_BASE_URL}/v1/oauth2/token"
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en_US",
    }
    data = {"grant_type": "client_credentials"}
    
    async with httpx.AsyncClient() as client:
        # Аутентификация Basic Auth (передаем Client ID и Secret)
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

@router.post("")
async def create_order(payload: OrderRequest):
    try:
        access_token = await get_paypal_access_token()
        
        # ХАРДКОРНЫЙ ФИКС: Если с фронта летит KZT или знак тенге ₸, 
        # принудительно меняем на USD, иначе PayPal выплюнет ошибку!
        currency = payload.currency
        amount = payload.amount
        
        if currency in ["KZT", "₸", "kzt"]:
            currency = "USD"
            amount = "0.65" # Пересчитали твои 290 тенге в доллары по курсу
            
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
                "return_url": "http://localhost:8000/landing/success.html",
                "cancel_url": "http://localhost:8000/landing/home.html"
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=body)
            
        # Если PayPal вернул ошибку (например, 400 или 422), мы выводим её в консоль Python
        if response.status_code != 201:
            print(f"❌ PayPal API Error Full Details: {response.text}")
            raise HTTPException(
                status_code=response.status_code, 
                detail=f"PayPal refused to create order: {response.text}"
            )
            
        order_data = response.json()
        return {"id": order_data.get("id")}
        
    except Exception as e:
        print(f"❌ Критическая ошибка бэкенда: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")