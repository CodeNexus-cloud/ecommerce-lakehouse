from sqlalchemy import text
from src.generator.utils import create_database_engine, fake


NEW_CATEGORIES = [
    "Smart Home",
    "Gaming",
    "Baby Products",
    "Musical Instruments",
    "Industrial Equipment",
]


def generate_new_categories():

    engine = create_database_engine()

    insert_sql = text(
        """
        INSERT INTO categories (
            category_name,
            description
        )
        SELECT
            :category_name,
            :description
        WHERE NOT EXISTS (
            SELECT 1
            FROM categories
            WHERE LOWER(category_name) = LOWER(:category_name)
        )
        """
    )

    inserted = 0

    with engine.begin() as connection:

        for category_name in NEW_CATEGORIES:

            result = connection.execute(
                insert_sql,
                {
                    "category_name": category_name,
                    "description": fake.sentence(nb_words=8),
                },
            )

            if result.rowcount == 1:
                inserted += 1
                print(f"Inserted: {category_name}")
            else:
                print(f"Already exists: {category_name}")

    print(f"\nNew categories inserted: {inserted}")


if __name__ == "__main__":
    generate_new_categories()