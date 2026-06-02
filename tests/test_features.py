import pytest

@pytest.mark.asyncio
async def test_features_register_and_track_expenses(db):
    """Сценарий: Регистрация и добавление транзакций"""
    user_id = 1001
    await db.add_user(user_id, "Test User", "KZ", "ru", "KZT")
    
    await db.add_transaction(user_id, "income", 100000.0, "Зарплата", "")
    await db.add_transaction(user_id, "income", 50000.0, "Бонус", "")
    await db.add_transaction(user_id, "expense", 15000.0, "Еда", "")
    await db.add_transaction(user_id, "expense", 5000.0, "Транспорт", "")
    
    stats = await db.get_stats(user_id, days=30)
    assert stats[0] == 150000.0
    assert stats[1] == 20000.0
    assert stats[2] == 130000.0

@pytest.mark.asyncio
async def test_features_create_goal_and_complete(db):
    user_id = 1002
    await db.add_user(user_id, "Goal User", "KZ", "ru", "KZT")
    
    goal_id = await db.add_goal(user_id, "Новый телефон", 300000.0)
    assert goal_id is not None
    
    await db.add_transaction(user_id, "income", 100000.0, "Зарплата", "")
    await db.update_goal_progress(user_id, 100000.0)
    
    goals = await db.get_goals(user_id)
    assert len(goals) > 0
    assert goals[0][3] == 100000.0

@pytest.mark.asyncio
async def test_features_premium_unlocks_features(db):
    user_id = 1003
    await db.add_user(user_id, "Premium User", "KZ", "ru", "KZT")
    
    assert await db.is_premium(user_id) is False
    await db.add_premium(user_id, days=30)
    assert await db.is_premium(user_id) is True

@pytest.mark.asyncio
async def test_features_shared_goal_collaboration(db):
    user1 = 2001
    user2 = 2002
    
    await db.add_user(user1, "User One", "KZ", "ru", "KZT")
    await db.add_user(user2, "User Two", "KZ", "ru", "KZT")
    
    invite_code = "SHARED2026"
    goal_id = await db.create_shared_goal(user1, "Совместная поездка", 100000.0, invite_code)
    assert goal_id is not None
    
    result = await db.join_shared_goal(user2, invite_code)
    assert result is not None
    
    await db.add_to_shared_goal(user1, goal_id, 40000.0)
    await db.add_to_shared_goal(user2, goal_id, 60000.0)
    
    details = await db.get_shared_goal_details(goal_id)
    assert details is not None
    assert details['goal'][3] >= 100000.0

@pytest.mark.asyncio
async def test_features_coins_and_discount(db):
    user_id = 3001
    await db.add_user(user_id, "Coin User", "KZ", "ru", "KZT")
    
    # Проверяем, что можно играть (первый раз)
    assert await db.can_play_today(user_id) is True
    
    # Добавляем монеты
    await db.add_coins(user_id, 100)
    coins, _ = await db.get_coins(user_id)
    assert coins == 100
    
    # После добавления монет играть сегодня уже нельзя
    assert await db.can_play_today(user_id) is False
    
    # Используем монеты для скидки
    result = await db.use_coins_for_discount(user_id, 50)
    assert result is True
    
    coins, _ = await db.get_coins(user_id)
    assert coins == 50