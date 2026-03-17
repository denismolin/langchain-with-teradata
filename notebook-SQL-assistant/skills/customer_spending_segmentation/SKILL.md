---
name: customer_spending_segmentation
description: Analyze customer spending behavior using aggregated metrics from DB_SOURCE.transactions. Only aggregated or top-N queries are allowed.
---

# Customer Spending Segmentation (Aggregated Only)

Use this skill when the user asks for customer behavior analysis, repeat purchase patterns, category preferences, merchant concentration, or spending segmentation.

## Table

```sql
DB_SOURCE.transactions
```

## Available Columns

- `CustomerID`
- `Transaction_Amount`
- `Date_transaction`
- `Category`
- `MerchantID`

---

## 🚨 CRITICAL RULES (MANDATORY)

- NEVER return raw transaction-level data
- NEVER return all customers without LIMIT
- ALWAYS aggregate BEFORE returning results
- ALWAYS include `LIMIT` or filtering
- Prefer TOP-N queries (e.g., top 20 customers)
- Default LIMIT is 20 unless specified otherwise
- If the result could exceed ~100 rows, reduce it

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
GROUP BY CustomerID
LIMIT 20;
```

---

## Allowed Analysis Types

- Top customers by spend
- Customer segmentation (tiers)
- Category or merchant aggregation
- Distribution summaries
- Aggregated KPIs

---

## Core Aggregations

### Total spend per customer
```sql
SUM(Transaction_Amount)
```

### Transaction count
```sql
COUNT(*)
```

### Average transaction
```sql
AVG(Transaction_Amount)
```

---

## Safe Query Patterns

### Top customers (MANDATORY LIMIT)
```sql
SELECT
    CustomerID,
    COUNT(*) AS transaction_count,
    SUM(Transaction_Amount) AS total_spent,
    AVG(Transaction_Amount) AS avg_transaction_amount
FROM DB_SOURCE.transactions
GROUP BY CustomerID
ORDER BY total_spent DESC
LIMIT 20;
```

---

### Spend distribution (no customer-level output)
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

### Spend tiers (aggregated)
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
            WHEN SUM(Transaction_Amount) < 500 THEN 'low'
            WHEN SUM(Transaction_Amount) < 2000 THEN 'medium'
            ELSE 'high'
        END AS spend_tier
    FROM DB_SOURCE.transactions
    GROUP BY CustomerID
) t
GROUP BY spend_tier;
```

---

### Category distribution (aggregated only)
```sql
SELECT
    Category,
    COUNT(*) AS transaction_count,
    SUM(Transaction_Amount) AS total_spent
FROM DB_SOURCE.transactions
GROUP BY Category
ORDER BY total_spent DESC
LIMIT 20;
```

---

## Response Style

- Always describe results at **aggregated level**
- Avoid listing all customers
- Prefer summaries like:
  - "Top 20 customers represent X% of spend"
  - "Most transactions occur in category Y"
- Be concise and analytical