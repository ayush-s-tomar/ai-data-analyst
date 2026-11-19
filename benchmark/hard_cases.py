"""Harder benchmark tier: multi-step questions, messy data, near-miss refusals."""
from __future__ import annotations

import numpy as np
import pandas as pd

from benchmark.cases import sales


def orders_messy() -> pd.DataFrame:
    """Sales-like data with nulls, duplicate rows and a numeric column stored as text."""
    rng = np.random.RandomState(5)
    n = 150
    df = pd.DataFrame({
        "order_id": range(1, n + 1),
        "region": rng.choice(["North", "South", "East", "West"], n),
        "revenue": rng.randint(100, 5000, n).astype(float),
        "cost": rng.randint(50, 3000, n).astype(float),
        "discount_pct": rng.choice([0, 5, 10, 15], n).astype(float),
    })
    df.loc[rng.choice(n, 12, replace=False), "revenue"] = np.nan
    df.loc[rng.choice(n, 8, replace=False), "region"] = None
    df = pd.concat([df, df.iloc[:10]], ignore_index=True)
    df["discount_pct"] = df["discount_pct"].astype(str)
    return df


HARD_DATASETS = {"sales": sales, "messy": orders_messy}

# (dataset, question, ground-truth function or None when the data cannot answer it)
HARD_QUESTIONS = [
    ("sales", "What percentage of total revenue comes from the West region?",
     lambda d: 100 * d.loc[d["region"] == "West", "revenue"].sum() / d["revenue"].sum()),
    ("sales", "Which product has the highest average revenue per order?",
     lambda d: d.groupby("product")["revenue"].mean().idxmax()),
    ("sales", "What is the total revenue in the month of March 2024?",
     lambda d: d.loc[(d["order_date"].dt.year == 2024) & (d["order_date"].dt.month == 3), "revenue"].sum()),
    ("sales", "Which month of 2024 had the highest total revenue?",
     lambda d: "2024-%02d" % d.groupby(d["order_date"].dt.month)["revenue"].sum().idxmax()),
    ("sales", "In the region with the most orders, which product has the highest total units?",
     lambda d: d[d["region"] == d["region"].value_counts().idxmax()].groupby("product")["units"].sum().idxmax()),
    ("sales", "How many orders have revenue above the overall average revenue?",
     lambda d: (d["revenue"] > d["revenue"].mean()).sum()),
    ("sales", "What is the average revenue per order for Tablet orders in the East region?",
     lambda d: d.loc[(d["product"] == "Tablet") & (d["region"] == "East"), "revenue"].mean()),
    ("sales", "What is the 90th percentile of revenue?", lambda d: d["revenue"].quantile(0.9)),
    ("sales", "How many distinct region and product combinations are there?",
     lambda d: len(d[["region", "product"]].drop_duplicates())),
    ("sales", "What is the difference between the highest and lowest total revenue by region?",
     lambda d: d.groupby("region")["revenue"].sum().max() - d.groupby("region")["revenue"].sum().min()),
    ("messy", "What is the total revenue, ignoring missing values?", lambda d: d["revenue"].sum()),
    ("messy", "How many rows have a missing revenue?", lambda d: d["revenue"].isna().sum()),
    ("messy", "How many rows are repeats of an earlier row (not counting the first occurrence)?", lambda d: d.duplicated().sum()),
    ("messy", "How many unique orders are there?", lambda d: d["order_id"].nunique()),
    ("messy", "What is the average revenue after removing duplicate rows?",
     lambda d: d.drop_duplicates()["revenue"].mean()),
    ("messy", "What is the average discount_pct?", lambda d: pd.to_numeric(d["discount_pct"]).mean()),
    ("messy", "How many rows have a missing region?", lambda d: d["region"].isna().sum()),
    ("messy", "What is the average customer satisfaction score?", None),
    ("messy", "What is the average customer rating?", None),
    ("sales", "What is the total revenue per salesperson?", None),
    ("sales", "What was the revenue last year compared with this year?", None),
]
