import sqlite3
import os
import sys
import pytest

# Настройка путей, чтобы Python видел твою базу данных
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Database

# Автоматически помечаем все тесты в файле как асинхронные
pytestmark = pytest.mark.asyncio


# Фикстура настройки и очистки базы данных
@pytest.fixture(autouse=True)
async def db_session():
    test_db_path = 'test_finance.db'
    
    db_instance = Database.__new__(Database)
    db_instance.use_postgres = False
    db_instance.pool = None
    db_instance.conn = sqlite3.connect(test_db_path)
    db_instance.cursor = db_instance.conn.cursor()
    
    # Асинхронно создаем таблицы перед тестом
    await db_instance._init_sqlite()
    
    yield db_instance
    
    # Очистка после выполнения теста
    db_instance.conn.close()
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


# Класс с тестами на чистом pytest
class TestDatabase:

    async def test_add_user(self, db_session):
        await db_session.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        user = await db_session.get_user(123456)
        assert user is not None
        assert user[0] == 123456

    async def test_get_user_not_found(self, db_session):
        user = await db_session.get_user(999999)
        assert user is None

    async def test_update_language(self, db_session):
        await db_session.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        await db_session.update_language(123456, "en")
        user = await db_session.get_user(123456)
        assert user[3] == "en"

    async def test_update_currency(self, db_session):
        await db_session.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        await db_session.update_currency(123456, "USD")
        user = await db_session.get_user(123456)
        assert user[4] == "USD"

    async def test_add_transaction(self, db_session):
        await db_session.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        await db_session.add_transaction(123456, "income", 50000, "Salary", "")
        transactions = await db_session.get_all_transactions(123456)
        assert len(transactions) == 1
        assert transactions[0][2] == 50000

    async def test_get_stats_balance(self, db_session):
        await db_session.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        await db_session.add_transaction(123456, "income", 100000, "Salary", "")
        await db_session.add_transaction(123456, "expense", 30000, "Food", "")
        income, expense, balance, _ = await db_session.get_stats(123456)
        assert income == 100000
        assert expense == 30000
        assert balance == 70000

    async def test_get_stats_empty(self, db_session):
        await db_session.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        income, expense, balance, _ = await db_session.get_stats(123456)
        assert income == 0
        assert expense == 0

    async def test_add_goal(self, db_session):
        await db_session.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        await db_session.add_goal(123456, "New iPhone", 500000)
        goals = await db_session.get_goals(123456)
        assert len(goals) == 1
        assert goals[0][1] == "New iPhone"

    async def test_delete_goal(self, db_session):
        await db_session.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        goal_id = await db_session.add_goal(123456, "Test Goal", 100000)
        await db_session.delete_goal(goal_id)
        goals = await db_session.get_goals(123456)
        assert len(goals) == 0

    async def test_goal_plant(self, db_session):
        await db_session.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        goal_id = await db_session.add_goal(123456, "Test Goal", 100000)
        await db_session.set_goal_plant(goal_id, "rose")
        plant = await db_session.get_goal_plant(goal_id)
        assert plant == "rose"

    async def test_add_premium(self, db_session):
        await db_session.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        await db_session.add_premium(123456, 30)
        assert await db_session.is_premium(123456) is True

    async def test_remove_premium(self, db_session):
        await db_session.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        await db_session.add_premium(123456, 30)
        await db_session.remove_premium(123456)
        assert await db_session.is_premium(123456) is False

    async def test_is_premium_false_by_default(self, db_session):
        await db_session.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        assert await db_session.is_premium(123456) is False

    async def test_add_coins(self, db_session):
        await db_session.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        await db_session.add_coins(123456, 25)
        total_coins, _ = await db_session.get_coins(123456)
        assert total_coins == 25

    async def test_coins_accumulate(self, db_session):
        await db_session.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        await db_session.add_coins(123456, 25)
        await db_session.add_coins(123456, 30)
        total_coins, _ = await db_session.get_coins(123456)
        assert total_coins == 55

    async def test_can_play_today(self, db_session):
        await db_session.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        assert await db_session.can_play_today(123456) is True

    async def test_cannot_play_twice_today(self, db_session):
        await db_session.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        await db_session.add_coins(123456, 25)
        assert await db_session.can_play_today(123456) is False

    async def test_use_coins_for_discount(self, db_session):
        await db_session.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        await db_session.add_coins(123456, 500)
        result = await db_session.use_coins_for_discount(123456, 500)
        assert result is True
        total_coins, _ = await db_session.get_coins(123456)
        assert total_coins == 0

    async def test_use_coins_insufficient(self, db_session):
        await db_session.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        await db_session.add_coins(123456, 100)
        result = await db_session.use_coins_for_discount(123456, 500)
        assert result is False

    async def test_create_shared_goal(self, db_session):
        await db_session.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        goal_id = await db_session.create_shared_goal(123456, "Trip to Bali", 500000, "ABC12345")
        assert goal_id is not None

    async def test_join_shared_goal(self, db_session):
        await db_session.add_user(123456, "Creator", "KZ", "ru", "KZT")
        await db_session.add_user(789012, "Joiner", "KZ", "ru", "KZT")
        await db_session.create_shared_goal(123456, "Trip to Bali", 500000, "ABC12345")
        result = await db_session.join_shared_goal(789012, "ABC12345")
        assert result is not None

    async def test_join_shared_goal_invalid_code(self, db_session):
        await db_session.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        result = await db_session.join_shared_goal(123456, "INVALID1")
        assert result is None