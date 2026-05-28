<<<<<<< HEAD
FROM python:3.11

WORKDIR /app

COPY . .

RUN pip install aiogram python-dotenv openai

CMD ["python", "bot.py"]
=======
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
>>>>>>> 25448a4aaada500ce0b5a1e4c2441dd2e0883371
