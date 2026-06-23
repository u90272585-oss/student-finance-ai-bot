# payment_endpoints.py
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse
import aiohttp
import os
from typing import Optional

# Временно убираем проблемные импорты
# from database import Database
# from dependencies import get_current_user_id, get_db

app = FastAPI()

# Конфигурация Bereke Bank
BEREKE_BASE_URL = os.getenv("BEREKE_BASE_URL", "https://3dsec.berekebank.kz/payment/rest")
BEREKE_USERNAME = os.getenv("BEREKE_USERNAME")
BEREKE_PASSWORD = os.getenv("BEREKE_PASSWORD")
BEREKE_RETURN_URL = os.getenv("BEREKE_RETURN_URL")
BEREKE_FAIL_URL = os.getenv("BEREKE_FAIL_URL")


# Временная заглушка для зависимостей
async def get_current_user_id():
    return 1  # Временный ID для тестирования

async def get_db():
    from database import Database
    db = Database()
    return db


async def bereke_register_order(order_id: int, amount: int, user_id: int):
    """Регистрирует платёж в Bereke Bank"""
    async with aiohttp.ClientSession() as session:
        data = {
            "userName": BEREKE_USERNAME,
            "password": BEREKE_PASSWORD,
            "orderNumber": str(order_id),
            "amount": str(amount * 100),
            "returnUrl": BEREKE_RETURN_URL,
            "failUrl": BEREKE_FAIL_URL,
            "language": "ru"
        }
        
        async with session.post(f"{BEREKE_BASE_URL}/register.do", data=data) as resp:
            result = await resp.json()
            
            if result.get("errorCode"):
                raise HTTPException(
                    status_code=400,
                    detail=f"Bereke error: {result.get('errorMessage')}"
                )
            
            gateway_order_id = result.get("orderId")
            payment_url = result.get("formUrl")
            
            return gateway_order_id, payment_url


@app.post("/checkout")
async def checkout(amount: int, user_id: int = Depends(get_current_user_id)):
    """Создаёт заказ и возвращает ссылку на оплату"""
    from database import Database
    db = Database()
    
    # Проверка существующего заказа
    existing_order = await db.find_recent_pending_order(user_id, amount)
    
    if existing_order:
        if db.use_postgres:
            order_id = existing_order["id"]
            payment_url = existing_order["payment_url"]
        else:
            order_id = existing_order[0]
            payment_url = existing_order[5]
        
        return {
            "order_id": order_id,
            "payment_url": payment_url,
            "message": "Использован существующий заказ"
        }
    
    # Создаём новый заказ
    order_id = await db.create_order(user_id=user_id, amount=amount, status="created")
    
    # Регистрируем в Bereke
    gateway_order_id, payment_url = await bereke_register_order(order_id, amount, user_id)
    
    # Обновляем заказ
    await db.update_order_gateway_id(order_id, gateway_order_id)
    await db.update_order_payment_url(order_id, payment_url)
    await db.transition_order(order_id, "pending")
    
    return {
        "order_id": order_id,
        "payment_url": payment_url,
        "redirect_url": payment_url
    }


@app.get("/payment/success")
async def payment_success(orderId: str):
    """Возврат с успешной оплаты"""
    from database import Database
    db = Database()
    
    async with aiohttp.ClientSession() as session:
        data = {
            "userName": BEREKE_USERNAME,
            "password": BEREKE_PASSWORD,
            "orderId": orderId
        }
        
        async with session.post(f"{BEREKE_BASE_URL}/getOrderStatus.do", data=data) as resp:
            result = await resp.json()
            
            if result.get("OrderStatus") == 2:
                order = await db.get_order_by_gateway_id(orderId)
                
                if order:
                    order_id = order["id"] if db.use_postgres else order[0]
                    await db.transition_order(order_id, "paid")
                    await db.activate_premium_after_payment(order_id)
                    
                    return {"message": "Payment successful!", "order_id": order_id}
    
    return {"message": "Payment status check failed"}


@app.get("/payment/fail")
async def payment_fail(orderId: str, errorCode: Optional[str] = None):
    """Возврат с неудачной оплаты"""
    from database import Database
    db = Database()
    
    order = await db.get_order_by_gateway_id(orderId)
    
    if order:
        order_id = order["id"] if db.use_postgres else order[0]
        await db.transition_order(order_id, "failed")
        
        return {"message": "Payment failed", "order_id": order_id, "error": errorCode}
    
    return {"message": "Order not found"}


@app.post("/payment/callback")
async def payment_callback(request: Request):
    """Callback от банка"""
    from database import Database
    db = Database()
    
    data = await request.form()
    order_id = data.get("orderId")
    
    print(f"📞 Callback: orderId={order_id}")
    
    async with aiohttp.ClientSession() as session:
        req_data = {
            "userName": BEREKE_USERNAME,
            "password": BEREKE_PASSWORD,
            "orderId": order_id
        }
        
        async with session.post(f"{BEREKE_BASE_URL}/getOrderStatus.do", data=req_data) as resp:
            result = await resp.json()
            
            if result.get("OrderStatus") == 2:
                order = await db.get_order_by_gateway_id(order_id)
                
                if order:
                    db_order_id = order["id"] if db.use_postgres else order[0]
                    
                    try:
                        await db.transition_order(db_order_id, "paid")
                        await db.activate_premium_after_payment(db_order_id)
                        print(f"✅ Заказ {db_order_id} оплачен")
                        return {"status": "success"}
                    except ValueError as e:
                        print(f"⚠️ Ошибка: {e}")
                        return {"status": "error", "message": str(e)}
    
    return {"status": "pending"}