---
name: transaction_analysis
description: Analyze customer transactions by amount, date, category, and merchant using the DB_SOURCE.transactions table.
---

# Transaction Analysis

Use this skill when the user asks for SQL queries or analysis involving transaction amounts, transaction dates, customer activity, category spending, or merchant-level transaction summaries.

## Table

The main table is:

```sql
DB_SOURCE.transactions
```

## Columns

### CustomerID
Identifier of the customer associated with the transaction.

### Transaction_Amount
Numeric amount of the transaction.

### Date_transaction
Transaction date.

### Category
Transaction category such as Cosmetic, Clothing, Restaurant, Market, Travel, or Electronics.

### MerchantID
Identifier of the merchant associated with the transaction.

## Assumptions and Scope

Only use columns that are explicitly present in the table:

- CustomerID
- Transaction_Amount
- Date_transaction
- Category
- MerchantID

Do not assume the existence of any of the following unless the user explicitly provides them:

- transaction_id
- transaction_status
- currency
- payment_method
- city
- country
- merchant_name
- customer demographics

## Analysis Patterns

### Customer spending
Use `SUM(Transaction_Amount)` grouped by `CustomerID`.

### Merchant volume
Use `COUNT(*)` or `SUM(Transaction_Amount)` grouped by `MerchantID`.

### Category spending
Use `SUM(Transaction_Amount)` grouped by `Category`.

### Time-based filtering
Use `Date_transaction` for filtering by day, month, quarter, year, or rolling periods.

### High-value transactions
Treat these as user-defined unless the prompt specifies a threshold. If needed, ask for or infer a threshold from the request.

## Query Guidelines

- Prefer explicit column selection over `SELECT *` unless the user asks for all fields.
- Alias aggregates clearly, for example:
  - `total_spent`
  - `transaction_count`
  - `avg_transaction_amount`
- When ranking, use `ORDER BY` with `DESC`.
- When returning top results, use `LIMIT`.
- For monthly summaries, truncate or extract from `Date_transaction` using the SQL dialect appropriate to the environment.

## Example Queries

### Top 10 customers by total spending
```sql
SELECT
    CustomerID,
    SUM(Transaction_Amount) AS total_spent
FROM DB_SOURCE.transactions
GROUP BY CustomerID
ORDER BY total_spent DESC
LIMIT 10;
```

### Total spending by category
```sql
SELECT
    Category,
    SUM(Transaction_Amount) AS total_spent,
    COUNT(*) AS transaction_count
FROM DB_SOURCE.transactions
GROUP BY Category
ORDER BY total_spent DESC;
```

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

## Response Style

When answering:
- write SQL that uses only the known columns
- mention any assumptions
- prefer robust aggregation and filtering patterns
- avoid inventing business rules that are not present in the schema
