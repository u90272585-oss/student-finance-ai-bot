# tests/conftest.py
import pytest
import sqlite3
import os
from unittest.mock import AsyncMock

# Отключаем PostgreSQL для тестов
os.environ["USE_POSTGRES"] = "False"
if "DATABASE_URL" in os.environ:
    del os.environ["DATABASE_URL"]

from database import Database


@pytest.fixture
def db():
    """Тестовая база данных SQLite in-memory"""
    db_instance = Database()
    db_instance.use_postgres = False
    db_instance.conn = sqlite3.connect(':memory:')
    db_instance.cursor = db_instance.conn.cursor()
    
    # Вызываем твой реальный метод инициализации
    db_instance._init_sqlite()
    
    yield db_instance
    db_instance.conn.close()


@pytest.fixture
def mock_bot():
    """Мок Telegram бота"""
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    bot.send_photo = AsyncMock()
    return bot


@pytest.fixture
def test_user(db):
    """Создаёт тестового пользователя (user_id = 123456789)"""
    db.cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, name, language, currency) VALUES (?, ?, ?, ?)",
        (123456789, "Test User", "ru", "KZT")
    )
    db.conn.commit()
    
    return {
        "user_id": 123456789,
        "name": "Test User",
        "language": "ru",
        "currency": "KZT"
    }


@pytest.fixture
def test_admin(db):
    """Создаёт тестового админа (обычный пользователь, роль пока не используется)"""
    db.cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, name, language, currency) VALUES (?, ?, ?, ?)",
        (999999999, "Admin User", "ru", "KZT")
    )
    db.conn.commit()
    
    return {
        "user_id": 999999999,
        "name": "Admin User",
        "language": "ru",
        "currency": "KZT"
    }


@pytest.fixture
def test_premium_user(db):
    """Создаёт премиум пользователя"""
    user_id = 777777777
    db.cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, name) VALUES (?, ?)",
        (user_id, "Premium User")
    )
    # Добавляем премиум до конца 2030 года
    premium_until = "2030-12-31 23:59:59"
    db.cursor.execute(
        "INSERT OR REPLACE INTO premium_users (user_id, premium_until) VALUES (?, ?)",
        (user_id, premium_until)
    )
    db.conn.commit()
    
    return {
        "user_id": user_id,
        "name": "Premium User",
        "premium_until": premium_until
    }