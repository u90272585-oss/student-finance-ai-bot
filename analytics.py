import os
from posthog import Posthog

POSTHOG_API_KEY = os.getenv("POSTHOG_API_KEY", "").strip()
POSTHOG_HOST = os.getenv("POSTHOG_HOST", "https://us.i.posthog.com")

if POSTHOG_API_KEY:
    client = Posthog(POSTHOG_API_KEY, host=POSTHOG_HOST)
else:
    client = None


def identify_user(user_id, properties=None):
    """Устанавливает person-свойства пользователя (замена старого identify())."""
    if not client:
        return
    client.set(distinct_id=str(user_id), properties=properties or {})


def capture_event(user_id, event_name, properties=None):
    if not client:
        return
    client.capture(distinct_id=str(user_id), event=event_name, properties=properties or {})


def capture_error(user_id, error_name, properties=None):
    capture_event(user_id, "error_occurred", properties or {"error": error_name})