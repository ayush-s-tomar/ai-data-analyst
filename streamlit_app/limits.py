"""Usage limits for the shared demo key."""
FREE_QUESTIONS_PER_SESSION = 15


def allowed(asked: int, using_own_key: bool, limit: int = FREE_QUESTIONS_PER_SESSION) -> bool:
    """Visitors with their own key are unlimited; the shared key gets a per-session cap."""
    return using_own_key or asked < limit
