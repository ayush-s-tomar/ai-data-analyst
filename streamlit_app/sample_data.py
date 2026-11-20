"""Small built-in dataset so the app can be tried without uploading anything."""
import numpy as np
import pandas as pd


def sample_sales() -> pd.DataFrame:
    rng = np.random.RandomState(2024)
    n = 120
    df = pd.DataFrame({
        "order_date": pd.date_range("2024-01-01", periods=n, freq="D"),
        "region": rng.choice(["North", "South", "East", "West"], n),
        "product": rng.choice(["Laptop", "Phone", "Tablet", "Monitor"], n),
        "units": rng.randint(1, 15, n),
        "unit_price": rng.choice([300, 500, 800, 1200], n),
    })
    df["revenue"] = df["units"] * df["unit_price"]
    return df
