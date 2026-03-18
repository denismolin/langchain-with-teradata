---
name: transaction_analysis
description: Analyze transactions using aggregated Teradata SQL queries from DB_SOURCE.transactions. Never return raw rows. Always aggregate and limit results.
---

# Transaction Analysis

Use this skill when the user asks for SQL analysis involving transaction amounts, dates, customer activity, category spending, or merchant summaries.

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

- **Never** use `SELECT *` or return raw transaction rows
- **Always** aggregate before returning results
- **Always** use `TOP N` (Teradata syntax) on entity-level queries — default `TOP 20`
- If a result set could exceed ~100 rows, aggregate further or add a filter

---

## Query Patterns (Teradata SQL)

### Top customers by spend
```sql
SELECT TOP 20
    CustomerID,
    SUM(Transaction_Amount) AS total_spent,
    COUNT(*) AS transaction_count
FROM DB_SOURCE.transactions
GROUP BY CustomerID
ORDER BY total_spent DESC;
```

### Category spending summary
```sql
SELECT TOP 20
    Category,
    SUM(Transaction_Amount) AS total_spent,
    COUNT(*) AS transaction_count
FROM DB_SOURCE.transactions
GROUP BY Category
ORDER BY total_spent DESC;
```

### Top merchants by revenue
```sql
SELECT TOP 20
    MerchantID,
    SUM(Transaction_Amount) AS total_amount,
    COUNT(*) AS transaction_count
FROM DB_SOURCE.transactions
GROUP BY MerchantID
ORDER BY total_amount DESC;
```

### Monthly summary
```sql
SELECT
    TRUNC(Date_transaction, 'MM') AS month,
    SUM(Transaction_Amount) AS total_amount,
    COUNT(*) AS transaction_count
FROM DB_SOURCE.transactions
GROUP BY TRUNC(Date_transaction, 'MM')
ORDER BY month;
```

### Global summary
```sql
SELECT
    COUNT(*) AS total_transactions,
    SUM(Transaction_Amount) AS total_volume,
    AVG(Transaction_Amount) AS avg_transaction,
    MIN(Transaction_Amount) AS min_transaction,
    MAX(Transaction_Amount) AS max_transaction
FROM DB_SOURCE.transactions;
```

---

## Response Style

- Return aggregated insights only — no raw rows
- Be concise and explicit about any assumptions made
