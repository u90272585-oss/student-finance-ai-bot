import os
import posthog

POSTHOG_API_KEY = os.getenv("POSTHOG_API_KEY", "").strip()
POSTHOG_HOST = os.getenv("POSTHOG_HOST", "https://us.i.posthog.com")

if POSTHOG_API_KEY:
    posthog.project_api_key = POSTHOG_API_KEY
    posthog.host = POSTHOG_HOST
    print(f"✅ PostHog инициализирован (host: {POSTHOG_HOST})")
else:
    print("⚠️ POSTHOG_API_KEY не найден — аналитика отключена")

def identify_user(user_id, properties=None):
    if not POSTHOG_API_KEY:
        return
    posthog.identify(distinct_id=str(user_id), properties=properties or {})

def capture_event(user_id, event_name, properties=None):
    print(f"📤 Событие: {event_name} | user: {user_id}")
    if not POSTHOG_API_KEY:
        print("❌ POSTHOG_API_KEY пустой — событие не отправлено")
        return
    posthog.capture(distinct_id=str(user_id), event=event_name, properties=properties or {})

def capture_error(user_id, error_name, properties=None):
    capture_event(user_id, "error_occurred", properties or {"error": error_name})