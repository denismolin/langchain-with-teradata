---
name: transaction_anomaly_detection
description: Detect unusual transaction patterns using aggregated heuristics only from DB_SOURCE.transactions. Avoid raw transaction outputs.
---

# Transaction Anomaly Detection (Aggregated Only)

Use this skill when the user asks for unusual transaction detection, outlier analysis, suspicious merchant patterns, or abnormal customer spending.

## Table

```sql
DB_SOURCE.transactions
```

## Columns

- CustomerID
- Transaction_Amount
- Date_transaction
- Category
- MerchantID

---

## 🚨 CRITICAL RULES (MANDATORY)

- NEVER return raw transaction-level rows
- NEVER expose full transaction lists
- ALWAYS aggregate results
- ALWAYS use LIMIT when returning entities
- Default LIMIT is 20
- Focus on summaries, not individual transactions

❌ Forbidden:
```sql
SELECT * FROM DB_SOURCE.transactions;
```

❌ Forbidden:
```sql
SELECT CustomerID, Transaction_Amount FROM DB_SOURCE.transactions;
```

✅ Required:
```sql
GROUP BY ...
LIMIT 20;
```

---

## Scope & Limitations

- No fraud labels → only heuristics
- No timestamps → limited temporal precision
- No external metadata → no demographics or geography

Always describe results as:
- anomalies
- unusual patterns
- high-risk indicators

Never claim confirmed fraud.

---

## Allowed Detection Types

- High-spend customers (aggregated)
- Customers with abnormal averages
- Merchant-level anomalies
- Category-level anomalies
- Distribution outliers

---

## Core Metrics

- SUM(Transaction_Amount)
- AVG(Transaction_Amount)
- COUNT(*)
- STDDEV_SAMP(Transaction_Amount)

---

## Safe Query Patterns

### High-spend customers (proxy for anomaly)
```sql
SELECT
    CustomerID,
    COUNT(*) AS transaction_count,
    SUM(Transaction_Amount) AS total_spent,
    AVG(Transaction_Amount) AS avg_amount
FROM DB_SOURCE.transactions
GROUP BY CustomerID
ORDER BY total_spent DESC
LIMIT 20;
```

---

### Customers with unusually high average spend
```sql
SELECT
    CustomerID,
    COUNT(*) AS transaction_count,
    AVG(Transaction_Amount) AS avg_amount
FROM DB_SOURCE.transactions
GROUP BY CustomerID
HAVING AVG(Transaction_Amount) > (
    SELECT AVG(Transaction_Amount) * 3 FROM DB_SOURCE.transactions
)
ORDER BY avg_amount DESC
LIMIT 20;
```

---

### Merchant anomaly (high-value concentration)
```sql
SELECT
    MerchantID,
    COUNT(*) AS transaction_count,
    SUM(Transaction_Amount) AS total_amount,
    AVG(Transaction_Amount) AS avg_amount
FROM DB_SOURCE.transactions
GROUP BY MerchantID
ORDER BY avg_amount DESC
LIMIT 20;
```

---

### Category anomalies (high average)
```sql
SELECT
    Category,
    COUNT(*) AS transaction_count,
    AVG(Transaction_Amount) AS avg_amount,
    SUM(Transaction_Amount) AS total_amount
FROM DB_SOURCE.transactions
GROUP BY Category
ORDER BY avg_amount DESC
LIMIT 20;
```

---

### Sparse but high-value customers
```sql
SELECT
    CustomerID,
    COUNT(*) AS transaction_count,
    AVG(Transaction_Amount) AS avg_amount,
    SUM(Transaction_Amount) AS total_amount
FROM DB_SOURCE.transactions
GROUP BY CustomerID
HAVING COUNT(*) <= 3
ORDER BY avg_amount DESC
LIMIT 20;
```

---

## Response Style

- Always describe aggregated anomalies
- Avoid listing individual transactions
- Explain the heuristic used (e.g., high average, top spenders)
- Be cautious: label results as "potential anomalies"
- Be concise and analytical