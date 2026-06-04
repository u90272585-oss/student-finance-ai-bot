# tests/test_rbac.py
import pytest

pytestmark = pytest.mark.asyncio


class TestRBAC:
    """Тесты для ролей (если есть)"""
    
    async def test_user_exists(self, db, test_user):
        """Проверка что пользователь существует"""
        db.cursor.execute(
            "SELECT COUNT(*) FROM users WHERE user_id = ?",
            (test_user["user_id"],)
        )
        count = db.cursor.fetchone()[0]
        assert count == 1
    
    async def test_admin_exists(self, db, test_admin):
        """Проверка что админ существует"""
        db.cursor.execute(
            "SELECT COUNT(*) FROM users WHERE user_id = ?",
            (test_admin["user_id"],)
        )
        count = db.cursor.fetchone()[0]
        assert count == 1