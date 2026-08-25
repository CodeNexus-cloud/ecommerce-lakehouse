import random

from sqlalchemy import text

from src.generator.config import (
    ORDER_ITEM_DUPLICATE_RATE,
    ORDER_ITEM_INVALID_QUANTITY_RATE,
)


from src.generator.utils import (
    create_database_engine,
    initialize_random_seed,
    random_bool,
)


def generate_order_items():
    """
    Generate order items for existing orders and products.
    """

    initialize_random_seed(43)

    engine = create_database_engine()

    # Load orders
    with engine.connect() as connection:
        order_ids = [
            row[0]
            for row in connection.execute(
                text(
                    """
                    SELECT order_id
                    FROM orders
                    ORDER BY order_id
                    """
                )
            )
        ]

    # Load products and their current prices
    with engine.connect() as connection:
        products = [
            {
                "product_id": row[0],
                "unit_price": float(row[1]),
            }
            for row in connection.execute(
                text(
                    """
                    SELECT
                        product_id,
                        unit_price
                    FROM products
                    WHERE product_status = 'ACTIVE'
                    """
                )
            )
        ]

    if not order_ids:
        raise RuntimeError(
            "No orders found. Generate orders first."
        )

    if not products:
        raise RuntimeError(
            "No active products found."
        )

    records = []

    for order_id in order_ids:

        # Number of items in this order
        item_count = random.choices(
            population=[1, 2, 3, 4, 5],
            weights=[55, 25, 12, 5, 3],
            k=1,
        )[0]

        selected_products = random.sample(
            products,
            k=min(item_count, len(products)),
        )

        for product in selected_products:

            quantity = random.choices(
                population=[1, 2, 3, 4, 5],
                weights=[60, 25, 10, 4, 1],
                k=1,
            )[0]

            # Intentionally introduce bad quantities
            if random_bool(
                ORDER_ITEM_INVALID_QUANTITY_RATE
            ):
                quantity = random.choice([0, -1, -2])

            unit_price = product["unit_price"]

            discount_amount = round(
                unit_price
                * quantity
                * random.choice(
                    [0, 0, 0, 0.05, 0.10, 0.15]
                ),
                2,
            )

            line_total = round(
                (unit_price * quantity)
                - discount_amount,
                2,
            )

            record = {
                "order_id": order_id,
                "product_id": product["product_id"],
                "quantity": quantity,
                "unit_price": unit_price,
                "discount_amount": discount_amount,
                "line_total": line_total,
            }

            records.append(record)

    # -----------------------------------------
    # Introduce duplicate order-item records
    # -----------------------------------------

    duplicate_count = int(
        len(records) * ORDER_ITEM_DUPLICATE_RATE
    )

    for _ in range(duplicate_count):
        duplicate = random.choice(records).copy()
        records.append(duplicate)

    # -----------------------------------------
    # Insert records
    # -----------------------------------------

    insert_sql = text(
        """
        INSERT INTO order_items (
            order_id,
            product_id,
            quantity,
            unit_price,
            discount_amount,
            line_total
        )
        VALUES (
            :order_id,
            :product_id,
            :quantity,
            :unit_price,
            :discount_amount,
            :line_total
        )
        """
    )

    with engine.begin() as connection:
        connection.execute(
            insert_sql,
            records,
        )

    print(
        f"Inserted {len(records):,} order items "
        f"({duplicate_count:,} duplicate records)."
    )


if __name__ == "__main__":
    generate_order_items()