import random
import uuid
from datetime import timedelta

from sqlalchemy import text

from src.generator.config import (
    PAYMENT_AMOUNT_MISMATCH_RATE,
    PAYMENT_DUPLICATE_RATE,
    PAYMENT_MISSING_REFERENCE_RATE,
    PAYMENT_NO_PAYMENT_RATE,
)
from src.generator.utils import (
    create_database_engine,
    initialize_random_seed,
    random_bool,
    random_datetime,
    weighted_choice,
)


PAYMENT_METHODS = [
    "CARD",
    "PAYPAL",
    "BANK_TRANSFER",
    "MOBILE_MONEY",
]

PAYMENT_METHOD_WEIGHTS = [
    50,
    20,
    10,
    20,
]


PAYMENT_STATUSES = [
    "SUCCESS",
    "FAILED",
    "PENDING",
    "REFUNDED",
]

PAYMENT_STATUS_WEIGHTS = [
    85,
    7,
    5,
    3,
]


def generate_transaction_reference():
    """
    Generate a unique-looking payment transaction reference.
    """

    return f"TXN-{uuid.uuid4().hex[:16].upper()}"


def generate_payments():

    initialize_random_seed(44)

    engine = create_database_engine()

    # -----------------------------------------
    # Load orders
    # -----------------------------------------

    with engine.connect() as connection:

        orders = [
            {
                "order_id": row[0],
                "order_date": row[1],
                "total_amount": float(row[2]),
            }
            for row in connection.execute(
                text(
                    """
                    SELECT
                        order_id,
                        order_date,
                        total_amount
                    FROM orders
                    """
                )
            )
        ]

    if not orders:
        raise RuntimeError(
            "No orders found. Generate orders first."
        )

    records = []

    # -----------------------------------------
    # Generate payments
    # -----------------------------------------

    for order in orders:

        # Some orders intentionally have no payment
        if random_bool(PAYMENT_NO_PAYMENT_RATE):
            continue

        payment_status = weighted_choice(
            PAYMENT_STATUSES,
            PAYMENT_STATUS_WEIGHTS,
        )

        payment_method = weighted_choice(
            PAYMENT_METHODS,
            PAYMENT_METHOD_WEIGHTS,
        )

        # Payment normally equals order total
        amount = order["total_amount"]

        # Introduce amount mismatches
        if random_bool(PAYMENT_AMOUNT_MISMATCH_RATE):

            adjustment = random.choice(
                [
                    -10,
                    -20,
                    -50,
                    10,
                    20,
                    50,
                ]
            )

            amount = round(
                max(0, amount + adjustment),
                2,
            )

        payment_date = order["order_date"] + timedelta(
            hours=random.randint(1, 72)
        )

        transaction_reference = (
            generate_transaction_reference()
        )

        # Missing transaction reference
        if random_bool(
            PAYMENT_MISSING_REFERENCE_RATE
        ):
            transaction_reference = None

        records.append(
            {
                "order_id": order["order_id"],
                "payment_date": payment_date,
                "payment_method": payment_method,
                "payment_status": payment_status,
                "amount": amount,
                "transaction_reference": transaction_reference,
            }
        )

    # -----------------------------------------
    # Duplicate payment records
    # -----------------------------------------

    duplicate_count = int(
        len(records) * PAYMENT_DUPLICATE_RATE
    )

    for _ in range(duplicate_count):

        duplicate = random.choice(records).copy()

        records.append(duplicate)

    # -----------------------------------------
    # Insert
    # -----------------------------------------

    insert_sql = text(
        """
        INSERT INTO payments (
            order_id,
            payment_date,
            payment_method,
            payment_status,
            amount,
            transaction_reference
        )
        VALUES (
            :order_id,
            :payment_date,
            :payment_method,
            :payment_status,
            :amount,
            :transaction_reference
        )
        """
    )

    with engine.begin() as connection:

        connection.execute(
            insert_sql,
            records,
        )

    print(
        f"Inserted {len(records):,} payments "
        f"({duplicate_count:,} duplicate records)."
    )


if __name__ == "__main__":
    generate_payments()
