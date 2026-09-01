import random

from sqlalchemy import text

from src.generator.utils import (
    create_database_engine,
    fake,
)


NEW_PRODUCTS = 500


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
]


def generate_new_products():

    engine = create_database_engine()

    with engine.connect() as connection:

        category_ids = [
            row[0]
            for row in connection.execute(
                text(
                    """
                    SELECT category_id
                    FROM categories
                    """
                )
            )
        ]

        last_product_id = connection.execute(
            text(
                """
                SELECT COALESCE(
                    MAX(product_id),
                    0
                )
                FROM products
                """
            )
        ).scalar()

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

    records = []

    for i in range(NEW_PRODUCTS):

        product_number = (
            last_product_id
            + i
            + 1
        )

        adjective = random.choice(
            PRODUCT_ADJECTIVES
        )

        noun = random.choice(
            PRODUCT_NOUNS
        )

        unit_price = round(
            random.uniform(10, 2000),
            2,
        )

        records.append(
            {
                "category_id": random.choice(
                    category_ids
                ),
                "product_name": (
                    f"{adjective} "
                    f"{noun} "
                    f"{product_number}"
                ),
                "sku": (
                    f"SKU-"
                    f"{product_number:06d}"
                ),
                "description": fake.sentence(
                    nb_words=10
                ),
                "unit_price": unit_price,
                "cost_price": round(
                    unit_price
                    * random.uniform(
                        0.4,
                        0.8,
                    ),
                    2,
                ),
                "product_status": "ACTIVE",
            }
        )

    with engine.begin() as connection:

        connection.execute(
            insert_sql,
            records,
        )

    print(
        f"Inserted {NEW_PRODUCTS:,} new products."
    )


if __name__ == "__main__":
    generate_new_products()