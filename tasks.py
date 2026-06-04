from celery_app import celery_app
import logging
from database import Database

logger = logging.getLogger(__name__)


@celery_app.task(name="send_welcome_message")
def send_welcome_message(user_id: int, name: str):
    """Фоновая отправка приветственного сообщения"""
    logger.info(f"Sending welcome message to user {user_id} ({name})")
    return {"status": "sent", "user_id": user_id}


@celery_app.task(name="clean_expired_premium")
def clean_expired_premium():
    """Очистка истёкшего премиума"""
    logger.info("Cleaning expired premium users")
    return {"status": "done"}


@celery_app.task(name="generate_daily_report")
def generate_daily_report(user_id: int):
    """Генерация ежедневного отчёта"""
    logger.info(f"Generating daily report for user {user_id}")
    return {"status": "generated", "user_id": user_id}


@celery_app.task(name="send_notification")
def send_notification(user_id: int, message: str):
    """Отправка уведомления"""
    logger.info(f"Sending notification to user {user_id}: {message}")
    return {"status": "sent", "user_id": user_id}
