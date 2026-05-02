import os
import sqlite3
from datetime import datetime, timedelta
import random
import asyncpg

# Определяем, где мы запущены
USE_POSTGRES = os.getenv("DATABASE_URL") is not None

class Database:
    def __init__(self):
        self.use_postgres = USE_POSTGRES
        self.conn = None
        self.cursor = None
        self.pool = None
        
        if not self.use_postgres:
            # SQLite (локально)
            self.conn = sqlite3.connect('finance.db')
            self.cursor = self.conn.cursor()
            self._init_sqlite()
            print("✅ SQLite база данных инициализирована")
    
    async def connect(self):
        """Подключение к PostgreSQL (на Railway)"""
        if self.use_postgres:
            database_url = os.getenv("DATABASE_URL")
            self.pool = await asyncpg.create_pool(database_url)
            await self._init_postgres()
            print("✅ PostgreSQL подключён и таблицы созданы")
    
    async def _init_postgres(self):
        """Создание таблиц в PostgreSQL"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    name TEXT,
                    country TEXT DEFAULT 'KZ',
                    language TEXT DEFAULT 'ru',
                    currency TEXT DEFAULT 'KZT',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    type TEXT,
                    amount REAL,
                    category TEXT,
                    note TEXT,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS goals (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    name TEXT,
                    target REAL,
                    current REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS goal_plants (
                    goal_id BIGINT PRIMARY KEY,
                    plant_type TEXT DEFAULT 'lotus',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS premium_users (
                    user_id BIGINT PRIMARY KEY,
                    premium_until TIMESTAMP
                )
            ''')
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS coins (
                    user_id BIGINT PRIMARY KEY,
                    total_coins INTEGER DEFAULT 0,
                    last_game_date TEXT
                )
            ''')
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS shared_goals (
                    id SERIAL PRIMARY KEY,
                    name TEXT,
                    target REAL,
                    current REAL DEFAULT 0,
                    creator_id BIGINT,
                    invite_code TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS shared_goal_members (
                    id SERIAL PRIMARY KEY,
                    goal_id BIGINT,
                    user_id BIGINT,
                    contributed REAL DEFAULT 0,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS videos (
                    id SERIAL PRIMARY KEY,
                    title TEXT,
                    url TEXT,
                    language TEXT,
                    category TEXT,
                    level TEXT,
                    duration TEXT,
                    description TEXT
                )
            ''')
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS financial_tips (
                    id SERIAL PRIMARY KEY,
                    tip TEXT,
                    video_link TEXT,
                    category TEXT
                )
            ''')
            
            # Проверяем, есть ли данные
            count = await conn.fetchval("SELECT COUNT(*) FROM users")
            if count == 0:
                print("⚠️ Таблицы созданы, но пользователей пока нет")
            else:
                print(f"✅ Найдено пользователей: {count}")
    
    def _init_sqlite(self):
        """Инициализация таблиц в SQLite (локально)"""
        # Твой существующий код init_db() из старого database.py
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                country TEXT DEFAULT 'KZ',
                language TEXT DEFAULT 'ru',
                currency TEXT DEFAULT 'KZT',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Добавь остальные таблицы...
        self.conn.commit()
    
    # ========== ОСНОВНЫЕ МЕТОДЫ (РАБОТАЮТ С ОБОИМИ БД) ==========
    
    async def add_user(self, user_id, name, country='KZ', language='ru', currency='KZT'):
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO users (user_id, name, country, language, currency) 
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (user_id) DO NOTHING
                ''', user_id, name, country, language, currency)
        else:
            self.cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, name, country, language, currency) 
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, name, country, language, currency))
            self.conn.commit()
    
    async def get_user(self, user_id):
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                return await conn.fetchrow('SELECT * FROM users WHERE user_id = $1', user_id)
        else:
            self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            return self.cursor.fetchone()
    
    async def is_premium(self, user_id):
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow('SELECT premium_until FROM premium_users WHERE user_id = $1', user_id)
                if row and row['premium_until']:
                    return datetime.now() < row['premium_until']
                return False
        else:
            self.cursor.execute('SELECT premium_until FROM premium_users WHERE user_id = ?', (user_id,))
            row = self.cursor.fetchone()
            if row and row[0]:
                return datetime.now() < datetime.fromisoformat(row[0])
            return False
    
    async def add_premium(self, user_id, days=30):
        until = (datetime.now() + timedelta(days=days)).isoformat()
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO premium_users (user_id, premium_until) VALUES ($1, $2)
                    ON CONFLICT (user_id) DO UPDATE SET premium_until = $2
                ''', user_id, until)
        else:
            self.cursor.execute('''
                INSERT OR REPLACE INTO premium_users (user_id, premium_until)
                VALUES (?, ?)
            ''', (user_id, until))
            self.conn.commit()
    
    # Добавь остальные методы по аналогии...
    
    async def close(self):
        if self.use_postgres and self.pool:
            await self.pool.close()
        elif self.conn:
            self.conn.close()