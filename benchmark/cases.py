"""Datasets and known-answer questions for the accuracy benchmark.

Ground truth is computed from the DataFrame with plain pandas, never typed by hand.
"""
from __future__ import annotations

import math
import re

import numpy as np
import pandas as pd


def sales() -> pd.DataFrame:
    rng = np.random.RandomState(42)
    n = 200
    df = pd.DataFrame({
        "order_id": range(1, n + 1),
        "region": rng.choice(["North", "South", "East", "West"], n),
        "product": rng.choice(["Laptop", "Phone", "Tablet", "Monitor"], n),
        "units": rng.randint(1, 20, n),
        "unit_price": rng.choice([300, 500, 800, 1200], n),
        "order_date": pd.date_range("2024-01-01", periods=n, freq="D"),
    })
    df["revenue"] = df["units"] * df["unit_price"]
    return df


def hr() -> pd.DataFrame:
    rng = np.random.RandomState(7)
    n = 120
    return pd.DataFrame({
        "employee_id": range(1, n + 1),
        "department": rng.choice(["Engineering", "Sales", "HR", "Finance"], n),
        "salary": rng.randint(30000, 150000, n),
        "years_experience": rng.randint(0, 21, n),
        "rating": rng.randint(1, 6, n),
    })


def students() -> pd.DataFrame:
    rng = np.random.RandomState(11)
    n = 150
    return pd.DataFrame({
        "student_id": range(1, n + 1),
        "class": rng.choice(["A", "B", "C"], n),
        "math": rng.randint(35, 101, n),
        "science": rng.randint(35, 101, n),
        "attendance": rng.randint(55, 101, n),
    })


DATASETS = {"sales": sales, "hr": hr, "students": students}

# (dataset, question, ground-truth function or None when the data cannot answer it)
QUESTIONS = [
    ("sales", "What is the total revenue?", lambda d: d["revenue"].sum()),
    ("sales", "Which region has the highest total revenue?", lambda d: d.groupby("region")["revenue"].sum().idxmax()),
    ("sales", "What is the average units per order?", lambda d: d["units"].mean()),
    ("sales", "How many orders were for Laptop?", lambda d: (d["product"] == "Laptop").sum()),
    ("sales", "What is the largest revenue from a single order?", lambda d: d["revenue"].max()),
    ("sales", "Which product sold the most units in total?", lambda d: d.groupby("product")["units"].sum().idxmax()),
    ("sales", "What is the total revenue for the West region?", lambda d: d.loc[d["region"] == "West", "revenue"].sum()),
    ("sales", "How many distinct products are there?", lambda d: d["product"].nunique()),
    ("sales", "What is the median revenue per order?", lambda d: d["revenue"].median()),
    ("sales", "What is the average customer age?", None),
    ("hr", "What is the average salary?", lambda d: d["salary"].mean()),
    ("hr", "Which department has the highest average salary?", lambda d: d.groupby("department")["salary"].mean().idxmax()),
    ("hr", "How many employees have a rating of 4 or higher?", lambda d: (d["rating"] >= 4).sum()),
    ("hr", "What is the maximum years_experience?", lambda d: d["years_experience"].max()),
    ("hr", "What is the total salary of the Engineering department?", lambda d: d.loc[d["department"] == "Engineering", "salary"].sum()),
    ("hr", "How many employees are there in total?", lambda d: len(d)),
    ("hr", "What is the correlation between salary and years_experience?", lambda d: d["salary"].corr(d["years_experience"])),
    ("hr", "Which department has the most employees?", lambda d: d["department"].value_counts().idxmax()),
    ("hr", "What is the standard deviation of salary?", lambda d: d["salary"].std()),
    ("hr", "What is the average bonus?", None),
    ("students", "What is the average math score?", lambda d: d["math"].mean()),
    ("students", "Which class has the highest average science score?", lambda d: d.groupby("class")["science"].mean().idxmax()),
    ("students", "How many students have attendance below 75?", lambda d: (d["attendance"] < 75).sum()),
    ("students", "What is the highest math score?", lambda d: d["math"].max()),
    ("students", "What is the average attendance?", lambda d: d["attendance"].mean()),
    ("students", "How many students are there?", lambda d: len(d)),
    ("students", "What is the correlation between math and science?", lambda d: d["math"].corr(d["science"])),
    ("students", "What is the median science score?", lambda d: d["science"].median()),
    ("students", "How many students are in class A?", lambda d: (d["class"] == "A").sum()),
    ("students", "What is the average age of the students?", None),
]

_NUMBER = re.compile(r"-?\d[\d,]*\.?\d*")


def ground_truth(fn, df):
    """Return the expected answer as float or str, or None for an unanswerable question."""
    if fn is None:
        return None
    value = fn(df)
    if isinstance(value, (np.integer, np.floating, int, float)):
        return float(value)
    return str(value)


def numbers_in(text: str) -> list:
    found = []
    for raw in _NUMBER.findall(text or ""):
        try:
            found.append(float(raw.replace(",", "")))
        except ValueError:
            continue
    return found


def matches(expected, output: str) -> bool:
    """Numbers: any printed number within 1% (or 0.01). Strings: case-insensitive substring."""
    if isinstance(expected, str):
        return expected.lower() in (output or "").lower()
    return any(math.isclose(n, expected, rel_tol=0.01, abs_tol=0.01) for n in numbers_in(output))
