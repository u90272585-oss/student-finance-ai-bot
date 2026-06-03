# tests/test_ownership.py
import pytest

pytestmark = pytest.mark.asyncio


class TestDataOwnership:
    """Тесты: пользователь видит только свои данные"""
    
    async def test_user_sees_own_data(self, db, test_user):
        """Пользователь видит свои данные"""
        db.cursor.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (test_user["user_id"],)
        )
        user_data = db.cursor.fetchone()
        
        assert user_data is not None
        assert user_data[1] == test_user["name"]
    
    async def test_transactions_belong_to_user(self, db, test_user):
        """Транзакции принадлежат пользователю"""
        # Добавляем транзакцию
        db.cursor.execute(
            "INSERT INTO transactions (user_id, type, amount, category) VALUES (?, ?, ?, ?)",
            (test_user["user_id"], "income", 1000, "salary")
        )
        db.conn.commit()
        
        # Получаем транзакции только этого пользователя
        db.cursor.execute(
            "SELECT COUNT(*) FROM transactions WHERE user_id = ?",
            (test_user["user_id"],)
        )
        count = db.cursor.fetchone()[0]
        
        assert count == 1
    
    async def test_cannot_see_other_user_transactions(self, db, test_user, test_admin):
        """Пользователь не видит транзакции другого пользователя"""
        # Транзакция админа
        db.cursor.execute(
            "INSERT INTO transactions (user_id, type, amount, category) VALUES (?, ?, ?, ?)",
            (test_admin["user_id"], "income", 5000, "bonus")
        )
        db.conn.commit()
        
        # Проверяем что у обычного пользователя нет этой транзакции
        db.cursor.execute(
            "SELECT COUNT(*) FROM transactions WHERE user_id = ? AND amount = 5000",
            (test_user["user_id"],)
        )
        count = db.cursor.fetchone()[0]
        
        assert count == 0