from sample_data import sample_sales


def test_sample_is_deterministic_and_consistent():
    a, b = sample_sales(), sample_sales()
    assert a.equals(b) and a.shape == (120, 6)
    assert (a["revenue"] == a["units"] * a["unit_price"]).all()
    assert a.isna().sum().sum() == 0
