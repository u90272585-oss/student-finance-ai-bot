import os
import asyncio
from cerebras.cloud.sdk import Cerebras
from dotenv import load_dotenv

load_dotenv()

CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
if not CEREBRAS_API_KEY:
    print("⚠️ CEREBRAS_API_KEY не найден!")

client = Cerebras(api_key=CEREBRAS_API_KEY)

async def get_ai_response(user_message: str) -> str:
    try:
        # Запускаем синхронный вызов в отдельном потоке, чтобы не блокировать бота
        response = await asyncio.to_thread(
            client.chat.completions.create,
            messages=[{"role": "user", "content": user_message}],
            model="llama3.1-8b",
            max_tokens=500,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Ошибка Cerebras: {e}")
        return "😔 Сервис ИИ временно недоступен."