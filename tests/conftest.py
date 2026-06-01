import pytest
import sqlite3
from database import Database
import os

# Отключаем PostgreSQL для тестов
os.environ["USE_POSTGRES"] = "False"
if "DATABASE_URL" in os.environ:
    del os.environ["DATABASE_URL"]

@pytest.fixture
async def db():
    db_instance = Database()
    db_instance.use_postgres = False
    db_instance.conn = sqlite3.connect(':memory:')
    db_instance.cursor = db_instance.conn.cursor()
    db_instance._init_sqlite()
    yield db_instance
    db_instance.conn.close()