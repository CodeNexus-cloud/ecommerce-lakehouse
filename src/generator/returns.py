import random

from sqlalchemy import text

from src.generator.config import (
    BATCH_SIZE,
    DATASET_SIZE,
    DEV_ORDERS,
    LARGE_ORDERS,
    RETURN_RATE,
)
from src.generator.utils import (
    create_database_engine,
    initialize_random_seed,
)


RETURN_REASONS = [
    "DAMAGED",
    "WRONG_ITEM",
    "NOT_AS_DESCRIBED",
    "CHANGED_MIND",
    "SIZE_ISSUE",
    "QUALITY_ISSUE",
]


RETURN_STATUSES = [
    "REQUESTED",
    "APPROVED",
    "RECEIVED",
    "REFUNDED",
    "REJECTED",
]


def get_order_count():
    """Return expected order count for selected dataset."""

    if DATASET_SIZE == "dev":
        return DEV_ORDERS

    if DATASET_SIZE == "large":
        return LARGE_ORDERS

    raise ValueError(
        f"Unknown DATASET_SIZE: {DATASET_SIZE}"
    )


def generate_return_record(order):
    """
    Generate one return record for a specific order item.
    """

    order_id = order["order_id"]
    order_item_id = order["order_item_id"]

    item_quantity = int(
        order["item_quantity"] or 0
    )

    unit_price = float(
        order["unit_price"] or 0
    )

    discount_amount = float(
        order["discount_amount"] or 0
    )

    # Safety check
    if item_quantity <= 0:
        return None

    # A return cannot exceed the quantity purchased
    return_quantity = random.randint(
        1,
        item_quantity,
    )

    # Allocate discount proportionally to the returned quantity
    discount_per_unit = (
        discount_amount / item_quantity
        if item_quantity > 0
        else 0
    )

    refund_amount = round(
        (
            unit_price
            - discount_per_unit
        )
        * return_quantity,
        2,
    )

    # Return date occurs after the order date
    order_date = order["order_date"]

    return_date = (
        order_date
        + __import__("datetime").timedelta(
            days=random.randint(1, 30)
        )
    )

    return {
        "order_id": order_id,
        "order_item_id": order_item_id,
        "return_date": return_date,
        "return_reason": random.choice(
            RETURN_REASONS
        ),
        "quantity": return_quantity,
        "refund_amount": max(
            refund_amount,
            0,
        ),
        "return_status": random.choice(
            RETURN_STATUSES
        ),
    }


def generate_returns():

    initialize_random_seed(46)

    engine = create_database_engine()

    insert_sql = text(
        """
        INSERT INTO returns (
            order_id,
            order_item_id,
            return_date,
            return_reason,
            quantity,
            refund_amount,
            return_status
        )
        VALUES (
            :order_id,
            :order_item_id,
            :return_date,
            :return_reason,
            :quantity,
            :refund_amount,
            :return_status
        )
        """
    )

    with engine.begin() as connection:

        last_order_id = 0

        total_orders_processed = 0
        total_returns_inserted = 0
        total_returns_skipped = 0

        while True:

            orders = connection.execute(
                text(
                    """
                    SELECT
                        o.order_id,
                        o.total_amount,
                        o.order_date,
                        oi.order_item_id,
                        oi.quantity AS item_quantity,
                        oi.unit_price,
                        oi.discount_amount

                    FROM orders o

                    JOIN LATERAL (
                        SELECT
                            order_item_id,
                            quantity,
                            unit_price,
                            discount_amount

                        FROM order_items oi

                        WHERE oi.order_id = o.order_id

                        ORDER BY random()

                        LIMIT 1

                    ) oi ON TRUE

                    WHERE o.order_id > :last_order_id

                    ORDER BY o.order_id

                    LIMIT :batch_size
                    """
                ),
                {
                    "last_order_id": last_order_id,
                    "batch_size": BATCH_SIZE,
                },
            ).mappings().all()

            if not orders:
                break

            return_batch = []

            for order in orders:

                # Not every order is returned.
                if random.random() > RETURN_RATE:
                    continue

                return_record = generate_return_record(
                    order
                )

                if return_record is None:

                    total_returns_skipped += 1

                    continue

                return_batch.append(
                    return_record
                )

            if return_batch:

                connection.execute(
                    insert_sql,
                    return_batch,
                )

                total_returns_inserted += len(
                    return_batch
                )

            total_orders_processed += len(
                orders
            )

            last_order_id = orders[-1][
                "order_id"
            ]

            print(
                f"Processed orders: "
                f"{total_orders_processed:,}/"
                f"{get_order_count():,} | "
                f"Returns: "
                f"{total_returns_inserted:,}"
            )

    print()
    print("=" * 70)
    print("RETURN GENERATION COMPLETE")
    print("=" * 70)

    print(
        f"Orders processed: "
        f"{total_orders_processed:,}"
    )

    print(
        f"Returns inserted: "
        f"{total_returns_inserted:,}"
    )

    print(
        f"Returns skipped: "
        f"{total_returns_skipped:,}"
    )


if __name__ == "__main__":
    generate_returns()