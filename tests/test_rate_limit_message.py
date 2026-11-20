from analyst import rate_limit_message, retry_hint

DAILY = ("Rate limit reached on tokens per day (TPD): Limit 200000, Used 199567. "
         "Please try again in 8m14.64s. Need more tokens?")


def test_retry_hint_is_extracted():
    assert retry_hint(DAILY) == "8m14.64s"
    assert retry_hint("nothing useful") == ""


def test_daily_quota_message_mentions_wait_time():
    text = rate_limit_message(DAILY)
    assert "daily" in text and "8m14.64s" in text


def test_generic_rate_limit_message():
    assert "wait a minute" in rate_limit_message("slow down")
