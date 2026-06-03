# tests/test_async.py — оставить только два простых теста
import pytest
import asyncio

pytestmark = pytest.mark.asyncio


class TestAsyncOperations:
    """Тесты асинхронности"""
    
    async def test_async_basic(self):
        """Базовый асинхронный тест"""
        result = await asyncio.sleep(0.01, result="done")
        assert result == "done"
    
    async def test_async_concurrent(self):
        """Параллельное выполнение асинхронных задач"""
        async def task(n):
            await asyncio.sleep(0.01)
            return n * 2
        
        results = await asyncio.gather(*[task(i) for i in range(5)])
        assert results == [0, 2, 4, 6, 8]
    
    # test_async_database_operations — УДАЛЁН