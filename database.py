import random
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager


class Database:
    def __init__(self):
        self.conn = sqlite3.connect("finance.db")
        self.conn.row_factory = sqlite3.Row  # Для удобного доступа по именам колонок
        self.cursor = self.conn.cursor()
        self.init_db()

    def init_db(self):
        # Таблица пользователей (расширенная)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                country TEXT DEFAULT 'KZ',
                language TEXT DEFAULT 'ru',
                currency TEXT DEFAULT 'KZT',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)

        # Таблица транзакций (с user_id FK)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT CHECK(type IN ('income', 'expense')),
                amount REAL NOT NULL CHECK(amount > 0),
                category TEXT NOT NULL,
                note TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)

        # Таблица целей (с user_id FK)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                target REAL NOT NULL CHECK(target > 0),
                current REAL DEFAULT 0 CHECK(current >= 0),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)

        # Таблица финансовых советов
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS financial_tips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tip TEXT NOT NULL,
                video_link TEXT,
                category TEXT
            )
        """)

        # Таблица для видео
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                language TEXT,
                category TEXT,
                level TEXT,
                duration TEXT,
                description TEXT
            )
        """)

        # Общие цели (без изменений)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS shared_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                target REAL NOT NULL,
                current REAL DEFAULT 0,
                creator_id INTEGER NOT NULL,
                invite_code TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (creator_id) REFERENCES users(user_id)
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS shared_goal_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                contributed REAL DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (goal_id) REFERENCES shared_goals(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                UNIQUE(goal_id, user_id)
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS goal_plants (
                goal_id INTEGER PRIMARY KEY,
                plant_type TEXT DEFAULT 'lotus',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS premium_users (
                user_id INTEGER PRIMARY KEY,
                premium_until TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)

        # Индексы для производительности
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_user_date ON transactions(user_id, date)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_user_type ON transactions(user_id, type)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_goals_user ON goals(user_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_shared_members_user ON shared_goal_members(user_id)")

        self.conn.commit()
        self.init_financial_tips()
        self.init_videos()

    def init_financial_tips(self):
        """Инициализация финансовых советов"""
        self.cursor.execute("SELECT COUNT(*) FROM financial_tips")
        if self.cursor.fetchone()[0] == 0:
            tips = [
                ("Правило 50/30/20: 50% на必需品, 30% на желания, 20% на сбережения", "", "budgeting"),
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
                self.cursor.execute(
                    "INSERT INTO financial_tips (tip, video_link, category) VALUES (?, ?, ?)",
                    (tip, video_link, category),
                )
            self.conn.commit()

    def init_videos(self):
        """Инициализация видео"""
        self.cursor.execute("SELECT COUNT(*) FROM videos")
        if self.cursor.fetchone()[0] == 0:
            russian_videos = [
                ("Почему ты бедный?", "https://youtu.be/ORhFkbMDw9Y", "ru", "basics", "beginner", "15:00", "Основы финансовой грамотности"),
                ("Финансовая грамотность для чайников", "https://youtu.be/073P_bPnS3w", "ru", "saving", "beginner", "12:00", "Простые способы накопления"),
            ]
            english_videos = [
                ("Introduction to interest", "https://youtu.be/GtaoP0skPWc", "en", "debt", "beginner", "8:00", "What is interest?"),
                ("Compound interest basics", "https://youtu.be/Rm6UdfRs3gw", "en", "investing", "beginner", "10:00", "Power of compounding"),
            ]

            for video in russian_videos + english_videos:
                self.cursor.execute(
                    "INSERT INTO videos (title, url, language, category, level, duration, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    video,
                )
            self.conn.commit()

    # ========== ПОЛЬЗОВАТЕЛИ (С ПРОВЕРКОЙ ВЛАДЕНИЯ) ==========
    
    def create_user(self, username: str, email: str, password_hash: str) -> int:
        """Создание нового пользователя"""
        try:
            self.cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, password_hash),
            )
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Получение пользователя по ID"""
        self.cursor.execute(
            "SELECT user_id, username, email, role, country, language, currency, is_active, created_at, last_login FROM users WHERE user_id = ?",
            (user_id,),
        )
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Получение пользователя по username (для аутентификации)"""
        self.cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Получение пользователя по email"""
        self.cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def update_last_login(self, user_id: int):
        """Обновление времени последнего входа"""
        self.cursor.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = ?",
            (user_id,),
        )
        self.conn.commit()

    def get_user_role(self, user_id: int) -> str:
        """Получение роли пользователя для RBAC"""
        self.cursor.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
        row = self.cursor.fetchone()
        return row["role"] if row else "user"

    # ========== ТРАНЗАКЦИИ (С ПРОВЕРКОЙ ВЛАДЕНИЯ) ==========
    
    def add_transaction(self, user_id: int, trans_type: str, amount: float, category: str, note: str = "") -> int:
        """Добавление транзакции с проверкой владения"""
        self.cursor.execute(
            """
            INSERT INTO transactions (user_id, type, amount, category, note) 
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, trans_type, amount, category, note),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_transaction(self, transaction_id: int, user_id: int) -> Optional[Dict]:
        """Получение транзакции с проверкой владения"""
        self.cursor.execute(
            """
            SELECT id, user_id, type, amount, category, note, date 
            FROM transactions 
            WHERE id = ? AND user_id = ?
            """,
            (transaction_id, user_id),
        )
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def get_all_transactions(self, user_id: int, limit: int = 100) -> List[Dict]:
        """Получение всех транзакций пользователя"""
        self.cursor.execute(
            """
            SELECT id, type, amount, category, note, date 
            FROM transactions 
            WHERE user_id = ? 
            ORDER BY date DESC 
            LIMIT ?
            """,
            (user_id, limit),
        )
        return [dict(row) for row in self.cursor.fetchall()]

    def update_transaction(self, transaction_id: int, user_id: int, **kwargs) -> bool:
        """Обновление транзакции с проверкой владения"""
        allowed_fields = ["type", "amount", "category", "note"]
        updates = []
        values = []
        
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                updates.append(f"{field} = ?")
                values.append(value)
        
        if not updates:
            return False
        
        values.extend([transaction_id, user_id])
        query = f"""
            UPDATE transactions 
            SET {', '.join(updates)} 
            WHERE id = ? AND user_id = ?
        """
        
        self.cursor.execute(query, values)
        self.conn.commit()
        return self.cursor.rowcount > 0

    def delete_transaction(self, transaction_id: int, user_id: int) -> bool:
        """Удаление транзакции с проверкой владения"""
        self.cursor.execute(
            "DELETE FROM transactions WHERE id = ? AND user_id = ?",
            (transaction_id, user_id),
        )
        self.conn.commit()
        return self.cursor.rowcount > 0

    def get_stats(self, user_id: int, days: int = 30) -> Tuple[float, float, float, List]:
        """Получение статистики с проверкой владения"""
        date_limit = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        self.cursor.execute(
            """
            SELECT COALESCE(SUM(amount), 0) FROM transactions 
            WHERE user_id = ? AND type = 'income' AND date >= ?
            """,
            (user_id, date_limit),
        )
        income = self.cursor.fetchone()[0]

        self.cursor.execute(
            """
            SELECT COALESCE(SUM(amount), 0) FROM transactions 
            WHERE user_id = ? AND type = 'expense' AND date >= ?
            """,
            (user_id, date_limit),
        )
        expense = self.cursor.fetchone()[0]

        self.cursor.execute(
            """
            SELECT category, SUM(amount) FROM transactions 
            WHERE user_id = ? AND type = 'expense' AND date >= ?
            GROUP BY category ORDER BY SUM(amount) DESC LIMIT 5
            """,
            (user_id, date_limit),
        )
        top_categories = self.cursor.fetchall()

        return income, expense, income - expense, top_categories

    # ========== ЦЕЛИ (С ПРОВЕРКОЙ ВЛАДЕНИЯ) ==========
    
    def add_goal(self, user_id: int, name: str, target: float) -> int:
        """Добавление цели с проверкой владения"""
        self.cursor.execute(
            "INSERT INTO goals (user_id, name, target) VALUES (?, ?, ?)",
            (user_id, name, target),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_goal(self, goal_id: int, user_id: int) -> Optional[Dict]:
        """Получение цели с проверкой владения"""
        self.cursor.execute(
            "SELECT id, name, target, current, created_at FROM goals WHERE id = ? AND user_id = ?",
            (goal_id, user_id),
        )
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def get_goals(self, user_id: int) -> List[Dict]:
        """Получение всех целей пользователя"""
        self.cursor.execute(
            "SELECT id, name, target, current, created_at FROM goals WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        )
        return [dict(row) for row in self.cursor.fetchall()]

    def update_goal_progress(self, user_id: int, amount: float) -> List[int]:
        """Обновление прогресса целей с проверкой владения"""
        self.cursor.execute(
            "SELECT id, target, current FROM goals WHERE user_id = ? AND current < target",
            (user_id,)
        )
        goals = self.cursor.fetchall()
        completed_goals = []

        for goal_id, target, current in goals:
            new_current = min(current + amount, target)
            self.cursor.execute(
                "UPDATE goals SET current = ? WHERE id = ? AND user_id = ?",
                (new_current, goal_id, user_id)
            )
            if new_current >= target:
                completed_goals.append(goal_id)
        
        self.conn.commit()
        return completed_goals

    def delete_goal(self, goal_id: int, user_id: int) -> bool:
        """Удаление цели с проверкой владения"""
        self.cursor.execute(
            "DELETE FROM goals WHERE id = ? AND user_id = ?",
            (goal_id, user_id)
        )
        self.conn.commit()
        return self.cursor.rowcount > 0

    def set_goal_plant(self, goal_id: int, user_id: int, plant_type: str) -> bool:
        """Установка растения для цели с проверкой владения"""
        # Сначала проверяем, принадлежит ли цель пользователю
        if not self.get_goal(goal_id, user_id):
            return False
        
        self.cursor.execute(
            "INSERT OR REPLACE INTO goal_plants (goal_id, plant_type) VALUES (?, ?)",
            (goal_id, plant_type),
        )
        self.conn.commit()
        return True

    # ========== ОБЩИЕ ЦЕЛИ (С ПРОВЕРКОЙ УЧАСТИЯ) ==========
    
    def create_shared_goal(self, creator_id: int, name: str, target: float, invite_code: str) -> int:
        """Создание общей цели"""
        self.cursor.execute(
            """
            INSERT INTO shared_goals (name, target, creator_id, invite_code)
            VALUES (?, ?, ?, ?)
            """,
            (name, target, creator_id, invite_code),
        )
        goal_id = self.cursor.lastrowid
        
        self.cursor.execute(
            "INSERT INTO shared_goal_members (goal_id, user_id) VALUES (?, ?)",
            (goal_id, creator_id),
        )
        self.conn.commit()
        return goal_id

    def join_shared_goal(self, user_id: int, invite_code: str) -> Optional[Dict]:
        """Присоединение к общей цели"""
        self.cursor.execute(
            "SELECT id, name, target, current FROM shared_goals WHERE invite_code = ?",
            (invite_code,),
        )
        goal = self.cursor.fetchone()
        
        if not goal:
            return None
        
        goal_id = goal["id"]
        
        # Проверяем, не состоит ли уже
        self.cursor.execute(
            "SELECT 1 FROM shared_goal_members WHERE goal_id = ? AND user_id = ?",
            (goal_id, user_id),
        )
        if self.cursor.fetchone():
            return {"error": "already_member"}
        
        self.cursor.execute(
            "INSERT INTO shared_goal_members (goal_id, user_id) VALUES (?, ?)",
            (goal_id, user_id),
        )
        self.conn.commit()
        return dict(goal)

    def add_to_shared_goal(self, user_id: int, goal_id: int, amount: float) -> bool:
        """Добавление средств в общую цель (с проверкой членства)"""
        if amount <= 0:
            return False
        
        # Проверяем, является ли пользователь участником
        self.cursor.execute(
            "SELECT 1 FROM shared_goal_members WHERE goal_id = ? AND user_id = ?",
            (goal_id, user_id),
        )
        if not self.cursor.fetchone():
            return False
        
        self.cursor.execute(
            "UPDATE shared_goals SET current = current + ? WHERE id = ?",
            (amount, goal_id),
        )
        
        self.cursor.execute(
            "UPDATE shared_goal_members SET contributed = contributed + ? WHERE goal_id = ? AND user_id = ?",
            (amount, goal_id, user_id),
        )
        self.conn.commit()
        
        self.cursor.execute(
            "SELECT target, current FROM shared_goals WHERE id = ?",
            (goal_id,),
        )
        target, current = self.cursor.fetchone()
        return current >= target

    def get_user_shared_goals(self, user_id: int) -> List[Dict]:
        """Получение общих целей пользователя"""
        self.cursor.execute(
            """
            SELECT sg.id, sg.name, sg.target, sg.current, sg.invite_code, sg.creator_id
            FROM shared_goals sg
            JOIN shared_goal_members sgm ON sg.id = sgm.goal_id
            WHERE sgm.user_id = ?
            ORDER BY sg.created_at DESC
            """,
            (user_id,),
        )
        return [dict(row) for row in self.cursor.fetchall()]

    # ========== ПРЕМИУМ ==========
    
    def is_premium(self, user_id: int) -> bool:
        """Проверка премиум статуса"""
        self.cursor.execute(
            "SELECT premium_until FROM premium_users WHERE user_id = ?",
            (user_id,)
        )
        row = self.cursor.fetchone()
        if row and row["premium_until"]:
            return datetime.now() < datetime.fromisoformat(row["premium_until"])
        return False

    def add_premium(self, user_id: int, days: int = 30):
        """Добавление премиум"""
        until = (datetime.now() + timedelta(days=days)).isoformat()
        self.cursor.execute(
            "INSERT OR REPLACE INTO premium_users (user_id, premium_until) VALUES (?, ?)",
            (user_id, until),
        )
        self.conn.commit()

    # ========== ВИДЕО И СОВЕТЫ (ПУБЛИЧНЫЕ) ==========
    
    def get_random_tip(self) -> Optional[Dict]:
        """Получение случайного совета"""
        self.cursor.execute("SELECT tip, video_link FROM financial_tips ORDER BY RANDOM() LIMIT 1")
        row = self.cursor.fetchone()
        return {"tip": row["tip"], "video_link": row["video_link"]} if row else None

    def get_videos_by_category(self, language: str, category: str, limit: int = 10) -> List[Dict]:
        """Получение видео по категории"""
        self.cursor.execute(
            """
            SELECT id, title, url, duration, description, level
            FROM videos 
            WHERE language = ? AND category = ?
            ORDER BY level, id
            LIMIT ?
            """,
            (language, category, limit),
        )
        return [dict(row) for row in self.cursor.fetchall()]

    # ========== ADMIN-ФУНКЦИИ (ТОЛЬКО ДЛЯ АДМИНОВ) ==========
    
    def get_all_users(self, admin_id: int, limit: int = 100) -> List[Dict]:
        """Получение всех пользователей (только для админов)"""
        # Сначала проверяем роль
        role = self.get_user_role(admin_id)
        if role != "admin":
            return []
        
        self.cursor.execute(
            "SELECT user_id, username, email, role, is_active, created_at, last_login FROM users LIMIT ?",
            (limit,),
        )
        return [dict(row) for row in self.cursor.fetchall()]

    def get_all_transactions_admin(self, admin_id: int, limit: int = 1000) -> List[Dict]:
        """Получение всех транзакций (только для админов)"""
        role = self.get_user_role(admin_id)
        if role != "admin":
            return []
        
        self.cursor.execute(
            """
            SELECT t.id, t.user_id, u.username, t.type, t.amount, t.category, t.date
            FROM transactions t
            JOIN users u ON t.user_id = u.user_id
            ORDER BY t.date DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(row) for row in self.cursor.fetchall()]

    def set_user_role(self, admin_id: int, target_user_id: int, role: str) -> bool:
        """Изменение роли пользователя (только для админов)"""
        admin_role = self.get_user_role(admin_id)
        if admin_role != "admin" or role not in ["user", "admin", "moderator"]:
            return False
        
        self.cursor.execute(
            "UPDATE users SET role = ? WHERE user_id = ?",
            (role, target_user_id),
        )
        self.conn.commit()
        return self.cursor.rowcount > 0

    def delete_user_admin(self, admin_id: int, target_user_id: int) -> bool:
        """Удаление пользователя (только для админов)"""
        admin_role = self.get_user_role(admin_id)
        if admin_role != "admin":
            return False
        
        # Нельзя удалить самого себя
        if admin_id == target_user_id:
            return False
        
        self.cursor.execute("DELETE FROM users WHERE user_id = ?", (target_user_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0

    # ========== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ==========
    
    def delete_all_user_data(self, user_id: int):
        """Полное удаление всех данных пользователя"""
        self.cursor.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
        self.cursor.execute("DELETE FROM goals WHERE user_id = ?", (user_id,))
        self.cursor.execute("DELETE FROM shared_goal_members WHERE user_id = ?", (user_id,))
        self.cursor.execute("DELETE FROM premium_users WHERE user_id = ?", (user_id,))
        self.cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        self.conn.commit()

    def close(self):
        self.conn.close()