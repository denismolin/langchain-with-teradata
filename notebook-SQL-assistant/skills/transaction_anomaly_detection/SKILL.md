---
name: transaction_anomaly_detection
description: Detect unusual transaction patterns and simple fraud-like heuristics using only the DB_SOURCE.transactions table.
---

# Transaction Anomaly Detection

Use this skill when the user asks for unusual transaction detection, outlier analysis, suspicious merchant patterns, abnormal customer spending, or simple fraud-oriented heuristics based only on the transaction table.

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

## Scope and Limitations

This skill is limited to heuristics that can be derived from a single table.

Do not assume the existence of:
- transaction timestamps beyond the date
- chargeback labels
- fraud labels
- merchant geography
- device identifiers
- IP addresses
- customer demographics
- account status
- transaction status or reversals

Because of those limits, results should be described as:
- unusual
- anomalous
- high-risk heuristic candidates

Do not claim confirmed fraud.

## Recommended Heuristics

### Large transaction outliers
Find transactions that are unusually large compared with:
- all transactions
- the customer's own history
- the category distribution

### Customer-level spikes
Detect customers whose recent transaction amounts are far above their own average.

### Merchant concentration risk
Identify merchants with unusually high counts of large transactions.

### Category anomalies
Find transactions that are extreme within a category.

### Sparse but high-value customers
Find customers with very few transactions but very high total or average amounts.

## Query Patterns

### Global high-value outliers using percentile logic
```sql
WITH threshold AS (
    SELECT PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY Transaction_Amount) AS p99_amount
    FROM DB_SOURCE.transactions
)
SELECT
    t.CustomerID,
    t.MerchantID,
    t.Category,
    t.Date_transaction,
    t.Transaction_Amount
FROM DB_SOURCE.transactions t
CROSS JOIN threshold th
WHERE t.Transaction_Amount >= th.p99_amount
ORDER BY t.Transaction_Amount DESC;
```

### Transactions far above each customer's average
```sql
WITH customer_stats AS (
    SELECT
        CustomerID,
        AVG(Transaction_Amount) AS avg_amount,
        STDDEV_SAMP(Transaction_Amount) AS std_amount
    FROM DB_SOURCE.transactions
    GROUP BY CustomerID
)
SELECT
    t.CustomerID,
    t.MerchantID,
    t.Category,
    t.Date_transaction,
    t.Transaction_Amount,
    cs.avg_amount,
    cs.std_amount
FROM DB_SOURCE.transactions t
JOIN customer_stats cs
    ON t.CustomerID = cs.CustomerID
WHERE t.Transaction_Amount > cs.avg_amount + 3 * COALESCE(cs.std_amount, 0)
ORDER BY t.Transaction_Amount DESC;
```

### Merchant-level concentration of high-value transactions
```sql
SELECT
    MerchantID,
    COUNT(*) AS transaction_count,
    SUM(Transaction_Amount) AS total_amount,
    AVG(Transaction_Amount) AS avg_amount,
    SUM(CASE WHEN Transaction_Amount >= 1000 THEN 1 ELSE 0 END) AS high_value_txn_count
FROM DB_SOURCE.transactions
GROUP BY MerchantID
ORDER BY high_value_txn_count DESC, total_amount DESC;
```

### Category-based outliers
```sql
WITH category_stats AS (
    SELECT
        Category,
        AVG(Transaction_Amount) AS avg_amount,
        STDDEV_SAMP(Transaction_Amount) AS std_amount
    FROM DB_SOURCE.transactions
    GROUP BY Category
)
SELECT
    t.CustomerID,
    t.MerchantID,
    t.Category,
    t.Date_transaction,
    t.Transaction_Amount
FROM DB_SOURCE.transactions t
JOIN category_stats cs
    ON t.Category = cs.Category
WHERE t.Transaction_Amount > cs.avg_amount + 3 * COALESCE(cs.std_amount, 0)
ORDER BY t.Category, t.Transaction_Amount DESC;
```

### Customers with few transactions but high average spend
```sql
SELECT
    CustomerID,
    COUNT(*) AS transaction_count,
    SUM(Transaction_Amount) AS total_amount,
    AVG(Transaction_Amount) AS avg_amount
FROM DB_SOURCE.transactions
GROUP BY CustomerID
HAVING COUNT(*) <= 3
ORDER BY avg_amount DESC, total_amount DESC;
```

## Response Style

When answering:
- label findings as anomaly detection heuristics, not confirmed fraud
- explain the baseline used for comparison
- prefer percentile, z-score, or customer-relative comparisons
- note when SQL functions may vary by dialect
- avoid overclaiming due to the limited schema
