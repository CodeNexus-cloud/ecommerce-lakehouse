import random
from datetime import datetime, timedelta

from sqlalchemy import text

from src.generator.config import (
    BATCH_SIZE,
    DATASET_SIZE,
    DEV_ORDERS,
    LARGE_ORDERS,
    ORDER_LATE_ARRIVAL_RATE,
    ORDER_MISSING_CUSTOMER_RATE,
    ORDER_UPDATED_RATE,
)

from src.generator.utils import (
    create_database_engine,
    initialize_random_seed,
    random_bool,
    weighted_choice,
)


ORDER_STATUSES = [
    "PENDING",
    "CONFIRMED",
    "SHIPPED",
    "DELIVERED",
    "CANCELLED",
]

ORDER_STATUS_WEIGHTS = [
    5,
    10,
    15,
    60,
    10,
]


CURRENCIES = [
    "KES",
]


CITIES = [
    "Nairobi",
    "Mombasa",
    "Kisumu",
    "Nakuru",
    "Eldoret",
    "Nyeri",
    "Thika",
]


STREETS = [
    "Main",
    "Market",
    "River",
    "Park",
    "Station",
]


ORDER_START_DATE = datetime(2023, 1, 1)
ORDER_END_DATE = datetime(2026, 8, 1)


def generate_order_date():
    """
    Generate a business event date for the order.
    """

    total_days = (
        ORDER_END_DATE - ORDER_START_DATE
    ).days

    random_days = random.randint(
        0,
        total_days,
    )

    return (
        ORDER_START_DATE
        + timedelta(days=random_days)
    )


def generate_order_timestamps(order_date):
    """
    Generate created_at and updated_at while
    maintaining:

        order_date <= created_at <= updated_at
    """

    # -----------------------------------------
    # Created timestamp
    # -----------------------------------------

    created_at = order_date

    if random_bool(ORDER_LATE_ARRIVAL_RATE):

        late_arrival_days = random.randint(1, 5)

        created_at = (
            order_date
            + timedelta(days=late_arrival_days)
        )

        # Don't create records outside the
        # simulated source-system period.
        if created_at > ORDER_END_DATE:
            created_at = ORDER_END_DATE

    # -----------------------------------------
    # Updated timestamp
    # -----------------------------------------

    updated_at = created_at

    if random_bool(ORDER_UPDATED_RATE):

        available_seconds = int(
            (
                ORDER_END_DATE - created_at
            ).total_seconds()
        )

        if available_seconds > 0:

            random_seconds = random.randint(
                0,
                available_seconds,
            )

            updated_at = (
                created_at
                + timedelta(
                    seconds=random_seconds
                )
            )

    return created_at, updated_at


def generate_order_record(customer_ids):
    """
    Generate a single order.
    """

    # -----------------------------------------
    # Customer
    # -----------------------------------------

    if random_bool(
        ORDER_MISSING_CUSTOMER_RATE
    ):
        customer_id = None

    else:
        customer_id = random.choice(
            customer_ids
        )

    # -----------------------------------------
    # Order date
    # -----------------------------------------

    order_date = generate_order_date()

    # -----------------------------------------
    # Timestamps
    # -----------------------------------------

    created_at, updated_at = (
        generate_order_timestamps(
            order_date
        )
    )

    # -----------------------------------------
    # Status
    # -----------------------------------------

    order_status = weighted_choice(
        ORDER_STATUSES,
        ORDER_STATUS_WEIGHTS,
    )

    # -----------------------------------------
    # Amount
    # -----------------------------------------

    total_amount = round(
        random.uniform(
            10,
            2500,
        ),
        2,
    )

    # -----------------------------------------
    # Shipping
    # -----------------------------------------

    shipping_city = random.choice(
        CITIES
    )

    shipping_country = "Kenya"

    shipping_address = (
        f"{random.randint(1, 999)} "
        f"{random.choice(STREETS)} "
        f"Road"
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


def get_order_count():
    """
    Return the number of orders based on the
    selected dataset size.
    """

    if DATASET_SIZE == "dev":
        return DEV_ORDERS

    if DATASET_SIZE == "large":
        return LARGE_ORDERS

    raise ValueError(
        f"Unknown DATASET_SIZE: {DATASET_SIZE}"
    )


def get_customer_ids(connection):
    """
    Load customer IDs.

    Customer IDs are small enough to keep in
    memory even for the large dataset.
    """

    rows = connection.execute(
        text(
            """
            SELECT customer_id
            FROM customers
            ORDER BY customer_id
            """
        )
    ).fetchall()

    customer_ids = [
        row[0]
        for row in rows
    ]

    if not customer_ids:
        raise RuntimeError(
            "No customers found. "
            "Generate customers before orders."
        )

    return customer_ids


def generate_orders():
    """
    Generate orders in batches.

    Important:
    We do NOT create a list containing all
    orders. Only one batch exists in memory
    at a time.
    """

    initialize_random_seed(43)

    order_count = get_order_count()

    engine = create_database_engine()

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

    total_inserted = 0

    with engine.begin() as connection:

        customer_ids = get_customer_ids(
            connection
        )

        batch = []

        for _ in range(order_count):

            batch.append(
                generate_order_record(
                    customer_ids
                )
            )

            if len(batch) >= BATCH_SIZE:

                connection.execute(
                    insert_sql,
                    batch,
                )

                total_inserted += len(batch)

                print(
                    f"Inserted orders: "
                    f"{total_inserted:,}/"
                    f"{order_count:,}"
                )

                batch.clear()

        # -------------------------------------
        # Insert final partial batch
        # -------------------------------------

        if batch:

            connection.execute(
                insert_sql,
                batch,
            )

            total_inserted += len(batch)

            batch.clear()

    print()
    print(
        f"Completed order generation: "
        f"{total_inserted:,} orders."
    )


if __name__ == "__main__":
    generate_orders()