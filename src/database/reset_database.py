from sqlalchemy import text

from src.generator.utils import create_database_engine


TABLES = [
    "returns",
    "payments",
    "order_items",
    "orders",
    "products",
    "categories",
    "customers",
]


def reset_database():

    engine = create_database_engine()

    with engine.begin() as connection:

        for table in TABLES:

            connection.execute(
                text(
                    f"TRUNCATE TABLE "
                    f"{table} "
                    f"RESTART IDENTITY CASCADE"
                )
            )

            print(f"Cleared {table}")

    print("\nDatabase reset complete.")


if __name__ == "__main__":
    reset_database()