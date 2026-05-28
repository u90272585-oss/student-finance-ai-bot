FROM python:3.11-slim

WORKDIR /app

# Добавляем установку клиента PostgreSQL
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "bot.py"]