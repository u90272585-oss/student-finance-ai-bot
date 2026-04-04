import sqlite3
from datetime import datetime, timedelta
import random

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('finance.db')
        self.cursor = self.conn.cursor()
        self.init_db()
    
    def init_db(self):
        # Таблица пользователей
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
        
        # Таблица транзакций
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
        
        # Таблица целей
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
        
        # Таблица финансовых советов
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS financial_tips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tip TEXT,
                video_link TEXT,
                category TEXT
            )
        ''')
        
        # Таблица для видео
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
        
        # ========== ТАБЛИЦЫ ДЛЯ ОБЩИХ ЦЕЛЕЙ ==========
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
        
        # ========== ТАБЛИЦА ДЛЯ ЦВЕТОВ ЦЕЛЕЙ ==========
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS goal_plants (
                goal_id INTEGER PRIMARY KEY,
                plant_type TEXT DEFAULT 'lotus',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE
            )
        ''')
        
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
                self.cursor.execute('INSERT INTO financial_tips (tip, video_link, category) VALUES (?, ?, ?)',
                                  (tip, video_link, category))
            self.conn.commit()
    
    def init_videos(self):
        """Инициализация видео (10 русских, 20 английских)"""
        self.cursor.execute("SELECT COUNT(*) FROM videos")
        if self.cursor.fetchone()[0] == 0:
            # Русские видео
            russian_videos = [
                ("Почему ты бедный?", "https://youtu.be/ORhFkbMDw9Y?si=FosMCa9wOun63_Ok", "ru", "basics", "beginner", "15:00", "Основы финансовой грамотности"),
                ("Финансовая грамотность для чайников", "https://youtu.be/073P_bPnS3w?si=oeTYsGHwRsU1hR5N4", "ru", "saving", "beginner", "12:00", "Простые способы накопления"),
                ("Идеальный маршрут инвестора - 7 шагов", "https://youtu.be/9p-rz-k5BPM?si=R_E2ypS6OTRtqQ0e", "ru", "investing", "beginner", "20:00", "Введение в инвестиции"),
                ("Как ИЗБАВИТЬСЯ ОТ ДОЛГОВ? — АМОБЛОГ", "https://youtu.be/IzFy83zbN3o?si=SGXq3JIzTmvOjSiw", "ru", "debt", "intermediate", "18:00", "Управление кредитами"),
                ("Как вести учет личных финансов и что я понял 5 лет считая каждый рубль", "https://youtu.be/Lc-bcvLT-x0?si=bqNFIGoZu0YA4uOk", "ru", "budgeting", "beginner", "14:00", "Как составить бюджет"),
                ("Пассивный доход", "https://youtu.be/WulzE9M7VJw?si=U3cl9F177QL3uMIx", "ru", "investing", "intermediate", "22:00", "Создание пассивного дохода"),
                ("Как выйти на финансовую свободу?", "https://youtu.be/Fx917LJiVr0?si=JcgNd5dQZEeoBHD4", "ru", "goals", "advanced", "25:00", "Путь к финансовой независимости"),
                ("50 вещей которые делают тебя бедней", "https://youtu.be/Ovovu1P7u78?si=peKgJZUjDkx9O2sj", "ru", "basics", "intermediate", "16:00", "бедность"),
                ("Криптовалюта. Полное объяснение для чайников", "https://youtu.be/QPOdFedaujY?si=llTzA47FL41GT42D", "ru", "investing", "intermediate", "19:00", "Что такое криптовалюта"),
                ("Психология денег: Как мыслить богато", "https://youtu.be/gqQLews_xuQ?si=gy99LfUVMzLbh_YF", "ru", "basics", "beginner", "21:00", "Финансовое мышление"),
            ]
            
            # Английские видео
            english_videos = [
                ("Introduction to interest", "https://youtu.be/GtaoP0skPWc?si=KucETPlR1ug733qZ", "en", "debt", "beginner", "8:00", "What is interest?"),
                ("Compound interest basics", "https://youtu.be/Rm6UdfRs3gw?si=vEcYozLdc9Hqpkak", "en", "investing", "beginner", "10:00", "Power of compounding"),
                ("Budgeting 101", "https://youtu.be/gn8Obk30Pc0?si=GoU2vkD2TXf0czDo", "en", "budgeting", "beginner", "7:00", "How to create a budget"),
                ("Financial Literacy - A Beginners Guide to Financial Education", "https://youtu.be/4XZIv4__sQA?si=VqJ_DDJ0DCjLDk9Z", "en", "saving", "beginner", "9:00", "Financial literacy"),
                ("Credit cards and loans", "https://youtu.be/QvaHDxdxQFg?si=oTJugpLn2fS50ynD", "en", "debt", "intermediate", "12:00", "Managing credit wisely"),
                ("How To Read Stock Charts Like A PRO Investor (Beginner Guide)", "https://youtu.be/8i6n5z9OXzM?si=UL-QIGMHQ1te6tNt", "en", "investing", "intermediate", "15:00", "How stock market works"),
                ("Emergency Funds 101: You're Screwed If You Don't Have One", "https://youtu.be/tVGJqaOkqac?si=exDU4yGMTjCmc5OF", "en", "saving", "beginner", "6:00", "Why you need emergency fund"),
                ("7 Principles For Teenagers To Become Millionaires", "https://youtu.be/1-izXBhkiHw?si=fG5I_LegTLP8Nyte", "en", "goals", "intermediate", "14:00", "how to become a millionaire"),
                ("Inflation and purchasing power", "https://youtu.be/zIbNJCSCEjk?si=KGcDis7T9RAOY-Vs", "en", "basics", "intermediate", "11:00", "How inflation affects you"),
                ("Diversification strategy", "https://youtu.be/ZDExLnS9IC0?si=fe3WdnpFuHbfK_4d", "en", "investing", "advanced", "13:00", "Don't put all eggs in one basket"),
                ("Taxes 101", "https://youtu.be/AMXGBH7hoJY?si=hI3QxCIpjyq6-nNq", "en", "basics", "beginner", "9:00", "Understanding taxes"),
                ("Dividend Investing Secrets Explained | Investing for Complete Beginners", "https://youtu.be/BGdc9xRPedY?si=XtnrUVTemXlbmzj9", "en", "dividend", "advanced", "18:00", "Dividend Investing"),
                ("Debt snowball method", "https://youtu.be/SQkoIJ-BLHI?si=uRBbeAncH96gv7lp", "en", "debt", "intermediate", "8:00", "Paying off debt effectively"),
                ("Financial goals setting", "https://youtu.be/MabD5R8kRak?si=U-kdNM4hjrYodx6r", "en", "goals", "beginner", "7:00", "SMART financial goals"),
                ("Risk management", "https://youtu.be/kXkVV7PFWgE?si=uX3nY9X7t2RxwvhH", "en", "investing", "intermediate", "10:00", "Understanding investment risk"),
                ("Bonds explained", "https://youtu.be/7d9Lz0D0uzA?si=DMzZHn2_OB-ws9sj", "en", "investing", "intermediate", "12:00", "What are bonds"),
                ("Mutual funds for beginners", "https://youtu.be/nQ0r_prerXo?si=gbTeWXzFYE1CGuWY", "en", "investing", "beginner", "11:00", "Introduction to mutual funds"),
                ("401k and retirement accounts", "https://youtu.be/BhTTeIDZtKY?si=i-mqungHMRHK9EGK", "en", "goals", "intermediate", "13:00", "Retirement savings accounts"),
                ("Credit Scores Fully Explained 2026", "https://youtu.be/TOdnj2p91_c?si=Xn05d8--KHDau1Z0", "en", "debt", "beginner", "9:00", "Understanding credit scores"),
                ("Passive income streams", "https://youtu.be/XFh3tRObiLM?si=H2Vb05IPzA4Mzk_M", "en", "investing", "advanced", "16:00", "Building passive income"),
            ]
            
            for video in russian_videos:
                self.cursor.execute('''
                    INSERT INTO videos (title, url, language, category, level, duration, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', video)
            
            for video in english_videos:
                self.cursor.execute('''
                    INSERT INTO videos (title, url, language, category, level, duration, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', video)
            
            self.conn.commit()
    
    def get_videos_by_category(self, language, category):
        self.cursor.execute('''
            SELECT id, title, url, duration, description, level
            FROM videos 
            WHERE language = ? AND category = ?
            ORDER BY level, id
            LIMIT 10
        ''', (language, category))
        return self.cursor.fetchall()
    
    def get_random_video(self, language):
        self.cursor.execute('''
            SELECT title, url, duration, description
            FROM videos 
            WHERE language = ?
            ORDER BY RANDOM()
            LIMIT 1
        ''', (language,))
        return self.cursor.fetchone()
    
    def get_video_categories(self, language):
        self.cursor.execute('''
            SELECT category, COUNT(*)
            FROM videos 
            WHERE language = ?
            GROUP BY category
        ''', (language,))
        return self.cursor.fetchall()
    
    def get_random_tip(self):
        self.cursor.execute('SELECT tip, video_link FROM financial_tips ORDER BY RANDOM() LIMIT 1')
        row = self.cursor.fetchone()
        if row:
            return {'tip': row[0], 'video_link': row[1]}
        return None
    
    def get_daily_tip(self):
        day_of_year = datetime.now().timetuple().tm_yday
        self.cursor.execute('SELECT tip, video_link FROM financial_tips LIMIT 1 OFFSET ?', (day_of_year % 10,))
        row = self.cursor.fetchone()
        if row:
            return {'tip': row[0], 'video_link': row[1]}
        return None
    
    def add_user(self, user_id, name, country='KZ', language='ru', currency='KZT'):
        self.cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, name, country, language, currency) 
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, name, country, language, currency))
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def get_user(self, user_id):
        self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return self.cursor.fetchone()
    
    def update_language(self, user_id, language):
        self.cursor.execute('UPDATE users SET language = ? WHERE user_id = ?', (language, user_id))
        self.conn.commit()
    
    def update_currency(self, user_id, currency):
        self.cursor.execute('UPDATE users SET currency = ? WHERE user_id = ?', (currency, user_id))
        self.conn.commit()
    
    def update_country(self, user_id, country):
        self.cursor.execute('UPDATE users SET country = ? WHERE user_id = ?', (country, user_id))
        self.conn.commit()
    
    def add_transaction(self, user_id, trans_type, amount, category, note=""):
        self.cursor.execute('''
            INSERT INTO transactions (user_id, type, amount, category, note) 
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, trans_type, amount, category, note))
        self.conn.commit()
    
    def get_all_transactions(self, user_id):
        self.cursor.execute('''
            SELECT id, type, amount, category, note, date FROM transactions 
            WHERE user_id = ? ORDER BY date DESC
        ''', (user_id,))
        return self.cursor.fetchall()
    
    def get_stats(self, user_id, days=30):
        date_limit = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
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
        top_categories = self.cursor.fetchall()
        
        return income, expense, income - expense, top_categories
    
    def add_goal(self, user_id, name, target):
        self.cursor.execute(
            'INSERT INTO goals (user_id, name, target) VALUES (?, ?, ?)',
            (user_id, name, target)
        )
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_goals(self, user_id):
        self.cursor.execute(
            'SELECT id, name, target, current FROM goals WHERE user_id = ? ORDER BY created_at DESC',
            (user_id,)
        )
        return self.cursor.fetchall()
    
    def update_goal_progress(self, user_id, amount):
        self.cursor.execute(
            'SELECT id, target, current FROM goals WHERE user_id = ?',
            (user_id,)
        )
        goals = self.cursor.fetchall()
        completed_goals = []
        
        for goal_id, target, current in goals:
            if current < target:
                new_current = min(current + amount, target)
                self.cursor.execute(
                    'UPDATE goals SET current = ? WHERE id = ?',
                    (new_current, goal_id)
                )
                if new_current >= target:
                    completed_goals.append(goal_id)
        self.conn.commit()
        return completed_goals if completed_goals else None
    
    def delete_goal(self, goal_id):
        self.cursor.execute('DELETE FROM goals WHERE id = ?', (goal_id,))
        self.conn.commit()
    
    def delete_all_user_data(self, user_id):
        self.cursor.execute('DELETE FROM transactions WHERE user_id = ?', (user_id,))
        self.cursor.execute('DELETE FROM goals WHERE user_id = ?', (user_id,))
        self.conn.commit()
    
    # ========== МЕТОДЫ ДЛЯ ОБЩИХ ЦЕЛЕЙ ==========
    
    def create_shared_goal(self, creator_id, name, target, invite_code):
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
    
    def join_shared_goal(self, user_id, invite_code):
        self.cursor.execute('SELECT id, name, target, current, creator_id FROM shared_goals WHERE invite_code = ?', (invite_code,))
        goal = self.cursor.fetchone()
        
        if not goal:
            return None
        
        goal_id, name, target, current, creator_id = goal
        
        self.cursor.execute('SELECT * FROM shared_goal_members WHERE goal_id = ? AND user_id = ?', (goal_id, user_id))
        if self.cursor.fetchone():
            return 'already_member'
        
        self.cursor.execute('''
            INSERT INTO shared_goal_members (goal_id, user_id, contributed)
            VALUES (?, ?, ?)
        ''', (goal_id, user_id, 0))
        self.conn.commit()
        return {'goal_id': goal_id, 'name': name, 'target': target, 'current': current, 'creator_id': creator_id}
    
    def add_to_shared_goal(self, user_id, goal_id, amount):
        self.cursor.execute('UPDATE shared_goals SET current = current + ? WHERE id = ?', (amount, goal_id))
        self.cursor.execute('''
            UPDATE shared_goal_members SET contributed = contributed + ? 
            WHERE goal_id = ? AND user_id = ?
        ''', (amount, goal_id, user_id))
        self.conn.commit()
        
        self.cursor.execute('SELECT target, current FROM shared_goals WHERE id = ?', (goal_id,))
        target, current = self.cursor.fetchone()
        return current >= target
    
    def get_user_shared_goals(self, user_id):
        self.cursor.execute('''
            SELECT sg.id, sg.name, sg.target, sg.current, sg.invite_code, sg.creator_id,
                   (SELECT SUM(contributed) FROM shared_goal_members WHERE goal_id = sg.id) as total_contributed
            FROM shared_goals sg
            JOIN shared_goal_members sgm ON sg.id = sgm.goal_id
            WHERE sgm.user_id = ?
            ORDER BY sg.created_at DESC
        ''', (user_id,))
        return self.cursor.fetchall()
    
    def get_shared_goal_details(self, goal_id):
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
    
    # ========== МЕТОДЫ ДЛЯ ЦВЕТОВ ЦЕЛЕЙ ==========
    
    def set_goal_plant(self, goal_id, plant_type):
        """Установить тип растения для цели"""
        self.cursor.execute('''
            INSERT OR REPLACE INTO goal_plants (goal_id, plant_type)
            VALUES (?, ?)
        ''', (goal_id, plant_type))
        self.conn.commit()
    
    def get_goal_plant(self, goal_id):
        """Получить тип растения для цели"""
        self.cursor.execute('SELECT plant_type FROM goal_plants WHERE goal_id = ?', (goal_id,))
        row = self.cursor.fetchone()
        return row[0] if row else 'lotus'
    
    def close(self):
        self.conn.close()