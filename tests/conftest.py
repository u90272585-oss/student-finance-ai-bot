import pytest
import sqlite3
from database import Database
import os

# Отключаем PostgreSQL для тестов (используем SQLite в памяти)
os.environ["USE_POSTGRES"] = "False"
os.environ.pop("DATABASE_URL", None)  # удаляем, если есть

@pytest.fixture
async def db():
    """Фикстура — создаёт чистую БД для каждого теста"""
    
    db_instance = Database()
    
    # Принудительно используем SQLite в памяти
    db_instance.use_postgres = False
    db_instance.conn = sqlite3.connect(':memory:')
    db_instance.cursor = db_instance.conn.cursor()
    
    # Создаём таблицы
    db_instance._init_sqlite()
    
    yield db_instance
    
    # Закрываем после теста
    db_instance.conn.close()