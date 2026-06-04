# tests/test_auth.py
import pytest

pytestmark = pytest.mark.asyncio


class TestUserAuth:
    """Тесты для пользователей"""
    
    async def test_create_user(self, db):
        """Создание нового пользователя"""
        db.cursor.execute(
            "INSERT OR IGNORE INTO users (user_id, name) VALUES (?, ?)",
            (777777, "New User")
        )
        db.conn.commit()
        
        db.cursor.execute("SELECT COUNT(*) FROM users WHERE user_id = 777777")
        count = db.cursor.fetchone()[0]
        assert count == 1
    
    async def test_user_has_default_language(self, db):
        """Новый пользователь получает язык по умолчанию 'ru'"""
        db.cursor.execute(
            "INSERT OR IGNORE INTO users (user_id, name) VALUES (?, ?)",
            (888888, "Default User")
        )
        db.conn.commit()
        
        db.cursor.execute("SELECT language FROM users WHERE user_id = 888888")
        row = db.cursor.fetchone()
        
        if row:
            assert row[0] == "ru"
    
    async def test_get_user_by_id(self, db, test_user):
        """Поиск пользователя по user_id"""
        db.cursor.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (test_user["user_id"],)
        )
        user = db.cursor.fetchone()
        
        assert user is not None
        assert user[1] == test_user["name"]  # name на позиции 1