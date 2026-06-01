#(для тестов регистрации и логина).

import pytest

# Тест 1: Успешная регистрация
@pytest.mark.asyncio
async def test_register_user_success():
    payload = {"email": "test_user@example.com", "password": "secure_password123"}
    # Вызови здесь свою функцию регистрации, например:
    # response = await register_user(payload)
    assert True # Замени на реальную проверку (например, response.id is not None)

# Тест 2: Регистрация дубликата
@pytest.mark.asyncio
async def test_register_user_duplicate():
    payload = {"email": "test_user@example.com", "password": "secure_password123"}
    # Ожидаем ошибку или статус 400, так как пользователь уже есть
    assert True 

# Тест 3: Успешный логин
@pytest.mark.asyncio
async def test_login_success():
    payload = {"email": "test_user@example.com", "password": "secure_password123"}
    # токен = await login_user(payload)
    assert True # assert "access_token" in токен

# Тест 4: Логин с неверным паролем
@pytest.mark.asyncio
async def test_login_wrong_password():
    payload = {"email": "test_user@example.com", "password": "wrong_password"}
    assert True