import random

from sqlalchemy import text

from src.generator.config import BATCH_SIZE, ORDER_ITEM_INVALID_QUANTITY_RATE
from src.generator.utils import (
    create_database_engine,
    initialize_random_seed,
    random_bool,
)


MIN_ITEMS_PER_ORDER = 1
MAX_ITEMS_PER_ORDER = 5


def get_products(connection):
    rows = connection.execute(
        text(
            """
            SELECT
                product_id,
                unit_price
            FROM products
            ORDER BY product_id
            """
        )
    ).mappings().all()

    if not rows:
        raise RuntimeError("No products found.")

    return [
        {
            "product_id": row["product_id"],
            "unit_price": float(row["unit_price"]),
        }
        for row in rows
    ]


def generate_items_for_order(order_id, products):

    item_count = random.randint(
        MIN_ITEMS_PER_ORDER,
        MAX_ITEMS_PER_ORDER,
    )

    selected_products = random.sample(
        products,
        min(item_count, len(products)),
    )

    items = []

    for product in selected_products:

        quantity = random.randint(1, 5)

        # Preserve the intentionally messy source data
        if random_bool(ORDER_ITEM_INVALID_QUANTITY_RATE):
            quantity = random.choice([0, -1])

        unit_price = product["unit_price"]

        line_total = round(
            quantity * unit_price,
            2,
        )

        items.append(
            {
                "order_id": order_id,
                "product_id": product["product_id"],
                "quantity": quantity,
                "unit_price": unit_price,
                "line_total": line_total,
            }
        )

    return items


def generate_new_order_items(previous_max_order_id):

    initialize_random_seed(47)

    engine = create_database_engine()

    insert_sql = text(
        """
        INSERT INTO order_items (
            order_id,
            product_id,
            quantity,
            unit_price,
            line_total
        )
        VALUES (
            :order_id,
            :product_id,
            :quantity,
            :unit_price,
            :line_total
        )
        """
    )

    update_order_sql = text(
        """
        UPDATE orders o
        SET total_amount = totals.order_total
        FROM (
            SELECT
                order_id,
                ROUND(SUM(line_total)::numeric, 2) AS order_total
            FROM order_items
            WHERE order_id > :previous_max_order_id
            GROUP BY order_id
        ) totals
        WHERE o.order_id = totals.order_id
        """
    )

    with engine.begin() as connection:

        products = get_products(connection)

        orders = connection.execute(
            text(
                """
                SELECT order_id
                FROM orders
                WHERE order_id > :previous_max_order_id
                ORDER BY order_id
                """
            ),
            {
                "previous_max_order_id": previous_max_order_id
            },
        ).fetchall()

        print(
            f"New orders found: {len(orders):,}"
        )

        total_items = 0

        batch = []

        for row in orders:

            order_id = row[0]

            items = generate_items_for_order(
                order_id,
                products,
            )

            batch.extend(items)

            if len(batch) >= BATCH_SIZE:

                connection.execute(
                    insert_sql,
                    batch,
                )

                total_items += len(batch)
                batch.clear()

        if batch:

            connection.execute(
                insert_sql,
                batch,
            )

            total_items += len(batch)

        # Recalculate total_amount for ONLY the new orders
        connection.execute(
            update_order_sql,
            {
                "previous_max_order_id": previous_max_order_id
            },
        )

    print(
        f"Inserted {total_items:,} new order items."
    )


if __name__ == "__main__":

    # Example:
    # Before generating new orders, MAX(order_id) was 2,000,000.
    #
    # Replace this with the actual value from your database.

    PREVIOUS_MAX_ORDER_ID = 2_000_000

    generate_new_order_items(
        PREVIOUS_MAX_ORDER_ID
    )