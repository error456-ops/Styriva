from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from accounts.models import UserUsage


# ==========================================================
# STYRIVA ABUSE PROTECTION
# ==========================================================


# ==========================================================
# CONSTANTS
# ==========================================================

REQUEST_LIMIT = 5
WINDOW_SECONDS = 60
DAILY_AI_LIMIT = 2


# ==========================================================
# RATE LIMITER
# ==========================================================

def get_rate_limit_key(request):
    """
    Creates a temporary rate-limit key for this browser session.
    """

    if not request.session.session_key:
        request.session.create()

    return f"styriva:ai_rate:{request.session.session_key}"


def is_rate_limited(request):
    """
    Returns True when this session has exceeded
    the allowed number of protected requests.
    """

    key = get_rate_limit_key(request)

    request_count = cache.get(key, 0)

    if request_count >= REQUEST_LIMIT:
        return True

    cache.set(
        key,
        request_count + 1,
        timeout=WINDOW_SECONDS,
    )

    return False


# ==========================================================
# DAILY AI USE
# ==========================================================

@transaction.atomic
def reserve_daily_ai_use(user):
    """
    Atomically reserves one AI use for an authenticated user.

    Returns:
        (True, None) when the user has an available AI use.
        (False, reason) when the daily limit has been reached.
    """

    usage, created = UserUsage.objects.select_for_update().get_or_create(
        user=user
    )

    today = timezone.localdate()

    # ------------------------------------------------------
    # New day → reset counter
    # ------------------------------------------------------

    if usage.last_generation_date != today:

        usage.daily_generations = 0
        usage.last_generation_date = today

    # ------------------------------------------------------
    # Daily limit
    # ------------------------------------------------------

    if usage.daily_generations >= DAILY_AI_LIMIT:

        # Save date reset if necessary.
        if usage.last_generation_date != today:
            usage.save(
                update_fields=[
                    "daily_generations",
                    "last_generation_date",
                ]
            )

        return (
            False,
            "You've used today's 2 free AI uses. "
            "Come back tomorrow for 2 more."
        )

    # ------------------------------------------------------
    # Reserve one AI use immediately.
    # ------------------------------------------------------

    usage.daily_generations += 1

    usage.last_generation_date = today

    usage.save(
        update_fields=[
            "daily_generations",
            "last_generation_date",
        ]
    )

    return True, None


@transaction.atomic
def release_daily_ai_use(user):
    """
    Returns one reserved AI use when job creation fails.
    """

    usage = UserUsage.objects.select_for_update().get(
        user=user
    )

    today = timezone.localdate()

    if usage.last_generation_date != today:
        return

    if usage.daily_generations > 0:
        usage.daily_generations -= 1

        usage.save(
            update_fields=[
                "daily_generations",
            ]
        )
        
        
# ==========================================================
# FINAL JOB SAFETY CHECK
# ==========================================================

