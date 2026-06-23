import asyncio
import logging
import csv
import io
import random
import string
from datetime import datetime
import os
from dotenv import load_dotenv
from security_logger import log_admin_access, log_security_event

# ─── ИМПОРТ ДЛЯ FASTAPI И PAYPAL ────────────────────────────────────
from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel
import httpx
from aiohttp import web  # Для Render ping

# ─── ИМПОРТ ДЛЯ БОТА ────────────────────────────────────────────────
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from ai_assistant import get_ai_response
from database import Database
from translations import get_text, COUNTRIES, LANGUAGES, CURRENCIES, VIDEO_CATEGORIES
from keyboards import (
    get_country_keyboard, get_language_keyboard, get_currency_keyboard,
    get_all_currencies_keyboard, get_main_keyboard, get_cancel_keyboard,
    get_categories_keyboard, get_settings_keyboard, get_delete_confirmation_keyboard,
    get_goal_actions_keyboard, get_video_categories_keyboard,
    get_shared_goals_keyboard, get_shared_goal_actions_keyboard,
    get_game_webapp_keyboard
)
from plant_goals import get_plant_text, get_plant_choice_keyboard, PLANT_TYPES

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
db = Database()

# ========== 1. СОЗДАЕМ FASTAPI ПРИЛОЖЕНИЕ (ОДИН РАЗ!) ==========
app = FastAPI()

# ========== 2. ПОДКЛЮЧАЕМ РОУТЕР ПЛАТЕЖЕЙ ==========
from payment import router as payment_router
app.include_router(payment_router)

# ========== 3. RATE LIMITING ==========
from collections import defaultdict
import time
user_last_message = defaultdict(float)
RATE_LIMIT_SECONDS = 1.0

@dp.message.outer_middleware()
async def rate_limit_middleware(handler, message, data):
    user_id = message.from_user.id
    now = time.time()
    last = user_last_message[user_id]
    if now - last < RATE_LIMIT_SECONDS:
        log_security_event("RATE_LIMIT_HIT", user_id, "telegram", {"limit": RATE_LIMIT_SECONDS})
        await message.answer("⏱ Не спамьте, пожалуйста!")
        return
    user_last_message[user_id] = now
    return await handler(message, data)

# ========== 4. ВЕБ-ХЕНДЛЕР ДЛЯ RENDER ==========
async def handle_render_ping(request):
    return web.Response(text="🚀 FINANCE BOT IS ALIVE AND RUNNING!")

# ========== 5. СОСТОЯНИЯ ДЛЯ БОТА ==========
class SetupState(StatesGroup):
    country = State()
    language = State()
    currency = State()

class TransactionState(StatesGroup):
    amount = State()
    category = State()
    note = State()

class GoalState(StatesGroup):
    name = State()
    amount = State()
    plant_choice = State()
    select_for_delete = State()
    confirm_delete = State()
    select_for_add_money = State()
    enter_add_amount = State()

class SettingsState(StatesGroup):
    action = State()
    language = State()
    currency = State()
    delete_data = State()
    confirm_delete_all = State()

class VideoState(StatesGroup):
    category = State()

class SharedGoalState(StatesGroup):
    create_name = State()
    create_target = State()
    join_goal = State()
    add_money = State()
    select_for_add = State()
    enter_amount = State()

# ========== 6. ВСЕ ХЕНДЛЕРЫ БОТА ==========
# [СЮДА ВСТАВЛЯЙ ВСЕ СВОИ @dp.message() ХЕНДЛЕРЫ. 
# Я ИХ НЕ ПРИВОЖУ, ПОТОМУ ЧТО ОНИ У ТЕБЯ УЖЕ ЕСТЬ.
# ПРОСТО СКОПИРУЙ ИХ СЮДА ИЗ СТАРОГО ФАЙЛА.
# НАПРИМЕР:
# @dp.message(Command("start"))
# async def cmd_start(...): ...
# ... и так далее
# НО НЕ ЗАБУДЬ УБРАТЬ ИЗ ЭТОЙ ЧАСТИ app = FastAPI() и payment_router, 
# ПОТОМУ ЧТО ОНИ УЖЕ ВВЕРХУ!
# ]

# ========== 7. ЗАПУСК ==========
import uvicorn

@app.on_event("startup")
async def on_startup():
    await asyncio.sleep(1)  
    print("=" * 50)
    print("🚀 FINANCE BOT STARTED!")
    print("=" * 50)

    await bot.set_my_commands([
        types.BotCommand(command="start", description="🚀 Запустить бота"),
        types.BotCommand(command="new_goal", description="🎯 Создать новую цель"),
        types.BotCommand(command="ask", description="🤖 Спросить у ИИ ассистента"),
        types.BotCommand(command="premium", description="💎 Премиум доступ"),
        types.BotCommand(command="tip", description="💡 Получить финансовый совет"),
        types.BotCommand(command="video", description="📺 Случайное видео"),
        types.BotCommand(command="export_csv", description="📁 Экспорт данных в CSV"),
        types.BotCommand(command="discount", description="🪙 Обменять монеты на скидку"),
    ])

    print("✅ Languages: Русский, Қазақша, English, Українська")
    print("✅ Currencies: KZT, RUB, UAH, USD, EUR, BYN, UZS, KGS")
    print("✅ Countries: USA, Kazakhstan, Russia, Ukraine, Belarus, Uzbekistan, Kyrgyzstan")
    print("✅ Features: Shared Goals, Videos, Tips, Export, Goal Flowers 🌸, AI Assistant 🤖, Premium 💎")
    print("=" * 50)

    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()))
    print("🤖 Telegram Bot polling успешно запущен в фоне!")
    print("=" * 50)

@app.on_event("shutdown")
async def on_shutdown():
    print("=" * 50)
    print("🛑 Останавливаем сервер и закрываем сессию бота...")
    await bot.session.close()
    print("👋 Все сессии успешно закрыты.")
    print("=" * 50)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🌍 Запускаем FastAPI сервер на порту {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)