import pytest
import sqlite3
from database import Database

@pytest.fixture
async def db_session():
    database = Database()
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
    
    if not database.use_postgres and database.conn:
        database.conn.close()
    if hasattr(database, 'pool') and database.pool:
        await database.pool.close()

@pytest.mark.asyncio
async def test_scenario_register_and_track_expenses(db_session):
    user_id = 11111
    await db_session.add_user(user_id, "Uldana", "KZ", "ru", "KZT")
    await db_session.add_transaction(user_id, "income", 200000, "Salary", "2026-06-01")
    await db_session.add_transaction(user_id, "expense", 15000, "Groceries", "2026-06-01")
    
    stats = await db_session.get_stats(user_id, days=1)
    if isinstance(stats, dict):
        income = stats.get('total_income', stats.get('income', 0))
        expense = stats.get('total_expense', stats.get('expense', 0))
        assert income == 200000
        assert expense == 15000
    else:
        assert stats[0] == 200000
        assert stats[1] == 15000

@pytest.mark.asyncio
async def test_scenario_create_goal_and_complete(db_session):
    user_id = 22222
    await db_session.add_user(user_id, "Madi", "KZ", "ru", "KZT")
    goal_id = await db_session.add_goal(user_id, "Iphone", 500000)
    
    completed = await db_session.update_goal_progress(user_id, 500000)
    assert completed is not None

@pytest.mark.asyncio
async def test_scenario_premium_unlocks_features(db_session):
    user_id = 33333
    await db_session.add_user(user_id, "Anya", "KZ", "en", "USD")
    
    await db_session.add_premium(user_id, days=30)
    has_premium = await db_session.is_premium(user_id)
    assert has_premium is True

@pytest.mark.asyncio
async def test_scenario_shared_goal_collaboration(db_session):
    user_a = 44444
    user_b = 55555
    await db_session.add_user(user_a, "User A", "KZ", "ru", "USD")
    await db_session.add_user(user_b, "User B", "KZ", "ru", "USD")
    
    goal_id = await db_session.create_shared_goal(user_a, "Trip", 5000, "TRIP2026")
    assert goal_id is not None
    
    join_res = await db_session.join_shared_goal(user_b, "TRIP2026")
    assert join_res is not None

@pytest.mark.asyncio
async def test_scenario_coins_and_discount(db_session):
    user_id = 66666
    await db_session.add_user(user_id, "User C", "KZ", "en", "EUR")
    await db_session.add_coins(user_id, 200)
    
    used = await db_session.use_coins_for_discount(user_id, 150)
    assert used is True
    
    res = await db_session.get_coins(user_id)
    if isinstance(res, tuple):
        assert res[0] == 50
    else:
        assert res.get('total_coins', res.get('coins', 0)) == 50