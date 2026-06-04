<<<<<<< HEAD
FROM python:3.11

WORKDIR /app

COPY . .

RUN pip install aiogram python-dotenv openai

CMD ["python", "bot.py"]
=======
FROM python:3.11-slim

WORKDIR /app

# Добавляем установку клиента PostgreSQL
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

<<<<<<< HEAD
CMD ["python", "bot.py"]
>>>>>>> 25448a4aaada500ce0b5a1e4c2441dd2e0883371
=======
CMD ["python", "bot.py"]
>>>>>>> f240d3e83dffb90e3b75096ef4f0ff73ae17cabe
