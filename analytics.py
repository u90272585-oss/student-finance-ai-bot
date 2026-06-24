import os
import posthog
from datetime import datetime

# Инициализация PostHog
POSTHOG_API_KEY = os.getenv("POSTHOG_API_KEY")
POSTHOG_HOST = os.getenv("POSTHOG_HOST", "https://us.i.posthog.com")

if POSTHOG_API_KEY:
    posthog.project_api_key = POSTHOG_API_KEY
    posthog.host = POSTHOG_HOST
    print("✅ PostHog инициализирован")
else:
    print("⚠️ POSTHOG_API_KEY не найден. Аналитика не будет работать.")


def identify_user(user_id, properties=None):
    """Идентификация пользователя в PostHog"""
    if not POSTHOG_API_KEY:
        return
    props = properties or {}
    posthog.identify(
        distinct_id=str(user_id),
        properties=props
    )


def capture_event(user_id, event_name, properties=None):
    """Отправка события в PostHog"""
    if not POSTHOG_API_KEY:
        return
    props = properties or {}
    posthog.capture(
        distinct_id=str(user_id),
        event=event_name,
        properties=props
    )


def capture_error(user_id, error_name, properties=None):
    """Отправка ошибки в PostHog"""
    if not POSTHOG_API_KEY:
        return
    props = properties or {"error": error_name}
    capture_event(user_id, "error_occurred", props)