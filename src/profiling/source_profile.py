from sqlalchemy import text

from src.generator.utils import create_database_engine


def print_section(title: str):
    """Print a readable section heading."""
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def run_query(connection, query: str):
    """Execute a query and return all rows."""
    return connection.execute(text(query)).fetchall()


def profile_row_counts(connection):
    print_section("ROW COUNTS")

    query = """
        SELECT 'categories' AS table_name, COUNT(*) AS row_count
        FROM categories

        UNION ALL

        SELECT 'customers', COUNT(*)
        FROM customers

        UNION ALL

        SELECT 'products', COUNT(*)
        FROM products

        UNION ALL

        SELECT 'orders', COUNT(*)
        FROM orders

        UNION ALL

        SELECT 'order_items', COUNT(*)
        FROM order_items

        UNION ALL

        SELECT 'payments', COUNT(*)
        FROM payments

        UNION ALL

        SELECT 'returns', COUNT(*)
        FROM returns

        ORDER BY table_name;
    """

    for row in run_query(connection, query):
        print(f"{row[0]:<20} {row[1]:>10,}")


def profile_customers(connection):
    print_section("CUSTOMER DATA QUALITY")

    queries = {
        "Total customers": """
            SELECT COUNT(*)
            FROM customers
        """,

        "Missing emails": """
            SELECT COUNT(*)
            FROM customers
            WHERE email IS NULL
        """,

        "Missing phones": """
            SELECT COUNT(*)
            FROM customers
            WHERE phone IS NULL
        """,

        "Duplicate emails": """
            SELECT COUNT(*)
            FROM (
                SELECT email
                FROM customers
                WHERE email IS NOT NULL
                GROUP BY email
                HAVING COUNT(*) > 1
            ) duplicates
        """,

        "Inactive customers": """
            SELECT COUNT(*)
            FROM customers
            WHERE customer_status = 'INACTIVE'
        """,
    }

    for label, query in queries.items():
        result = run_query(connection, query)[0][0]
        print(f"{label:<30} {result:>10,}")


def profile_orders(connection):
    print_section("ORDER DATA QUALITY")

    queries = {
        "Total orders": """
            SELECT COUNT(*)
            FROM orders
        """,

        "Orders without customer": """
            SELECT COUNT(*)
            FROM orders
            WHERE customer_id IS NULL
        """,

        "Updated orders": """
            SELECT COUNT(*)
            FROM orders
            WHERE updated_at > created_at
        """,

        "Cancelled orders": """
            SELECT COUNT(*)
            FROM orders
            WHERE order_status = 'CANCELLED'
        """,
    }

    for label, query in queries.items():
        result = run_query(connection, query)[0][0]
        print(f"{label:<30} {result:>10,}")


def profile_order_items(connection):
    print_section("ORDER ITEM DATA QUALITY")

    queries = {
        "Total order items": """
            SELECT COUNT(*)
            FROM order_items
        """,

        "Invalid quantities": """
            SELECT COUNT(*)
            FROM order_items
            WHERE quantity <= 0
        """,

        "Orders with items": """
            SELECT COUNT(DISTINCT order_id)
            FROM order_items
        """,

        "Distinct products sold": """
            SELECT COUNT(DISTINCT product_id)
            FROM order_items
        """,
    }

    for label, query in queries.items():
        result = run_query(connection, query)[0][0]
        print(f"{label:<30} {result:>10,}")


def profile_payments(connection):
    print_section("PAYMENT DATA QUALITY")

    queries = {
        "Total payments": """
            SELECT COUNT(*)
            FROM payments
        """,

        "Missing transaction references": """
            SELECT COUNT(*)
            FROM payments
            WHERE transaction_reference IS NULL
        """,

        "Successful payments": """
            SELECT COUNT(*)
            FROM payments
            WHERE payment_status = 'SUCCESS'
        """,

        "Failed payments": """
            SELECT COUNT(*)
            FROM payments
            WHERE payment_status = 'FAILED'
        """,

        "Orders without payment": """
            SELECT COUNT(*)
            FROM orders o
            LEFT JOIN payments p
                ON o.order_id = p.order_id
            WHERE p.payment_id IS NULL
        """,

        "Payment amount mismatches": """
            SELECT COUNT(*)
            FROM payments p
            JOIN orders o
                ON p.order_id = o.order_id
            WHERE p.amount <> o.total_amount
        """,
    }

    for label, query in queries.items():
        result = run_query(connection, query)[0][0]
        print(f"{label:<35} {result:>10,}")


