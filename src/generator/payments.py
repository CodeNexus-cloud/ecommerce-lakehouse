import random

from sqlalchemy import text

from src.generator.config import (
    BATCH_SIZE,
    DATASET_SIZE,
    DEV_ORDERS,
    LARGE_ORDERS,
)
from src.generator.utils import (
    create_database_engine,
    initialize_random_seed,
    weighted_choice,
)


PAYMENT_METHODS = [
    "CARD",
    "MOBILE_MONEY",
    "BANK_TRANSFER",
    "CASH",
]


PAYMENT_METHOD_WEIGHTS = [
    45,
    35,
    15,
    5,
]


PAYMENT_STATUSES = [
    "SUCCESS",
    "FAILED",
    "PENDING",
]


PAYMENT_STATUS_WEIGHTS = [
    90,
    7,
    3,
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


def generate_payment_record(order):
    """
    Generate a payment for an order.

    The payment amount comes directly from
    orders.total_amount.
    """

    order_id = order["order_id"]
    order_total = float(
        order["total_amount"] or 0
    )

    payment_status = weighted_choice(
        PAYMENT_STATUSES,
        PAYMENT_STATUS_WEIGHTS,
    )

    # Successful payments normally cover
    # the order amount.
    if payment_status == "SUCCESS":

        amount = order_total

    elif payment_status == "FAILED":

        # Failed payment may be for the full
        # amount or a partial attempted amount.
        amount = round(
            order_total * random.uniform(
                0.1,
                1.0,
            ),
            2,
        )

    else:

        amount = order_total

    return {
        "order_id": order_id,
        "payment_method": weighted_choice(
            PAYMENT_METHODS,
            PAYMENT_METHOD_WEIGHTS,
        ),
        "payment_status": payment_status,
        "amount": amount,
    }


def generate_payments():

    initialize_random_seed(45)

    engine = create_database_engine()

    insert_sql = text(
        """
        INSERT INTO payments (
            order_id,
            payment_method,
            payment_status,
            amount
        )
        VALUES (
            :order_id,
            :payment_method,
            :payment_status,
            :amount
        )
        """
    )

    with engine.begin() as connection:

        last_order_id = 0

        total_orders_processed = 0
        total_payments_inserted = 0

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

            payment_batch = []

            for order in orders:

                payment = generate_payment_record(
                    order
                )

                payment_batch.append(payment)

            connection.execute(
                insert_sql,
                payment_batch,
            )

            total_orders_processed += len(
                orders
            )

            total_payments_inserted += len(
                payment_batch
            )

            last_order_id = orders[-1][
                "order_id"
            ]

            print(
                f"Processed orders: "
                f"{total_orders_processed:,}/"
                f"{get_order_count():,} | "
                f"Payments: "
                f"{total_payments_inserted:,}"
            )

    print()
    print("=" * 70)
    print("PAYMENT GENERATION COMPLETE")
    print("=" * 70)
    print(
        f"Orders processed: "
        f"{total_orders_processed:,}"
    )
    print(
        f"Payments inserted: "
        f"{total_payments_inserted:,}"
    )


if __name__ == "__main__":
    generate_payments()