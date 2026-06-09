import os
import sqlite3
from datetime import datetime, timedelta
import random
import asyncpg
from cache import get_cached, set_cached, delete_cached, clear_user_cache, row_to_dict
from security_logger import log_security_event

# Определяем, где мы запущены
USE_POSTGRES = os.getenv("DATABASE_URL") is not None
VALID_TRANSITIONS = {
    "created": ["pending"],

    "pending": [
        "paid",
        "failed",
        "cancelled"
    ],

    "paid": [
        "refunded"
    ],

    "failed": [],

    "cancelled": [],

    "refunded": []
}
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
    CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        amount INTEGER NOT NULL,

        status TEXT NOT NULL DEFAULT 'created',

        gateway_order_id TEXT,
        payment_url TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

            # Индексы для ускорения запросов
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_goals_user_id ON goals(user_id)')

            # Проверяем, есть ли данные
            count = await conn.fetchval("SELECT COUNT(*) FROM users")
            if count == 0:
                print("⚠️ Таблицы созданы, но пользователей пока нет")
            else:
                print(f"✅ Найдено пользователей: {count}")

    def _init_sqlite(self):
        """Инициализация таблиц в SQLite (локально)"""
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
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT,
                amount REAL,
                category TEXT,
                note TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                target REAL,
                current REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS goal_plants (
                goal_id INTEGER PRIMARY KEY,
                plant_type TEXT DEFAULT 'lotus',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS premium_users (
                user_id INTEGER PRIMARY KEY,
                premium_until TIMESTAMP
            )
        ''')
        self.cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER NOT NULL,
        amount INTEGER NOT NULL,

        status TEXT NOT NULL DEFAULT 'created',

        gateway_order_id TEXT,
        payment_url TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS coins (
                user_id INTEGER PRIMARY KEY,
                total_coins INTEGER DEFAULT 0,
                last_game_date TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS shared_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                target REAL,
                current REAL DEFAULT 0,
                creator_id INTEGER,
                invite_code TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS shared_goal_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER,
                user_id INTEGER,
                contributed REAL DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                url TEXT,
                language TEXT,
                category TEXT,
                level TEXT,
                duration TEXT,
                description TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS financial_tips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tip TEXT,
                video_link TEXT,
                category TEXT
            )
        ''')

        # Индексы для ускорения запросов
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_goals_user_id ON goals(user_id)')

        self.conn.commit()
        self._init_financial_tips_sqlite()
        self._init_videos_sqlite()

    def _init_financial_tips_sqlite(self):
        """Инициализация финансовых советов в SQLite"""
        self.cursor.execute("SELECT COUNT(*) FROM financial_tips")
        if self.cursor.fetchone()[0] == 0:
            tips = [
                ("Правило 50/30/20: 50% на необходимое, 30% на желания, 20% на сбережения", "", "budgeting"),
                ("Создайте резервный фонд на 3-6 месяцев расходов", "", "saving"),
                ("Автоматизируйте свои сбережения", "", "saving"),
                ("Отслеживайте каждую трату в течение месяца", "", "tracking"),
                ("Используйте кэшбэк и бонусные программы", "", "saving"),
                ("Инвестируйте рано, даже небольшие суммы", "", "investing"),
                ("Погашайте долги с самой высокой процентной ставкой", "", "debt"),
                ("Готовьте дома, чтобы экономить на еде", "", "saving"),
                ("Сравнивайте цены перед покупкой", "", "saving"),
                ("Установите финансовые цели на год", "", "goals"),
            ]
            for tip, video_link, category in tips:
                self.cursor.execute('INSERT INTO financial_tips (tip, video_link, category) VALUES (?, ?, ?)',
                                  (tip, video_link, category))
            self.conn.commit()

    def _init_videos_sqlite(self):
        """Инициализация видео в SQLite"""
        self.cursor.execute("SELECT COUNT(*) FROM videos")
        if self.cursor.fetchone()[0] == 0:
            russian_videos = [
                ("Почему ты бедный?", "https://youtu.be/ORhFkbMDw9Y", "ru", "basics", "beginner", "15:00", "Основы финансовой грамотности"),
                ("Финансовая грамотность для чайников", "https://youtu.be/073P_bPnS3w", "ru", "saving", "beginner", "12:00", "Простые способы накопления"),
                ("Идеальный маршрут инвестора - 7 шагов", "https://youtu.be/9p-rz-k5BPM", "ru", "investing", "beginner", "20:00", "Введение в инвестиции"),
                ("Как ИЗБАВИТЬСЯ ОТ ДОЛГОВ? — АМОБЛОГ", "https://youtu.be/IzFy83zbN3o", "ru", "debt", "intermediate", "18:00", "Управление кредитами"),
                ("Как вести учет личных финансов", "https://youtu.be/Lc-bcvLT-x0", "ru", "budgeting", "beginner", "14:00", "Как составить бюджет"),
                ("Пассивный доход", "https://youtu.be/WulzE9M7VJw", "ru", "investing", "intermediate", "22:00", "Создание пассивного дохода"),
                ("Как выйти на финансовую свободу?", "https://youtu.be/Fx917LJiVr0", "ru", "goals", "advanced", "25:00", "Путь к финансовой независимости"),
                ("50 вещей которые делают тебя бедней", "https://youtu.be/Ovovu1P7u78", "ru", "basics", "intermediate", "16:00", "бедность"),
                ("Криптовалюта. Полное объяснение для чайников", "https://youtu.be/QPOdFedaujY", "ru", "investing", "intermediate", "19:00", "Что такое криптовалюта"),
                ("Психология денег: Как мыслить богато", "https://youtu.be/gqQLews_xuQ", "ru", "basics", "beginner", "21:00", "Финансовое мышление"),
            ]
            for video in russian_videos:
                self.cursor.execute('''
                    INSERT INTO videos (title, url, language, category, level, duration, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', video)
            self.conn.commit()

    async def add_user(self, user_id, name, country='KZ', language='ru', currency='KZT'):
        from security_logger import log_security_event

        # Проверка на дубликат
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                existing = await conn.fetchrow('SELECT user_id FROM users WHERE user_id = $1', user_id)
                if existing:
                    log_security_event(
                        "DUPLICATE_USER_ATTEMPT",
                        user_id,
                        "telegram",
                        {"name": name, "action": "add_user_ignored"}
                    )
                    return

                await conn.execute('''
                    INSERT INTO users (user_id, name, country, language, currency)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (user_id) DO NOTHING
                ''', user_id, name, country, language, currency)
        else:
            # SQLite
            self.cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
            existing = self.cursor.fetchone()
            if existing:
                log_security_event(
                    "DUPLICATE_USER_ATTEMPT",
                    user_id,
                    "telegram",
                    {"name": name, "action": "add_user_ignored"}
                )
                return

            self.cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, name, country, language, currency)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, name, country, language, currency))
            self.conn.commit()

        # Логируем успешное создание
        log_security_event("USER_CREATED", user_id, "telegram", {"name": name})

    async def get_user(self, user_id):
        # Проверяем кэш
        cached_user = get_cached(f"user:{user_id}")
        if cached_user:
            return cached_user

        if self.use_postgres:
            async with self.pool.acquire() as conn:
                user = await conn.fetchrow('SELECT * FROM users WHERE user_id = $1', user_id)
        else:
            self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            user = self.cursor.fetchone()

        # Сохраняем в кэш на 5 минут
        if user:
            set_cached(f"user:{user_id}", row_to_dict(user), ttl=300)

        return user

    async def update_language(self, user_id, language):
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                await conn.execute('UPDATE users SET language = $1 WHERE user_id = $2', language, user_id)
        else:
            self.cursor.execute('UPDATE users SET language = ? WHERE user_id = ?', (language, user_id))
            self.conn.commit()

        # Очищаем кэш
        clear_user_cache(user_id)

    async def update_currency(self, user_id, currency):
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                await conn.execute('UPDATE users SET currency = $1 WHERE user_id = $2', currency, user_id)
        else:
            self.cursor.execute('UPDATE users SET currency = ? WHERE user_id = ?', (currency, user_id))
            self.conn.commit()

        # Очищаем кэш
        clear_user_cache(user_id)

    async def add_transaction(self, user_id, trans_type, amount, category, note=""):
        # Валидация
        if amount <= 0:
            raise ValueError("Amount must be positive")

        if self.use_postgres:
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO transactions (user_id, type, amount, category, note)
                    VALUES ($1, $2, $3, $4, $5)
                ''', user_id, trans_type, amount, category, note)
        else:
            self.cursor.execute('''
                INSERT INTO transactions (user_id, type, amount, category, note)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, trans_type, amount, category, note))
            self.conn.commit()

        # Очищаем кэш транзакций
        delete_cached(f"transactions:{user_id}")

    async def get_all_transactions(self, user_id):
        # Проверяем кэш
        cached = get_cached(f"transactions:{user_id}")
        if cached:
            return cached

        if self.use_postgres:
            async with self.pool.acquire() as conn:
                transactions = await conn.fetch('''
                    SELECT id, type, amount, category, note, date FROM transactions
                    WHERE user_id = $1 ORDER BY date DESC
                ''', user_id)
        else:
            self.cursor.execute('''
                SELECT id, type, amount, category, note, date FROM transactions
                WHERE user_id = ? ORDER BY date DESC
            ''', (user_id,))
            transactions = self.cursor.fetchall()

        # Сохраняем в кэш на 1 минуту
        if transactions:
            set_cached(f"transactions:{user_id}", [row_to_dict(t) for t in transactions], ttl=60)

        return transactions

    async def get_stats(self, user_id, days=30):
        date_limit = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        if self.use_postgres:
            async with self.pool.acquire() as conn:
                income = await conn.fetchval('''
                    SELECT COALESCE(SUM(amount), 0) FROM transactions
                    WHERE user_id = $1 AND type = 'income' AND date >= $2
                ''', user_id, date_limit)

                expense = await conn.fetchval('''
                    SELECT COALESCE(SUM(amount), 0) FROM transactions
                    WHERE user_id = $1 AND type = 'expense' AND date >= $2
                ''', user_id, date_limit)

                top_cats = await conn.fetch('''
                    SELECT category, SUM(amount) FROM transactions
                    WHERE user_id = $1 AND type = 'expense' AND date >= $2
                    GROUP BY category ORDER BY SUM(amount) DESC LIMIT 5
                ''', user_id, date_limit)

                return income, expense, income - expense, top_cats
        else:
            self.cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) FROM transactions
                WHERE user_id = ? AND type = 'income' AND date >= ?
            ''', (user_id, date_limit))
            income = self.cursor.fetchone()[0]

            self.cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) FROM transactions
                WHERE user_id = ? AND type = 'expense' AND date >= ?
            ''', (user_id, date_limit))
            expense = self.cursor.fetchone()[0]

            self.cursor.execute('''
                SELECT category, SUM(amount) FROM transactions
                WHERE user_id = ? AND type = 'expense' AND date >= ?
                GROUP BY category ORDER BY SUM(amount) DESC LIMIT 5
            ''', (user_id, date_limit))
            top_cats = self.cursor.fetchall()

            return income, expense, income - expense, top_cats

    async def add_goal(self, user_id, name, target):
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow('''
                    INSERT INTO goals (user_id, name, target)
                    VALUES ($1, $2, $3)
                    RETURNING id
                ''', user_id, name, target)
                goal_id = row['id']
        else:
            self.cursor.execute(
                'INSERT INTO goals (user_id, name, target) VALUES (?, ?, ?)',
                (user_id, name, target)
            )
            self.conn.commit()
            goal_id = self.cursor.lastrowid

        # Очищаем кэш целей
        delete_cached(f"goals:{user_id}")
        return goal_id

    async def get_goals(self, user_id):
        # Проверяем кэш
        cached = get_cached(f"goals:{user_id}")
        if cached:
            return cached

        if self.use_postgres:
            async with self.pool.acquire() as conn:
                goals = await conn.fetch('''
                    SELECT id, name, target, current FROM goals
                    WHERE user_id = $1 ORDER BY created_at DESC
                ''', user_id)
        else:
            self.cursor.execute(
                'SELECT id, name, target, current FROM goals WHERE user_id = ? ORDER BY created_at DESC',
                (user_id,)
            )
            goals = self.cursor.fetchall()

        # Сохраняем в кэш
        if goals:
            set_cached(f"goals:{user_id}", [row_to_dict(g) for g in goals], ttl=300)

        return goals

    async def update_goal_progress(self, user_id, amount):
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                goals = await conn.fetch('SELECT id, target, current FROM goals WHERE user_id = $1', user_id)
                completed_goals = []
                for goal_id, target, current in goals:
                    if current < target:
                        new_current = min(current + amount, target)
                        await conn.execute('UPDATE goals SET current = $1 WHERE id = $2', new_current, goal_id)
                        if new_current >= target:
                            completed_goals.append(goal_id)

                # Очищаем кэш целей
                delete_cached(f"goals:{user_id}")

                return completed_goals if completed_goals else None
        else:
            self.cursor.execute('SELECT id, target, current FROM goals WHERE user_id = ?', (user_id,))
            goals = self.cursor.fetchall()
            completed_goals = []
            for goal_id, target, current in goals:
                if current < target:
                    new_current = min(current + amount, target)
                    self.cursor.execute('UPDATE goals SET current = ? WHERE id = ?', (new_current, goal_id))
                    if new_current >= target:
                        completed_goals.append(goal_id)
            self.conn.commit()

            # Очищаем кэш целей
            delete_cached(f"goals:{user_id}")

            return completed_goals if completed_goals else None

    async def delete_goal(self, goal_id):
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                await conn.execute('DELETE FROM goals WHERE id = $1', goal_id)
        else:
            self.cursor.execute('DELETE FROM goals WHERE id = ?', (goal_id,))
            self.conn.commit()

    async def set_goal_plant(self, goal_id, plant_type):
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO goal_plants (goal_id, plant_type) VALUES ($1, $2)
                    ON CONFLICT (goal_id) DO UPDATE SET plant_type = $2
                ''', goal_id, plant_type)
        else:
            self.cursor.execute('''
                INSERT OR REPLACE INTO goal_plants (goal_id, plant_type)
                VALUES (?, ?)
            ''', (goal_id, plant_type))
            self.conn.commit()

    async def get_goal_plant(self, goal_id):
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow('SELECT plant_type FROM goal_plants WHERE goal_id = $1', goal_id)
                return row['plant_type'] if row else 'lotus'
        else:
            self.cursor.execute('SELECT plant_type FROM goal_plants WHERE goal_id = ?', (goal_id,))
            row = self.cursor.fetchone()
            return row[0] if row else 'lotus'

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
    async def create_order(
    self,
    user_id,
    amount,
    status="created",
    gateway_order_id=None,
    payment_url=None
):
    if self.use_postgres:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                INSERT INTO orders (
                    user_id,
                    amount,
                    status,
                    gateway_order_id,
                    payment_url
                )
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            ''',
            user_id,
            amount,
            status,
            gateway_order_id,
            payment_url)

            return row["id"]

    else:
        self.cursor.execute('''
            INSERT INTO orders (
                user_id,
                amount,
                status,
                gateway_order_id,
                payment_url
            )
            VALUES (?, ?, ?, ?, ?)
        ''',
        (
            user_id,
            amount,
            status,
            gateway_order_id,
            payment_url
        ))

        self.conn.commit()

        return self.cursor.lastrowid

async def get_order(self, order_id):
    if self.use_postgres:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                '''
                SELECT *
                FROM orders
                WHERE id = $1
                ''',
                order_id
            )

    else:
        self.cursor.execute(
            '''
            SELECT *
            FROM orders
            WHERE id = ?
            ''',
            (order_id,)
        )

        return self.cursor.fetchone()
    
    async def update_order_status(
    self,
    order_id,
    new_status
):
    if self.use_postgres:
        async with self.pool.acquire() as conn:
            await conn.execute(
                '''
                UPDATE orders
                SET status = $1
                WHERE id = $2
                ''',
                new_status,
                order_id
            )

    else:
        self.cursor.execute(
            '''
            UPDATE orders
            SET status = ?
            WHERE id = ?
            ''',
            (
                new_status,
                order_id
            )
        )

        self.conn.commit()
async def find_recent_pending_order(
    self,
    user_id,
    amount
):
    if self.use_postgres:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                '''
                SELECT *
                FROM orders
                WHERE user_id = $1
                AND amount = $2
                AND status = 'pending'
                AND created_at >= NOW() - INTERVAL '5 minutes'
                ORDER BY created_at DESC
                LIMIT 1
                ''',
                user_id,
                amount
            )

    else:
        self.cursor.execute(
            '''
            SELECT *
            FROM orders
            WHERE user_id = ?
            AND amount = ?
            AND status = 'pending'
            AND datetime(created_at) >= datetime('now', '-5 minutes')
            ORDER BY created_at DESC
            LIMIT 1
            ''',
            (
                user_id,
                amount
            )
        )

        return self.cursor.fetchone()
async def activate_premium_after_payment(
    self,
    order_id
):
    order = await self.get_order(order_id)

    if not order:
        raise ValueError(
            f"Order {order_id} not found"
        )

    status = (
        order["status"]
        if self.use_postgres
        else order[3]
    )

    if status != "paid":
        raise ValueError(
            f"Order {order_id} is not paid"
        )

    user_id = (
        order["user_id"]
        if self.use_postgres
        else order[1]
    )

    await self.add_premium(
        user_id,
        days=30
    )

    return True

    
async def transition_order(
    self,
    order_id,
    new_status
):
    order = await self.get_order(order_id)

    if not order:
        raise ValueError(
            f"Order {order_id} not found"
        )

    current_status = order["status"] if self.use_postgres else order[3]

    allowed = VALID_TRANSITIONS.get(
        current_status,
        []
    )

    if new_status not in allowed:
        raise ValueError(
            f"Transition {current_status} -> {new_status} not allowed"
        )

    await self.update_order_status(
        order_id,
        new_status
    )

    return True
    async def remove_premium(self, user_id):
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                await conn.execute('DELETE FROM premium_users WHERE user_id = $1', user_id)
        else:
            self.cursor.execute('DELETE FROM premium_users WHERE user_id = ?', (user_id,))
            self.conn.commit()

    async def get_premium_expiry(self, user_id):
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow('SELECT premium_until FROM premium_users WHERE user_id = $1', user_id)
                return row['premium_until'] if row else None
        else:
            self.cursor.execute('SELECT premium_until FROM premium_users WHERE user_id = ?', (user_id,))
            row = self.cursor.fetchone()
            return datetime.fromisoformat(row[0]) if row and row[0] else None

    async def get_coins(self, user_id):
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow('SELECT total_coins, last_game_date FROM coins WHERE user_id = $1', user_id)
                return (row['total_coins'], row['last_game_date']) if row else (0, None)
        else:
            self.cursor.execute("SELECT total_coins, last_game_date FROM coins WHERE user_id = ?", (user_id,))
            row = self.cursor.fetchone()
            return row if row else (0, None)

    async def add_coins(self, user_id, amount):
        today = datetime.now().strftime("%Y-%m-%d")
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO coins (user_id, total_coins, last_game_date) VALUES ($1, $2, $3)
                    ON CONFLICT (user_id) DO UPDATE SET
                        total_coins = coins.total_coins + $2,
                        last_game_date = $3
                ''', user_id, amount, today)
        else:
            self.cursor.execute('''
                INSERT INTO coins (user_id, total_coins, last_game_date)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                total_coins = total_coins + ?,
                last_game_date = ?
            ''', (user_id, amount, today, amount, today))
            self.conn.commit()

    async def can_play_today(self, user_id):
        coins, last_game = await self.get_coins(user_id)
        today = datetime.now().strftime("%Y-%m-%d")
        return last_game != today

    async def use_coins_for_discount(self, user_id, coins_needed):
        coins, _ = await self.get_coins(user_id)
        if coins >= coins_needed:
            if self.use_postgres:
                async with self.pool.acquire() as conn:
                    await conn.execute('UPDATE coins SET total_coins = total_coins - $1 WHERE user_id = $2', coins_needed, user_id)
            else:
                self.cursor.execute("UPDATE coins SET total_coins = total_coins - ? WHERE user_id = ?", (coins_needed, user_id))
                self.conn.commit()
            return True
        return False

    # ========== МЕТОДЫ ДЛЯ ОБЩИХ ЦЕЛЕЙ ==========

    async def create_shared_goal(self, creator_id, name, target, invite_code):
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow('''
                    INSERT INTO shared_goals (name, target, current, creator_id, invite_code, created_at)
                    VALUES ($1, $2, 0, $3, $4, $5)
                    RETURNING id
                ''', name, target, creator_id, invite_code, datetime.now())
                goal_id = row['id']
                await conn.execute('''
                    INSERT INTO shared_goal_members (goal_id, user_id, contributed)
                    VALUES ($1, $2, 0)
                ''', goal_id, creator_id)
                return goal_id
        else:
            self.cursor.execute('''
                INSERT INTO shared_goals (name, target, current, creator_id, invite_code, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, target, 0, creator_id, invite_code, datetime.now()))
            goal_id = self.cursor.lastrowid
            self.cursor.execute('''
                INSERT INTO shared_goal_members (goal_id, user_id, contributed)
                VALUES (?, ?, ?)
            ''', (goal_id, creator_id, 0))
            self.conn.commit()
            return goal_id

    async def join_shared_goal(self, user_id, invite_code):
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                goal = await conn.fetchrow('SELECT id, name, target, current, creator_id FROM shared_goals WHERE invite_code = $1', invite_code)
                if not goal:
                    return None
                goal_id = goal['id']
                existing = await conn.fetchrow('SELECT * FROM shared_goal_members WHERE goal_id = $1 AND user_id = $2', goal_id, user_id)
                if existing:
                    return 'already_member'
                await conn.execute('''
                    INSERT INTO shared_goal_members (goal_id, user_id, contributed)
                    VALUES ($1, $2, 0)
                ''', goal_id, user_id)
                return {'goal_id': goal_id, 'name': goal['name'], 'target': goal['target'], 'current': goal['current'], 'creator_id': goal['creator_id']}
        else:
            self.cursor.execute('SELECT id, name, target, current, creator_id FROM shared_goals WHERE invite_code = ?', (invite_code,))
            goal = self.cursor.fetchone()
            if not goal:
                return None
            goal_id = goal[0]
            self.cursor.execute('SELECT * FROM shared_goal_members WHERE goal_id = ? AND user_id = ?', (goal_id, user_id))
            if self.cursor.fetchone():
                return 'already_member'
            self.cursor.execute('''
                INSERT INTO shared_goal_members (goal_id, user_id, contributed)
                VALUES (?, ?, ?)
            ''', (goal_id, user_id, 0))
            self.conn.commit()
            return {'goal_id': goal_id, 'name': goal[1], 'target': goal[2], 'current': goal[3], 'creator_id': goal[4]}

    async def add_to_shared_goal(self, user_id, goal_id, amount):
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                await conn.execute('UPDATE shared_goals SET current = current + $1 WHERE id = $2', amount, goal_id)
                await conn.execute('''
                    UPDATE shared_goal_members SET contributed = contributed + $1
                    WHERE goal_id = $2 AND user_id = $3
                ''', amount, goal_id, user_id)
                row = await conn.fetchrow('SELECT target, current FROM shared_goals WHERE id = $1', goal_id)
                return row['current'] >= row['target']
        else:
            self.cursor.execute('UPDATE shared_goals SET current = current + ? WHERE id = ?', (amount, goal_id))
            self.cursor.execute('''
                UPDATE shared_goal_members SET contributed = contributed + ?
                WHERE goal_id = ? AND user_id = ?
            ''', (amount, goal_id, user_id))
            self.conn.commit()
            self.cursor.execute('SELECT target, current FROM shared_goals WHERE id = ?', (goal_id,))
            target, current = self.cursor.fetchone()
            return current >= target

    async def get_user_shared_goals(self, user_id):
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                return await conn.fetch('''
                    SELECT sg.id, sg.name, sg.target, sg.current, sg.invite_code, sg.creator_id,
                           (SELECT SUM(contributed) FROM shared_goal_members WHERE goal_id = sg.id) as total_contributed
                    FROM shared_goals sg
                    JOIN shared_goal_members sgm ON sg.id = sgm.goal_id
                    WHERE sgm.user_id = $1
                    ORDER BY sg.created_at DESC
                ''', user_id)
        else:
            self.cursor.execute('''
                SELECT sg.id, sg.name, sg.target, sg.current, sg.invite_code, sg.creator_id,
                       (SELECT SUM(contributed) FROM shared_goal_members WHERE goal_id = sg.id) as total_contributed
                FROM shared_goals sg
                JOIN shared_goal_members sgm ON sg.id = sgm.goal_id
                WHERE sgm.user_id = ?
                ORDER BY sg.created_at DESC
            ''', (user_id,))
            return self.cursor.fetchall()

    async def get_shared_goal_details(self, goal_id):
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                goal = await conn.fetchrow('''
                    SELECT sg.id, sg.name, sg.target, sg.current, sg.invite_code, sg.creator_id,
                           u.name as creator_name
                    FROM shared_goals sg
                    JOIN users u ON sg.creator_id = u.user_id
                    WHERE sg.id = $1
                ''', goal_id)
                if not goal:
                    return None
                members = await conn.fetch('''
                    SELECT u.user_id, u.name, sgm.contributed
                    FROM shared_goal_members sgm
                    JOIN users u ON sgm.user_id = u.user_id
                    WHERE sgm.goal_id = $1
                    ORDER BY sgm.contributed DESC
                ''', goal_id)
                return {'goal': goal, 'members': members}
        else:
            self.cursor.execute('''
                SELECT sg.id, sg.name, sg.target, sg.current, sg.invite_code, sg.creator_id,
                       u.name as creator_name
                FROM shared_goals sg
                JOIN users u ON sg.creator_id = u.user_id
                WHERE sg.id = ?
            ''', (goal_id,))
            goal = self.cursor.fetchone()
            if not goal:
                return None
            self.cursor.execute('''
                SELECT u.user_id, u.name, sgm.contributed
                FROM shared_goal_members sgm
                JOIN users u ON sgm.user_id = u.user_id
                WHERE sgm.goal_id = ?
                ORDER BY sgm.contributed DESC
            ''', (goal_id,))
            members = self.cursor.fetchall()
            return {'goal': goal, 'members': members}

    async def get_videos_by_category(self, language, category):
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                return await conn.fetch('''
                    SELECT id, title, url, duration, description, level
                    FROM videos
                    WHERE language = $1 AND category = $2
                    ORDER BY level, id
                    LIMIT 10
                ''', language, category)
        else:
            self.cursor.execute('''
                SELECT id, title, url, duration, description, level
                FROM videos
                WHERE language = ? AND category = ?
                ORDER BY level, id
                LIMIT 10
            ''', (language, category))
            return self.cursor.fetchall()

    async def get_random_video(self, language):
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                return await conn.fetchrow('''
                    SELECT title, url, duration, description
                    FROM videos
                    WHERE language = $1
                    ORDER BY RANDOM()
                    LIMIT 1
                ''', language)
        else:
            self.cursor.execute('''
                SELECT title, url, duration, description
                FROM videos
                WHERE language = ?
                ORDER BY RANDOM()
                LIMIT 1
            ''', (language,))
            return self.cursor.fetchone()

    async def get_daily_tip(self):
        day_of_year = datetime.now().timetuple().tm_yday
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow('SELECT tip, video_link FROM financial_tips OFFSET $1 LIMIT 1', day_of_year % 10)
                return {'tip': row['tip'], 'video_link': row['video_link']} if row else None
        else:
            self.cursor.execute('SELECT tip, video_link FROM financial_tips LIMIT 1 OFFSET ?', (day_of_year % 10,))
            row = self.cursor.fetchone()
            return {'tip': row[0], 'video_link': row[1]} if row else None

    async def close(self):
        if self.use_postgres and self.pool:
            await self.pool.close()
        elif self.conn:
            self.conn.close()