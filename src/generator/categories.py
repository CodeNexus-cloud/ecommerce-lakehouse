import random

from sqlalchemy import text

from src.generator.config import DEV_CATEGORIES
from src.generator.utils import create_database_engine, fake


CATEGORY_NAMES = [
    "Electronics",
    "Computers",
    "Mobile Phones",
    "Home Appliances",
    "Furniture",
    "Clothing",
    "Shoes",
    "Sports & Fitness",
    "Beauty",
    "Health",
    "Books",
    "Toys",
    "Automotive",
    "Garden",
    "Kitchen",
    "Jewelry",
    "Pet Supplies",
    "Office Supplies",
    "Groceries",
    "Travel",
]


def generate_categories(count: int = DEV_CATEGORIES):
    """
    Generate product categories and insert them into PostgreSQL.
    """

    engine = create_database_engine()

    records = []

    for i in range(count):
        category_name = CATEGORY_NAMES[i % len(CATEGORY_NAMES)]

        records.append(
            {
                "category_name": category_name,
                "description": fake.sentence(nb_words=8),
            }
        )

    insert_sql = text(
        """
        INSERT INTO categories (
            category_name,
            description
        )
        VALUES (
            :category_name,
            :description
        )
        """
    )

    with engine.begin() as connection:
        connection.execute(insert_sql, records)

    print(f"Inserted {len(records):,} categories.")


if __name__ == "__main__":
    generate_categories()
