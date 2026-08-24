 
import random
from datetime import datetime, timedelta

from sqlalchemy import text

from src.generator.config import (
    ORDER_START_DATE,
    ORDER_END_DATE,
    DEV_ORDERS,
    ORDER_DUPLICATE_RATE,
    ORDER_MISSING_CUSTOMER_RATE,
    ORDER_LATE_ARRIVAL_RATE,
    ORDER_UPDATED_RATE,
)

from src.generator.utils import (
    create_database_engine,
    initialize_random_seed,
    random_bool,
    random_datetime,
    weighted_choice,
)


ORDER_STATUSES = [
    "DELIVERED",
    "SHIPPED",
    "PROCESSING",
    "CONFIRMED",
    "PENDING",
    "CANCELLED",
]

ORDER_STATUS_WEIGHTS = [
    65,
    12,
    8,
    6,
    4,
    5,
]

CURRENCIES = [
    "USD",
    "KES",
    "EUR",
    "GBP",
]


def generate_order_date():
    """
    Generate an order date within the simulated
    operational period.
    """

    start = datetime.fromisoformat(ORDER_START_DATE)
    end = datetime.fromisoformat(ORDER_END_DATE)

    return random_datetime(start, end)


def generate_order_record(customer_ids):

    # ---------------------------------
    # Customer assignment
    # ---------------------------------

    if random_bool(ORDER_MISSING_CUSTOMER_RATE):
        customer_id = None
    else:
        customer_id = random.choice(customer_ids)

    # ---------------------------------
    # Order date
    # ---------------------------------

    order_date = generate_order_date()

    # ---------------------------------
    # Status
    # ---------------------------------

    order_status = weighted_choice(
        ORDER_STATUSES,
        ORDER_STATUS_WEIGHTS,
    )

    # ---------------------------------
    # Amount
    # ---------------------------------

    total_amount = round(
        random.uniform(10, 2500),
        2,
    )

    # ---------------------------------
    # Shipping information
    # ---------------------------------

    shipping_city = random.choice(
        [
            "Nairobi",
            "Mombasa",
            "Kisumu",
            "Nakuru",
            "Eldoret",
            "Nyeri",
            "Thika",
        ]
    )

    shipping_country = "Kenya"

    shipping_address = (
        f"{random.randint(1, 999)} "
        f"{random.choice(['Main', 'Market', 'River', 'Park', 'Station'])} "
        f"Road"
    )

    # ---------------------------------
    # Created timestamp
    # ---------------------------------

    created_at = order_date

    # ---------------------------------
    # Updated timestamp
    # ---------------------------------

    if random_bool(ORDER_UPDATED_RATE):

        max_update = datetime.fromisoformat(
            ORDER_END_DATE
        )

        if created_at < max_update:

            updated_at = random_datetime(
                created_at,
                max_update,
            )

        else:
            updated_at = created_at

    else:
        updated_at = created_at

    # ---------------------------------
    # Late-arriving data
    # ---------------------------------

    # The business event occurred earlier,
    # but the record is considered to have
    # arrived later in the operational system.

    if random_bool(ORDER_LATE_ARRIVAL_RATE):

        created_at = created_at + timedelta(
            days=random.randint(1, 5)
        )

    return {
        "customer_id": customer_id,
        "order_date": order_date,
        "order_status": order_status,
        "currency": random.choice(CURRENCIES),
        "shipping_address": shipping_address,
        "shipping_city": shipping_city,
        "shipping_country": shipping_country,
        "total_amount": total_amount,
        "created_at": created_at,
        "updated_at": updated_at,
    }


def generate_orders(count: int = DEV_ORDERS):

    initialize_random_seed(42)

    engine = create_database_engine()

    # ---------------------------------
    # Load customer IDs
    # ---------------------------------

    with engine.connect() as connection:

        customer_ids = [
            row[0]
            for row in connection.execute(
                text(
                    """
                    SELECT customer_id
                    FROM customers
                    WHERE customer_status = 'ACTIVE'
                    """
                )
            )
        ]

    if not customer_ids:
        raise RuntimeError(
            "No active customers found. "
            "Generate customers first."
        )

    # ---------------------------------
    # Generate base orders
    # ---------------------------------

    records = []

    for _ in range(count):

        record = generate_order_record(
            customer_ids
        )

        records.append(record)

    # ---------------------------------
    # Generate duplicate transactions
    # ---------------------------------

    duplicate_count = int(
        count * ORDER_DUPLICATE_RATE
    )

    for _ in range(duplicate_count):

        duplicate = random.choice(records).copy()

        records.append(duplicate)

    # ---------------------------------
    # Insert
    # ---------------------------------

    insert_sql = text(
        """
        INSERT INTO orders (
            customer_id,
            order_date,
            order_status,
            currency,
            shipping_address,
            shipping_city,
            shipping_country,
            total_amount,
            created_at,
            updated_at
        )
        VALUES (
            :customer_id,
            :order_date,
            :order_status,
            :currency,
            :shipping_address,
            :shipping_city,
            :shipping_country,
            :total_amount,
            :created_at,
            :updated_at
        )
        """
    )

    with engine.begin() as connection:

        connection.execute(
            insert_sql,
            records,
        )

    print(
        f"Inserted {len(records):,} orders "
        f"({duplicate_count:,} duplicate transactions)."
    )


if __name__ == "__main__":
    generate_orders()