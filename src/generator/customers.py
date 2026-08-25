import random
from datetime import datetime

from sqlalchemy import text

from src.generator.config import (
    CUSTOMER_CAPITALIZATION_ERROR_RATE,
    CUSTOMER_DUPLICATE_RATE,
    CUSTOMER_END_DATE,
    CUSTOMER_INVALID_EMAIL_RATE,
    CUSTOMER_MISSING_EMAIL_RATE,
    CUSTOMER_MISSING_PHONE_RATE,
    CUSTOMER_START_DATE,
    CUSTOMER_WHITESPACE_ERROR_RATE,
    DEV_CUSTOMERS,

)
from src.generator.utils import (
    create_database_engine,
    fake,
    initialize_random_seed,
    random_bool,
    random_datetime,
)
from sqlalchemy import text

from src.generator.config import (
    BATCH_SIZE,
    DATASET_SIZE,
    DEV_CUSTOMERS,
    LARGE_CUSTOMERS,
)


def generate_email(first_name: str, last_name: str) -> str:
    """
    Generate a normal email address.
    """

    domains = [
        "gmail.com",
        "yahoo.com",
        "outlook.com",
        "hotmail.com",
        "example.com",
    ]

    return (
        f"{first_name.lower()}."
        f"{last_name.lower()}"
        f"@{random.choice(domains)}"
    )


def generate_phone() -> str:
    """
    Generate a Kenyan-style mobile number.
    """

    prefixes = [
        "0700",
        "0710",
        "0711",
        "0720",
        "0721",
        "0722",
        "0730",
        "0740",
        "0750",
        "0760",
        "0770",
        "0780",
        "0790",
    ]

    return (
        random.choice(prefixes)
        + "".join(random.choices("0123456789", k=6))
    )


def generate_customer_record(
    duplicate_source=None,
):
    """
    Generate one customer record.

    If duplicate_source is supplied, create a second
    source record representing the same real-world customer.
    """

    if duplicate_source:
        first_name = duplicate_source["first_name"]
        last_name = duplicate_source["last_name"]
        email = duplicate_source["email"]
        phone = duplicate_source["phone"]
        date_of_birth = duplicate_source["date_of_birth"]
        gender = duplicate_source["gender"]
        city = duplicate_source["city"]
        country = duplicate_source["country"]

    else:
        first_name = fake.first_name()
        last_name = fake.last_name()

        email = generate_email(
            first_name,
            last_name,
        )

        phone = generate_phone()

        date_of_birth = fake.date_of_birth(
            minimum_age=18,
            maximum_age=80,
        )

        gender = random.choice(
            ["MALE", "FEMALE", "OTHER"]
        )

        city = random.choice(
            [
                "Nairobi",
                "Mombasa",
                "Kisumu",
                "Nakuru",
                "Eldoret",
                "Thika",
                "Nyeri",
                "Machakos",
            ]
        )

        country = "Kenya"

    # -------------------------
    # Data quality issues
    # -------------------------

    if random_bool(CUSTOMER_MISSING_EMAIL_RATE):
        email = None

    elif random_bool(CUSTOMER_INVALID_EMAIL_RATE):
        email = email.replace("@", "")

    if random_bool(CUSTOMER_MISSING_PHONE_RATE):
        phone = None

    if random_bool(CUSTOMER_CAPITALIZATION_ERROR_RATE):
        first_name = first_name.upper()
        last_name = last_name.upper()

    if random_bool(CUSTOMER_WHITESPACE_ERROR_RATE):
        first_name = f" {first_name} "
        last_name = f"{last_name} "

    created_at = random_datetime(
        datetime.fromisoformat(CUSTOMER_START_DATE),
        datetime.fromisoformat(CUSTOMER_END_DATE),
    )

    updated_at = random_datetime(
        created_at,
        datetime.fromisoformat(CUSTOMER_END_DATE),
    )

    return {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
        "date_of_birth": date_of_birth,
        "gender": gender,
        "city": city,
        "country": country,
        "customer_status": random.choices(
            ["ACTIVE", "INACTIVE"],
            weights=[95, 5],
            k=1,
        )[0],
        "created_at": created_at,
        "updated_at": updated_at,
    }


def generate_customers(count=None):

    initialize_random_seed(42)

    if count is None:
        count = (
            LARGE_CUSTOMERS
            if DATASET_SIZE == "large"
            else DEV_CUSTOMERS
        )

    engine = create_database_engine()

    insert_sql = text(
        """
        INSERT INTO customers (
            first_name,
            last_name,
            email,
            phone,
            date_of_birth,
            gender,
            city,
            country,
            customer_status,
            created_at,
            updated_at
        )
        VALUES (
            :first_name,
            :last_name,
            :email,
            :phone,
            :date_of_birth,
            :gender,
            :city,
            :country,
            :customer_status,
            :created_at,
            :updated_at
        )
        """
    )

    total_inserted = 0

    with engine.begin() as connection:

        batch = []

        for _ in range(count):

            batch.append(
                generate_customer_record()
            )

            if len(batch) >= BATCH_SIZE:

                connection.execute(
                    insert_sql,
                    batch,
                )

                total_inserted += len(batch)

                print(
                    f"Inserted customers: "
                    f"{total_inserted:,}/{count:,}"
                )

                batch.clear()

        # Remaining records
        if batch:

            connection.execute(
                insert_sql,
                batch,
            )

            total_inserted += len(batch)

    # -----------------------------------------
    # Duplicate customers
    # -----------------------------------------

    duplicate_count = int(
        count * CUSTOMER_DUPLICATE_RATE
    )

    with engine.begin() as connection:

        source_customers = connection.execute(
            text(
                """
                SELECT
                    first_name,
                    last_name,
                    email,
                    phone,
                    date_of_birth,
                    gender,
                    city,
                    country,
                    customer_status,
                    created_at,
                    updated_at
                FROM customers
                ORDER BY RANDOM()
                LIMIT :duplicate_count
                """
            ),
            {
                "duplicate_count": duplicate_count
            },
        ).mappings().all()

        duplicate_records = [
            dict(customer)
            for customer in source_customers
        ]

        connection.execute(
            insert_sql,
            duplicate_records,
        )

    total_inserted += duplicate_count

    print(
        f"Inserted {total_inserted:,} customers "
        f"including {duplicate_count:,} duplicates."
    )

if __name__ == "__main__":
    generate_customers()