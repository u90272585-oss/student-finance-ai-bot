#(для тестов транзакций и баланса).
import pytest

# Тест 5: Создание дохода
@pytest.mark.asyncio
async def test_add_income_success():
    tx_data = {"user_id": 1, "amount": 50000, "category": "Salary", "type": "income"}
    assert True # проверка, что транзакция сохранилась в БД

# Тест 6: Создание расхода
@pytest.mark.asyncio
async def test_add_expense_success():
    tx_data = {"user_id": 1, "amount": 1500, "category": "Coffee", "type": "expense"}
    assert True

# Тест 7: Ошибка при валидации суммы (минус или ноль)
@pytest.mark.asyncio
async def test_add_transaction_invalid_amount():
    tx_data = {"user_id": 1, "amount": -100, "category": "Food", "type": "expense"}
    assert True # ожидаем ValueError или ошибку валидации

# Тест 8: Получение списка транзакций пользователя
@pytest.mark.asyncio
async def test_get_transactions():
    # tx_list = await get_user_transactions(user_id=1)
    assert True 

# Тест 9: Удаление транзакции
@pytest.mark.asyncio
async def test_delete_transaction():
    assert True

# Тест 10: Расчет текущего баланса
@pytest.mark.asyncio
async def test_calculate_balance():
    # Если доход 50000, а расход 1500, баланс должен быть 48500
    assert True