import os
from posthog import Posthog

POSTHOG_API_KEY = os.getenv("POSTHOG_API_KEY", "").strip()
POSTHOG_HOST = os.getenv("POSTHOG_HOST", "https://us.i.posthog.com")

if POSTHOG_API_KEY:
    client = Posthog(POSTHOG_API_KEY, host=POSTHOG_HOST)
    print(f"✅ PostHog клиент создан, ключ: {POSTHOG_API_KEY[:10]}...")
else:
    client = None
    print("⚠️ POSTHOG_API_KEY не найден")

def identify_user(user_id, properties=None):
    if not client:
        return
    client.identify(distinct_id=str(user_id), properties=properties or {})

def capture_event(user_id, event_name, properties=None):
    print(f"📤 capture_event вызван: {event_name} | user: {user_id}")
    if not client:
        print(f"❌ PostHog клиент не создан")
        return
    try:
        client.capture(distinct_id=str(user_id), event=event_name, properties=properties or {})
        print(f"✅ Событие отправлено: {event_name}")
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")

def capture_error(user_id, error_name, properties=None):
    capture_event(user_id, "error_occurred", properties or {"error": error_name})
