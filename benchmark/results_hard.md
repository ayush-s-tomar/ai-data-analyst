# Hard benchmark results

Model: `openai/gpt-oss-120b` | Date: 2026-11-18 | Runs per question: 3

**Questions passed on every run: 19/21** | Individual runs passed: 58/63

| Dataset | Question | Runs passed | Note |
|---|---|---|---|
| sales | What percentage of total revenue comes from the West region? | 3/3 |  |
| sales | Which product has the highest average revenue per order? | 3/3 |  |
| sales | What is the total revenue in the month of March 2024? | 3/3 |  |
| sales | Which month of 2024 had the highest total revenue? | 0/3 | last line: 2024-03 with revenue 218300 |
| sales | In the region with the most orders, which product has the highest total units? | 3/3 |  |
| sales | How many orders have revenue above the overall average revenue? | 3/3 |  |
| sales | What is the average revenue per order for Tablet orders in the East region? | 3/3 |  |
| sales | What is the 90th percentile of revenue? | 3/3 |  |
| sales | How many distinct region and product combinations are there? | 3/3 |  |
| sales | What is the difference between the highest and lowest total revenue by region? | 3/3 |  |
| messy | What is the total revenue, ignoring missing values? | 3/3 |  |
| messy | How many rows have a missing revenue? | 3/3 |  |
| messy | How many rows are repeats of an earlier row (not counting the first occurrence)? | 3/3 |  |
| messy | How many unique orders are there? | 3/3 |  |
| messy | What is the average revenue after removing duplicate rows? | 3/3 |  |
| messy | What is the average discount_pct? | 3/3 |  |
| messy | How many rows have a missing region? | 3/3 |  |
| messy | What is the average customer satisfaction score? | 3/3 |  |
| messy | What is the average customer rating? | 3/3 |  |
| sales | What is the total revenue per salesperson? | 3/3 |  |
| sales | What was the revenue last year compared with this year? | 1/3 | ran code instead of refusing |
