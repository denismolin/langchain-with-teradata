---
name: customer_spending_segmentation
description: Segment customers and spending behavior from the DB_SOURCE.transactions table using transaction amount, category, merchant, and transaction date.
---

# Customer Spending Segmentation

Use this skill when the user asks for customer behavior analysis, repeat purchase patterns, category preferences, merchant concentration, or spending segmentation based on transaction history.

## Table

The main table is:

```sql
DB_SOURCE.transactions
```

## Available Columns

- `CustomerID`
- `Transaction_Amount`
- `Date_transaction`
- `Category`
- `MerchantID`

## What this skill is for

This skill supports analysis such as:

- identifying top-spending customers
- finding frequent customers
- measuring average spend per customer
- identifying each customer's favorite category
- identifying merchant concentration by customer
- separating customers into spend tiers

## Important Constraints

Because only one table is shown, do not assume access to:

- customer profile tables
- merchant attributes
- product details
- fraud labels
- account status
- refunds or reversals

All segmentation must be derived only from transaction history in `DB_SOURCE.transactions`.

## Derived Metrics

### Total customer spend
```sql
SUM(Transaction_Amount)
```
grouped by `CustomerID`

### Transaction frequency
```sql
COUNT(*)
```
grouped by `CustomerID`

### Average basket size
```sql
AVG(Transaction_Amount)
```
grouped by `CustomerID`

### Active period
Use:
- `MIN(Date_transaction)` for first transaction
- `MAX(Date_transaction)` for most recent transaction

### Favorite category
Rank categories per customer by:
- transaction count, or
- total spend

Be explicit about which definition is used.

## Recommended Segmentation Approaches

### Spend tiers
Create tiers using thresholds or quantiles, for example:
- low spend
- medium spend
- high spend

Only define thresholds if the user requests them or if you clearly state them.

### Frequency tiers
Group customers by transaction count.

### Category affinity
Find the category with the highest count or spending per customer.

### Merchant concentration
Measure whether a customer spends across many merchants or only a few.

## Query Patterns

### Top customers by transaction count
```sql
SELECT
    CustomerID,
    COUNT(*) AS transaction_count,
    SUM(Transaction_Amount) AS total_spent,
    AVG(Transaction_Amount) AS avg_transaction_amount
FROM DB_SOURCE.transactions
GROUP BY CustomerID
ORDER BY transaction_count DESC
LIMIT 20;
```

### Customer spend tiers
```sql
SELECT
    CustomerID,
    SUM(Transaction_Amount) AS total_spent,
    CASE
        WHEN SUM(Transaction_Amount) < 500 THEN 'low'
        WHEN SUM(Transaction_Amount) < 2000 THEN 'medium'
        ELSE 'high'
    END AS spend_tier
FROM DB_SOURCE.transactions
GROUP BY CustomerID
ORDER BY total_spent DESC;
```

### Favorite category per customer
```sql
WITH category_rank AS (
    SELECT
        CustomerID,
        Category,
        COUNT(*) AS category_txn_count,
        SUM(Transaction_Amount) AS category_spend,
        ROW_NUMBER() OVER (
            PARTITION BY CustomerID
            ORDER BY COUNT(*) DESC, SUM(Transaction_Amount) DESC
        ) AS rn
    FROM DB_SOURCE.transactions
    GROUP BY CustomerID, Category
)
SELECT
    CustomerID,
    Category AS favorite_category,
    category_txn_count,
    category_spend
FROM category_rank
WHERE rn = 1;
```

### Merchant diversity by customer
```sql
SELECT
    CustomerID,
    COUNT(DISTINCT MerchantID) AS distinct_merchants,
    COUNT(*) AS transaction_count,
    SUM(Transaction_Amount) AS total_spent
FROM DB_SOURCE.transactions
GROUP BY CustomerID
ORDER BY distinct_merchants DESC;
```

## Response Style

When answering:
- derive all metrics from the visible transaction table only
- clearly state whether segmentation is based on spend, count, or recency
- use window functions when ranking within customer groups
- avoid unsupported claims about churn, fraud, or customer demographics