def profile_returns(connection):
    print_section("RETURN DATA QUALITY")

    queries = {
        "Total returns": """
            SELECT COUNT(*)
            FROM returns
        """,

        "Completed returns": """
            SELECT COUNT(*)
            FROM returns
            WHERE return_status = 'COMPLETED'
        """,

        "Invalid return quantities": """
            SELECT COUNT(*)
            FROM returns r
            JOIN order_items oi
                ON r.order_item_id = oi.order_item_id
            WHERE r.quantity <= 0
               OR r.quantity > oi.quantity
        """,

        "Total refund amount": """
            SELECT COALESCE(SUM(refund_amount), 0)
            FROM returns
        """,
    }

    for label, query in queries.items():
        result = run_query(connection, query)[0][0]
        print(f"{label:<35} {result:>10,}")


def profile_referential_integrity(connection):
    print_section("REFERENTIAL INTEGRITY")

    queries = {
        "Orders with invalid customer": """
            SELECT COUNT(*)
            FROM orders o
            LEFT JOIN customers c
                ON o.customer_id = c.customer_id
            WHERE o.customer_id IS NOT NULL
              AND c.customer_id IS NULL
        """,

        "Order items with invalid order": """
            SELECT COUNT(*)
            FROM order_items oi
            LEFT JOIN orders o
                ON oi.order_id = o.order_id
            WHERE o.order_id IS NULL
        """,

        "Order items with invalid product": """
            SELECT COUNT(*)
            FROM order_items oi
            LEFT JOIN products p
                ON oi.product_id = p.product_id
            WHERE p.product_id IS NULL
        """,

        "Payments with invalid order": """
            SELECT COUNT(*)
            FROM payments p
            LEFT JOIN orders o
                ON p.order_id = o.order_id
            WHERE o.order_id IS NULL
        """,

        "Returns with invalid order item": """
            SELECT COUNT(*)
            FROM returns r
            LEFT JOIN order_items oi
                ON r.order_item_id = oi.order_item_id
            WHERE oi.order_item_id IS NULL
        """,
    }

    for label, query in queries.items():
        result = run_query(connection, query)[0][0]
        print(f"{label:<40} {result:>10,}")


def profile_date_ranges(connection):
    print_section("DATE RANGES")

    queries = {
        "Customer earliest created": """
            SELECT MIN(created_at)
            FROM customers
        """,

        "Customer latest created": """
            SELECT MAX(created_at)
            FROM customers
        """,

        "Order earliest date": """
            SELECT MIN(order_date)
            FROM orders
        """,

        "Order latest date": """
            SELECT MAX(order_date)
            FROM orders
        """,

        "Payment earliest date": """
            SELECT MIN(payment_date)
            FROM payments
        """,

        "Payment latest date": """
            SELECT MAX(payment_date)
            FROM payments
        """,

        "Return earliest date": """
            SELECT MIN(return_date)
            FROM returns
        """,

        "Return latest date": """
            SELECT MAX(return_date)
            FROM returns
        """,
    }

    for label, query in queries.items():
        result = run_query(connection, query)[0][0]
        print(f"{label:<35} {result}")


def profile_status_distributions(connection):
    print_section("STATUS DISTRIBUTIONS")

    print("\nOrders:")

    query = """
        SELECT order_status, COUNT(*)
        FROM orders
        GROUP BY order_status
        ORDER BY COUNT(*) DESC
    """

    for row in run_query(connection, query):
        print(f"  {row[0]:<20} {row[1]:>10,}")

    print("\nPayments:")

    query = """
        SELECT payment_status, COUNT(*)
        FROM payments
        GROUP BY payment_status
        ORDER BY COUNT(*) DESC
    """

    for row in run_query(connection, query):
        print(f"  {row[0]:<20} {row[1]:>10,}")

    print("\nReturns:")

    query = """
        SELECT return_status, COUNT(*)
        FROM returns
        GROUP BY return_status
        ORDER BY COUNT(*) DESC
    """

    for row in run_query(connection, query):
        print(f"  {row[0]:<20} {row[1]:>10,}")


def main():
    engine = create_database_engine()

    print("\nE-COMMERCE SOURCE DATA PROFILE")
    print("=" * 70)

    with engine.connect() as connection:

        profile_row_counts(connection)

        profile_customers(connection)

        profile_orders(connection)

        profile_order_items(connection)

        profile_payments(connection)

        profile_returns(connection)

        profile_referential_integrity(connection)

        profile_date_ranges(connection)

        profile_status_distributions(connection)

    print()
    print("=" * 70)
    print("SOURCE PROFILING COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()