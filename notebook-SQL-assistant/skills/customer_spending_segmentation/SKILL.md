---
name: customer_spending_segmentation
description: Analyze customer spending behavior using aggregated Teradata SQL from DB_SOURCE.transactions. Only aggregated or top-N queries allowed.
---

# Customer Spending Segmentation

Use this skill when the user asks about customer behavior, repeat purchases, category preferences, merchant concentration, or spending tiers.

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
- **Always** aggregate before returning results
- **Always** use `TOP N` — default `TOP 20`
- If a result could exceed ~100 rows, reduce or aggregate further

---

## Query Patterns (Teradata SQL)

### Top customers by spend
```sql
SELECT TOP 20
    CustomerID,
    COUNT(*) AS transaction_count,
    SUM(Transaction_Amount) AS total_spent,
    AVG(Transaction_Amount) AS avg_transaction_amount
FROM DB_SOURCE.transactions
GROUP BY CustomerID
ORDER BY total_spent DESC;
```

### Global spend distribution (no customer-level output)
```sql
SELECT
    COUNT(*) AS total_transactions,
    SUM(Transaction_Amount) AS total_volume,
    AVG(Transaction_Amount) AS avg_transaction,
    MIN(Transaction_Amount) AS min_transaction,
    MAX(Transaction_Amount) AS max_transaction
FROM DB_SOURCE.transactions;
```

### Spend tier distribution
```sql
SELECT
    spend_tier,
    COUNT(*) AS num_customers,
    AVG(total_spent) AS avg_spend
FROM (
    SELECT
        CustomerID,
        SUM(Transaction_Amount) AS total_spent,
        CASE
            WHEN SUM(Transaction_Amount) < 500  THEN 'low'
            WHEN SUM(Transaction_Amount) < 2000 THEN 'medium'
            ELSE 'high'
        END AS spend_tier
    FROM DB_SOURCE.transactions
    GROUP BY CustomerID
) t
GROUP BY spend_tier;
```

### Category distribution
```sql
SELECT TOP 20
    Category,
    COUNT(*) AS transaction_count,
    SUM(Transaction_Amount) AS total_spent
FROM DB_SOURCE.transactions
GROUP BY Category
ORDER BY total_spent DESC;
```

---

## Response Style

- Summarize at the aggregated level — no raw customer lists
- Prefer statements like "Top 20 customers represent X% of spend"
- Be concise and analytical
