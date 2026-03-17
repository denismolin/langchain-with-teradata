---
name: transaction_analysis
description: Analyze transactions using aggregated queries only from DB_SOURCE.transactions. Avoid raw data outputs and always use limits.
---

# Transaction Analysis (Aggregated Only)

Use this skill when the user asks for SQL queries or analysis involving transaction amounts, transaction dates, customer activity, category spending, or merchant-level summaries.

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

- NEVER return raw transaction-level data
- NEVER use SELECT *
- ALWAYS aggregate results before returning
- ALWAYS use LIMIT when returning entity-level results (customers, merchants, categories)
- Default LIMIT is 20 unless specified otherwise
- If result could exceed ~100 rows → reduce or aggregate further

❌ Forbidden:
```sql
SELECT * FROM DB_SOURCE.transactions;
```

❌ Forbidden:
```sql
SELECT CustomerID FROM DB_SOURCE.transactions;
```

✅ Required pattern:
```sql
GROUP BY ...
LIMIT 20;
```

---

## Scope & Assumptions

Only use these columns:

- CustomerID
- Transaction_Amount
- Date_transaction
- Category
- MerchantID

Do NOT assume:
- transaction_id
- status, currency, payment method
- location or demographics
- merchant metadata

---

## Allowed Analysis Types

- Customer-level aggregated spending
- Category-level summaries
- Merchant-level summaries
- Time-based aggregations (daily, monthly, yearly)
- Distribution metrics

---

## Core Aggregations

- Total spend → SUM(Transaction_Amount)
- Transaction count → COUNT(*)
- Average transaction → AVG(Transaction_Amount)
- Min / Max → MIN(), MAX()

---

## Safe Query Patterns

### Top customers by spending
```sql
SELECT
    CustomerID,
    SUM(Transaction_Amount) AS total_spent,
    COUNT(*) AS transaction_count
FROM DB_SOURCE.transactions
GROUP BY CustomerID
ORDER BY total_spent DESC
LIMIT 20;
```

---

### Category spending summary
```sql
SELECT
    Category,
    SUM(Transaction_Amount) AS total_spent,
    COUNT(*) AS transaction_count
FROM DB_SOURCE.transactions
GROUP BY Category
ORDER BY total_spent DESC
LIMIT 20;
```

---

### Top merchants by revenue
```sql
SELECT
    MerchantID,
    SUM(Transaction_Amount) AS total_amount,
    COUNT(*) AS transaction_count
FROM DB_SOURCE.transactions
GROUP BY MerchantID
ORDER BY total_amount DESC
LIMIT 20;
```

---

### Monthly transaction summary
```sql
SELECT
    DATE_TRUNC('month', Date_transaction) AS month,
    SUM(Transaction_Amount) AS total_amount,
    COUNT(*) AS transaction_count
FROM DB_SOURCE.transactions
GROUP BY DATE_TRUNC('month', Date_transaction)
ORDER BY month;
```

---

### Global summary (no entity-level output)
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

- Always return aggregated insights
- Avoid listing raw rows
- Prefer summaries such as:
  - "Top 20 customers represent X% of total spend"
  - "Category X accounts for the largest share"
- Be concise, analytical, and explicit about assumptions