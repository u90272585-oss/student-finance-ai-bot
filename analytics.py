import os
import posthog

POSTHOG_API_KEY = os.getenv("POSTHOG_API_KEY", "").strip()
POSTHOG_HOST = os.getenv("POSTHOG_HOST", "https://us.i.posthog.com")

if POSTHOG_API_KEY:
    print(f"✅ PostHog инициализирован, ключ: {POSTHOG_API_KEY[:10]}...")
else:
    print("⚠️ POSTHOG_API_KEY не найден")

def identify_user(user_id, properties=None):
    if not POSTHOG_API_KEY:
        return
    posthog.identify(
        distinct_id=str(user_id),
        properties=properties or {},
        api_key=POSTHOG_API_KEY,
        host=POSTHOG_HOST
    )

def capture_event(user_id, event_name, properties=None):
    if not POSTHOG_API_KEY:
        print(f"❌ Ключ пустой, событие {event_name} не отправлено")
        return
    posthog.capture(
        distinct_id=str(user_id),
        event=event_name,
        properties=properties or {},
        api_key=POSTHOG_API_KEY,
        host=POSTHOG_HOST
    )
POSTHOG_API_KEY = os.getenv("POSTHOG_API_KEY", "").strip()
print(f"DEBUG POSTHOG KEY: '{POSTHOG_API_KEY}'")
print(f"DEBUG KEY LENGTH: {len(POSTHOG_API_KEY)}")

def capture_error(user_id, error_name, properties=None):
    capture_event(user_id, "error_occurred", properties or {"error": error_name})