import random

from sqlalchemy import text

from src.generator.config import (
    LARGE_PRODUCTS,
    DEV_PRODUCTS,
    DATASET_SIZE,
)
from src.generator.utils import create_database_engine, fake


PRODUCT_ADJECTIVES = [
    "Premium",
    "Advanced",
    "Smart",
    "Classic",
    "Professional",
    "Essential",
    "Portable",
    "Wireless",
    "Digital",
    "Ultra",
]

PRODUCT_NOUNS = [
    "Headphones",
    "Laptop",
    "Keyboard",
    "Monitor",
    "Camera",
    "Speaker",
    "Backpack",
    "Watch",
    "Tablet",
    "Phone",
    "Printer",
    "Desk",
    "Chair",
    "Blender",
    "Vacuum",
]


def generate_products(count=None):

    if count is None:

        count = (
            LARGE_PRODUCTS
            if DATASET_SIZE == "large"
            else DEV_PRODUCTS
        )
    """
    Generate products using existing categories.
    """

    engine = create_database_engine()

    with engine.connect() as connection:
        category_ids = [ row[0] for row in connection.execute(
                text(
                    """
                    SELECT category_id
                    FROM categories
                    ORDER BY category_id
                    """
                )
            )
        ]

    if not category_ids:
        raise RuntimeError(
            "No categories found. Generate categories first."
        )

    records = []

    for i in range(count):
        adjective = random.choice(PRODUCT_ADJECTIVES)
        noun = random.choice(PRODUCT_NOUNS)

        product_name = f"{adjective} {noun} {i + 1}"

        unit_price = round(
            random.uniform(10, 2000),
            2,
        )

        cost_price = round(
            unit_price * random.uniform(0.4, 0.8),
            2,
        )

        records.append(
            {
                "category_id": random.choice(category_ids),
                "product_name": product_name,
                "sku": f"SKU-{i + 1:06d}",
                "description": fake.sentence(nb_words=10),
                "unit_price": unit_price,
                "cost_price": cost_price,
                "product_status": random.choices(
                    ["ACTIVE", "INACTIVE"],
                    weights=[95, 5],
                    k=1,
                )[0],
            }
        )

    insert_sql = text(
        """
        INSERT INTO products (
            category_id,
            product_name,
            sku,
            description,
            unit_price,
            cost_price,
            product_status
        )
        VALUES (
            :category_id,
            :product_name,
            :sku,
            :description,
            :unit_price,
            :cost_price,
            :product_status
        )
        """
    )

    with engine.begin() as connection:
        connection.execute(insert_sql, records)

    print(f"Inserted {len(records):,} products.")


if __name__ == "__main__":
    generate_products()