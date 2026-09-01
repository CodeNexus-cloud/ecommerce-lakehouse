import random
from datetime import datetime

from sqlalchemy import text

from src.generator.utils import (
    create_database_engine,
    fake,
    random_datetime,
)


NEW_CUSTOMERS = 5_000


def generate_email(first_name, last_name):
    domains = [
        "gmail.com",
        "yahoo.com",
        "outlook.com",
        "hotmail.com",
    ]

    return (
        f"{first_name.lower()}."
        f"{last_name.lower()}@"
        f"{random.choice(domains)}"
    )


def generate_phone():

    prefixes = [
        "0700",
        "0710",
        "0720",
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
        + "".join(
            random.choices("0123456789", k=6)
        )
    )


def generate_new_customers():

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

    records = []

    for _ in range(NEW_CUSTOMERS):

        first_name = fake.first_name()
        last_name = fake.last_name()

        created_at = random_datetime(
            datetime(2026, 8, 2),
            datetime(2026, 8, 31),
        )

        records.append(
            {
                "first_name": first_name,
                "last_name": last_name,
                "email": generate_email(
                    first_name,
                    last_name,
                ),
                "phone": generate_phone(),
                "date_of_birth": fake.date_of_birth(
                    minimum_age=18,
                    maximum_age=80,
                ),
                "gender": random.choice(
                    ["MALE", "FEMALE", "OTHER"]
                ),
                "city": random.choice(
                    [
                        "Nairobi",
                        "Mombasa",
                        "Kisumu",
                        "Nakuru",
                        "Eldoret",
                        "Nyeri",
                    ]
                ),
                "country": "Kenya",
                "customer_status": "ACTIVE",
                "created_at": created_at,
                "updated_at": created_at,
            }
        )

    with engine.begin() as connection:

        connection.execute(
            insert_sql,
            records,
        )

    print(
        f"Inserted {NEW_CUSTOMERS:,} new customers."
    )


if __name__ == "__main__":
    generate_new_customers()