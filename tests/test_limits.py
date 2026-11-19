from limits import FREE_QUESTIONS_PER_SESSION, allowed


def test_shared_key_is_capped():
    assert allowed(0, False)
    assert allowed(FREE_QUESTIONS_PER_SESSION - 1, False)
    assert not allowed(FREE_QUESTIONS_PER_SESSION, False)


def test_own_key_is_unlimited():
    assert allowed(10_000, True)
