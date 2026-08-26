import random

from sqlalchemy import text

from src.generator.config import (
    BATCH_SIZE,
    DATASET_SIZE,
    DEV_ORDERS,
    LARGE_ORDERS,
    ORDER_ITEM_INVALID_QUANTITY_RATE,
)
from src.generator.utils import (
    create_database_engine,
    initialize_random_seed,
    random_bool,
)


MIN_ITEMS_PER_ORDER = 1
MAX_ITEMS_PER_ORDER = 5


def get_order_count():
    """Return expected order count for selected dataset."""

    if DATASET_SIZE == "dev":
        return DEV_ORDERS

    if DATASET_SIZE == "large":
        return LARGE_ORDERS

    raise ValueError(
        f"Unknown DATASET_SIZE: {DATASET_SIZE}"
    )


def get_products(connection):
    """
    Load product IDs and their current unit prices.

    Products are small enough to keep in memory.
    """

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

    products = [
        {
            "product_id": row["product_id"],
            "unit_price": float(row["unit_price"]),
        }
        for row in rows
    ]

    if not products:
        raise RuntimeError(
            "No products found. "
            "Generate products before order items."
        )

    return products


def generate_items_for_order(
    order_id,
    products,
):
    """
    Generate 1-5 order items for a single order.

    Returns:
        order_items
        calculated_order_total
    """

    item_count = random.randint(
        MIN_ITEMS_PER_ORDER,
        MAX_ITEMS_PER_ORDER,
    )

    # Prefer unique products within an order.
    if len(products) >= item_count:

        selected_products = random.sample(
            products,
            item_count,
        )

    else:

        selected_products = [
            random.choice(products)
            for _ in range(item_count)
        ]

    order_items = []
    order_total = 0.0

    for product in selected_products:

        quantity = random.randint(1, 5)

        # -----------------------------------------
        # Deliberately introduce bad source data
        # -----------------------------------------

        if random_bool(
            ORDER_ITEM_INVALID_QUANTITY_RATE
        ):
            quantity = random.choice(
                [
                    0,
                    -1,
                ]
            )

        unit_price = product["unit_price"]

        line_total = round(
            quantity * unit_price,
            2,
        )

        order_items.append(
            {
                "order_id": order_id,
                "product_id": product["product_id"],
                "quantity": quantity,
                "unit_price": unit_price,
                "line_total": line_total,
            }
        )

        order_total += line_total

    return (
        order_items,
        round(order_total, 2),
    )


def generate_order_items():
    """
    Generate order items in batches and update
    orders.total_amount from calculated item totals.
    """

    initialize_random_seed(44)

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
        UPDATE orders
        SET total_amount = :total_amount
        WHERE order_id = :order_id
        """
    )

    with engine.begin() as connection:

        products = get_products(connection)

        # -----------------------------------------
        # Process orders in batches
        # -----------------------------------------

        last_order_id = 0
        total_orders_processed = 0
        total_items_inserted = 0

        while True:

            orders = connection.execute(
                text(
                    """
                    SELECT
                        order_id
                    FROM orders
                    WHERE order_id > :last_order_id
                    ORDER BY order_id
                    LIMIT :batch_size
                    """
                ),
                {
                    "last_order_id": last_order_id,
                    "batch_size": BATCH_SIZE,
                },
            ).fetchall()

            if not orders:
                break

            item_batch = []
            order_total_updates = []

            # -------------------------------------
            # Generate items for each order
            # -------------------------------------

            for row in orders:

                order_id = row[0]

                (
                    order_items,
                    order_total,
                ) = generate_items_for_order(
                    order_id,
                    products,
                )

                item_batch.extend(order_items)

                order_total_updates.append(
                    {
                        "order_id": order_id,
                        "total_amount": order_total,
                    }
                )

            # -------------------------------------
            # Insert order items
            # -------------------------------------

            connection.execute(
                insert_sql,
                item_batch,
            )

            # -------------------------------------
            # Update order totals
            # -------------------------------------

            connection.execute(
                update_order_sql,
                order_total_updates,
            )

            # -------------------------------------
            # Progress
            # -------------------------------------

            total_orders_processed += len(orders)

            total_items_inserted += len(
                item_batch
            )

            last_order_id = orders[-1][0]

            print(
                f"Processed orders: "
                f"{total_orders_processed:,}/"
                f"{get_order_count():,} | "
                f"Order items: "
                f"{total_items_inserted:,}"
            )

    print()
    print("=" * 70)
    print("ORDER ITEM GENERATION COMPLETE")
    print("=" * 70)
    print(
        f"Orders processed: "
        f"{total_orders_processed:,}"
    )
    print(
        f"Order items inserted: "
        f"{total_items_inserted:,}"
    )


if __name__ == "__main__":
    generate_order_items()