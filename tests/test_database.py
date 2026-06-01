import pytest
import sqlite3
import asyncio
from database import Database

@pytest.fixture
async def db():
    # Создаем экземпляр базы данных
    database = Database()
    
    # Изолируем тесты в оперативной памяти, чтобы избежать блокировок
    if not database.use_postgres:
        database.conn = sqlite3.connect(':memory:')
        database.cursor = database.conn.cursor()
        if hasattr(database, '_init_sqlite'):
            database._init_sqlite()
            
    if hasattr(database, 'connect'):
        try:
            await database.connect()
        except Exception:
            pass
            
    yield database
    
    # Очистка после теста
    if not database.use_postgres and database.conn:
        database.conn.close()
    if hasattr(database, 'pool') and database.pool:
        await database.pool.close()

@pytest.mark.asyncio
async def test_scenario_register_and_track_expenses(db):
    # Сценарий: Регистрация и добавление транзакций
    await db.add_user(55555, "Scenario User", "KZ", "ru", "KZT")
    await db.add_transaction(55555, "income", 200000.0, "Salary", "2026-06-01")
    await db.add_transaction(55555, "expense", 15000.0, "Groceries", "2026-06-01")
    
    stats = await db.get_stats(55555, days=1)
    if isinstance(stats, dict):
        assert stats.get('total_income', stats.get('income', 0)) == 200000.0
        assert stats.get('total_expense', stats.get('expense', 0)) == 15000.0
    else:
        assert stats[0] == 200000.0
        assert stats[1] == 15000.0

@pytest.mark.asyncio
async def test_scenario_create_goal_and_complete(db):
    # Сценарий: Создание цели и проверка её наличия
    await db.add_user(55555, "Scenario User", "KZ", "ru", "KZT")
    goal_id = await db.add_goal(55555, "New Laptop", 400000.0)
    assert goal_id is not None
    
    goals = await db.get_goals(55555)
    assert len(goals) > 0

@pytest.mark.asyncio
async def test_scenario_premium_unlocks_features(db):
    # Сценарий: Покупка премиума и проверка статуса
    await db.add_user(55555, "Scenario User", "KZ", "ru", "KZT")
    assert await db.is_premium(55555) is False
    
    await db.add_premium(55555, days=30)
    assert await db.is_premium(55555) is True

@pytest.mark.asyncio
async def test_scenario_shared_goal_collaboration(db):
    # Сценарий: Совместные цели двух пользователей
    await db.add_user(11111, "User One", "KZ", "ru", "KZT")
    await db.add_user(22222, "User Two", "KZ", "ru", "KZT")
    
    code = await db.create_shared_goal(11111, "Trip to Almaty", 50000.0, "ALM2026")
    assert code is not None
    
    join_res = await db.join_shared_goal(22222, "ALM2026")
    assert join_res is not None

@pytest.mark.asyncio
async def test_scenario_coins_and_discount(db):
    # Сценарий: Заработок монет и покупка скидки
    await db.add_user(55555, "Scenario User", "KZ", "ru", "KZT")
    await db.add_coins(55555, 100)
    
    success = await db.use_coins_for_discount(55555, 40)
    assert success is True
    
    res = await db.get_coins(55555)
    if isinstance(res, tuple):
        assert res[0] == 60
    else:
        assert res.get('total_coins', res.get('coins', 0)) == 60