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

    order_id = order["order_id"]
    order_total = float(
        order["total_amount"] or 0
    )

    return_amount = round(
        order_total
        * random.uniform(
            0.1,
            1.0,
        ),
        2,
    )

    return {
        "order_id": order_id,
        "return_reason": random.choice(
            RETURN_REASONS
        ),
        "return_status": random.choice(
            RETURN_STATUSES
        ),
        "refund_amount": return_amount,
    }


def generate_returns():

    initialize_random_seed(46)

    engine = create_database_engine()

    insert_sql = text(
        """
        INSERT INTO returns (
            order_id,
            return_reason,
            return_status,
            refund_amount
        )
        VALUES (
            :order_id,
            :return_reason,
            :return_status,
            :refund_amount
        )
        """
    )

    with engine.begin() as connection:

        last_order_id = 0

        total_orders_processed = 0
        total_returns_inserted = 0

        while True:

            orders = connection.execute(
                text(
                    """
                    SELECT
                        order_id,
                        total_amount
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
            ).mappings().all()

            if not orders:
                break

            return_batch = []

            for order in orders:

                # Not every order is returned.
                if random.random() > RETURN_RATE:
                    continue

                return_record = (
                    generate_return_record(
                        order
                    )
                )

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


if __name__ == "__main__":
    generate_returns()