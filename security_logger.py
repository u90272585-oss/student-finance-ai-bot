# security_logger.py
import logging
from datetime import datetime
from typing import Optional
import json

# Настройка логгера для безопасности
security_logger = logging.getLogger("security")
security_logger.setLevel(logging.INFO)

# Создаём обработчик для вывода в файл и консоль
file_handler = logging.FileHandler("security.log")
file_handler.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Формат логов
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

security_logger.addHandler(file_handler)
security_logger.addHandler(console_handler)


def log_security_event(event_type: str, user_id: Optional[int], ip: str, details: dict = None):
    """Логирование событий безопасности"""
    log_entry = {
        "event_type": event_type,
        "user_id": user_id,
        "ip": ip,
        "timestamp": datetime.now().isoformat(),
        "details": details or {}
    }
    
    if event_type in ["FAILED_LOGIN", "BRUTE_FORCE", "SUSPICIOUS_ACTIVITY"]:
        security_logger.warning(json.dumps(log_entry, ensure_ascii=False))
    else:
        security_logger.info(json.dumps(log_entry, ensure_ascii=False))


def log_failed_login(user_id: Optional[int], ip: str, reason: str = "wrong_password"):
    """Логирование неудачной попытки входа"""
    log_security_event("FAILED_LOGIN", user_id, ip, {"reason": reason})


def log_successful_login(user_id: int, ip: str):
    """Логирование успешного входа"""
    log_security_event("SUCCESSFUL_LOGIN", user_id, ip)


def log_admin_access(user_id: int, ip: str, endpoint: str, allowed: bool):
    """Логирование доступа к админке"""
    event = "ADMIN_ACCESS_GRANTED" if allowed else "ADMIN_ACCESS_DENIED"
    log_security_event(event, user_id, ip, {"endpoint": endpoint})


def log_sql_injection_attempt(ip: str, malicious_input: str):
    """Логирование попытки SQL инъекции"""
    log_security_event("SQL_INJECTION_ATTEMPT", None, ip, {"input": malicious_input[:200]})


def log_captcha_failure(ip: str, score: float):
    """Логирование проваленной CAPTCHA"""
    log_security_event("CAPTCHA_FAILED", None, ip, {"score": score})