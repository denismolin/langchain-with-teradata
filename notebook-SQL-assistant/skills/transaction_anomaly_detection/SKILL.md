---
name: transaction_anomaly_detection
description: Detect unusual transaction patterns using aggregated Teradata SQL heuristics from DB_SOURCE.transactions. Never return raw rows.
---

# Transaction Anomaly Detection

Use this skill when the user asks about unusual patterns, outlier analysis, suspicious merchants, or abnormal customer spending.

## Table & Columns

**Table:** `DB_SOURCE.transactions`

| Column | Description |
|---|---|
| CustomerID | Customer identifier |
| Transaction_Amount | Transaction value |
| Date_transaction | Transaction date |
| Category | Spending category |
| MerchantID | Merchant identifier |

---

## Hard Rules

- **Never** return raw transaction rows or full customer lists
- **Always** aggregate results
- **Always** use `TOP N` — default `TOP 20`
- Label all findings as **potential anomalies** — no fraud labels exist in this data

---

## Query Patterns (Teradata SQL)

### Top spenders (high-spend proxy)
```sql
SELECT TOP 20
    CustomerID,
    COUNT(*) AS transaction_count,
    SUM(Transaction_Amount) AS total_spent,
    AVG(Transaction_Amount) AS avg_amount
FROM DB_SOURCE.transactions
GROUP BY CustomerID
ORDER BY total_spent DESC;
```

### Customers with unusually high average spend (3× global average)
```sql
SELECT TOP 20
    CustomerID,
    COUNT(*) AS transaction_count,
    AVG(Transaction_Amount) AS avg_amount
FROM DB_SOURCE.transactions
GROUP BY CustomerID
HAVING AVG(Transaction_Amount) > (SELECT AVG(Transaction_Amount) * 3 FROM DB_SOURCE.transactions)
ORDER BY avg_amount DESC;
```

### Merchant anomalies (high average transaction value)
```sql
SELECT TOP 20
    MerchantID,
    COUNT(*) AS transaction_count,
    SUM(Transaction_Amount) AS total_amount,
    AVG(Transaction_Amount) AS avg_amount
FROM DB_SOURCE.transactions
GROUP BY MerchantID
ORDER BY avg_amount DESC;
```

### Category anomalies
```sql
SELECT TOP 20
    Category,
    COUNT(*) AS transaction_count,
    AVG(Transaction_Amount) AS avg_amount,
    SUM(Transaction_Amount) AS total_amount
FROM DB_SOURCE.transactions
GROUP BY Category
ORDER BY avg_amount DESC;
```

### Sparse but high-value customers (≤3 transactions)
```sql
SELECT TOP 20
    CustomerID,
    COUNT(*) AS transaction_count,
    AVG(Transaction_Amount) AS avg_amount,
    SUM(Transaction_Amount) AS total_amount
FROM DB_SOURCE.transactions
GROUP BY CustomerID
HAVING COUNT(*) <= 3
ORDER BY avg_amount DESC;
```

---

## Response Style

- Describe results at the aggregated level only
- Always explain the heuristic used (e.g., "3× global average")
- Label findings as "potential anomalies" — never as confirmed fraud
