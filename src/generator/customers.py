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


def generate_customers(count: int = DEV_CUSTOMERS):

    initialize_random_seed(42)

    engine = create_database_engine()

    records = []

    # Generate the normal customer population
    for _ in range(count):

        record = generate_customer_record()

        records.append(record)

    # Create duplicates from existing customers
    duplicate_count = int(
        count * CUSTOMER_DUPLICATE_RATE
    )

    for _ in range(duplicate_count):

        source_customer = random.choice(records)

        duplicate = generate_customer_record(
            duplicate_source=source_customer
        )

        records.append(duplicate)

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

    with engine.begin() as connection:
        connection.execute(
            insert_sql,
            records,
        )

    print(
        f"Inserted {len(records):,} customers "
        f"({duplicate_count:,} duplicates)."
    )


if __name__ == "__main__":
    generate_customers()