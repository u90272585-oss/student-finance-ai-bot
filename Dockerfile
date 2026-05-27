FROM python:3.11

WORKDIR /app

COPY . .

RUN pip install aiogram python-dotenv openai

CMD ["python", "bot.py"]