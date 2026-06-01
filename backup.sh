#!/bin/bash

# 1. Формат даты и папка для бэкапов
DATE=$(date +%Y-%m-%d_%H-%M)
BACKUP_DIR="backups"

# Используем вашу переменную DATABASE_URL из окружения Render/Docker
DB_URL=$DATABASE_URL

# 2. Создаем папку, если её нет
mkdir -p $BACKUP_DIR

# 3. Делаем бэкап через pg_dump
pg_dump $DB_URL > $BACKUP_DIR/backup_$DATE.sql

# 4. Проверяем статус выполнения
if [ $? -eq 0 ]; then
    echo "✔ Backup created: $BACKUP_DIR/backup_$DATE.sql"
else
    echo "❌ Error!"
fi

# 5. Удаляем бэкапы старше 7 дней (исправила опечатку с экрана на правильный синтаксис)
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
echo "🧹 Old backups deleted"