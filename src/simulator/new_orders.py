import random
from datetime import datetime, timedelta

from sqlalchemy import text

from src.generator.utils import (
    create_database_engine,
)


NEW_ORDERS = 50_000

BATCH_SIZE = 1_000

MIN_ITEMS = 1
MAX_ITEMS = 5


def generate_order_date():

    start_date = datetime(
        2026,
        8,
        2,
    )

    end_date = datetime(
        2026,
        8,
        31,
    )

    days = (
        end_date - start_date
    ).days

    return (
        start_date
        + timedelta(
            days=random.randint(
                0,
                days,
            )
        )
    )


def generate_new_orders():

    engine = create_database_engine()

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

        products = connection.execute(
            text(
                """
                SELECT
                    product_id,
                    unit_price
                FROM products
                WHERE product_status = 'ACTIVE'
                """
            )
        ).mappings().all()

    insert_order_sql = text(
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
        RETURNING order_id
        """
    )

    insert_item_sql = text(
        """
        INSERT INTO order_items (
            order_id,
            product_id,
            quantity,
            unit_price,
            line_total
        )
        VALUES (
            :order_id,
            :product_id,
            :quantity,
            :unit_price,
            :line_total
        )
        """
    )

    update_order_sql = text(
        """
        UPDATE orders
        SET total_amount = :total_amount
        WHERE order_id = :order_id
        """
    )

    total_orders = 0
    total_items = 0

    with engine.begin() as connection:

        for _ in range(NEW_ORDERS):

            order_date = generate_order_date()

            customer_id = random.choice(
                customer_ids
            )

            result = connection.execute(
                insert_order_sql,
                {
                    "customer_id": customer_id,
                    "order_date": order_date,
                    "order_status": random.choices(
                        [
                            "PENDING",
                            "CONFIRMED",
                            "SHIPPED",
                            "DELIVERED",
                        ],
                        weights=[
                            5,
                            10,
                            20,
                            65,
                        ],
                    )[0],
                    "currency": "KES",
                    "shipping_address": (
                        f"{random.randint(1, 999)} "
                        f"Main Road"
                    ),
                    "shipping_city": random.choice(
                        [
                            "Nairobi",
                            "Mombasa",
                            "Kisumu",
                            "Nakuru",
                            "Eldoret",
                            "Nyeri",
                        ]
                    ),
                    "shipping_country": "Kenya",
                    "total_amount": 0,
                    "created_at": order_date,
                    "updated_at": order_date,
                },
            )

            order_id = result.scalar()

            item_count = random.randint(
                MIN_ITEMS,
                MAX_ITEMS,
            )

            selected_products = random.sample(
                products,
                item_count,
            )

            item_records = []

            order_total = 0

            for product in selected_products:

                quantity = random.randint(
                    1,
                    5,
                )

                unit_price = float(
                    product["unit_price"]
                )

                line_total = round(
                    quantity
                    * unit_price,
                    2,
                )

                order_total += line_total

                item_records.append(
                    {
                        "order_id": order_id,
                        "product_id": product[
                            "product_id"
                        ],
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "line_total": line_total,
                    }
                )

            connection.execute(
                insert_item_sql,
                item_records,
            )

            connection.execute(
                update_order_sql,
                {
                    "order_id": order_id,
                    "total_amount": round(
                        order_total,
                        2,
                    ),
                },
            )

            total_orders += 1

            total_items += len(
                item_records
            )

            if (
                total_orders
                % BATCH_SIZE
                == 0
            ):

                print(
                    f"Orders: "
                    f"{total_orders:,}/"
                    f"{NEW_ORDERS:,} | "
                    f"Items: "
                    f"{total_items:,}"
                )

    print()
    print(
        f"Inserted "
        f"{total_orders:,} "
        f"new orders."
    )

    print(
        f"Inserted "
        f"{total_items:,} "
        f"new order items."
    )


if __name__ == "__main__":
    generate_new_orders()