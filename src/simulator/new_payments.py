import random

from sqlalchemy import text

from src.generator.utils import (
    create_database_engine,
)


BATCH_SIZE = 5_000


def generate_new_payments():

    engine = create_database_engine()

    insert_sql = text(
        """
        INSERT INTO payments (
            order_id,
            payment_method,
            payment_status,
            amount
        )
        VALUES (
            :order_id,
            :payment_method,
            :payment_status,
            :amount
        )
        """
    )

    total_inserted = 0

    with engine.begin() as connection:

        orders = connection.execute(
            text(
                """
                SELECT
                    o.order_id,
                    o.total_amount

                FROM orders o

                LEFT JOIN payments p
                    ON o.order_id =
                    p.order_id

                WHERE p.order_id IS NULL

                ORDER BY o.order_id
                """
            )
        ).mappings()

        batch = []

        for order in orders:

            payment_status = random.choices(
                [
                    "SUCCESS",
                    "FAILED",
                    "PENDING",
                ],
                weights=[
                    90,
                    7,
                    3,
                ],
            )[0]

            order_total = float(
                order["total_amount"]
            )

            if (
                payment_status
                == "FAILED"
            ):

                amount = round(
                    order_total
                    * random.uniform(
                        0.1,
                        1.0,
                    ),
                    2,
                )

            else:

                amount = order_total

            batch.append(
                {
                    "order_id": order[
                        "order_id"
                    ],
                    "payment_method": random.choices(
                        [
                            "CARD",
                            "MOBILE_MONEY",
                            "BANK_TRANSFER",
                            "CASH",
                        ],
                        weights=[
                            45,
                            35,
                            15,
                            5,
                        ],
                    )[0],
                    "payment_status": (
                        payment_status
                    ),
                    "amount": amount,
                }
            )

            if len(batch) >= BATCH_SIZE:

                connection.execute(
                    insert_sql,
                    batch,
                )

                total_inserted += len(
                    batch
                )

                print(
                    f"Payments inserted: "
                    f"{total_inserted:,}"
                )

                batch.clear()

        if batch:

            connection.execute(
                insert_sql,
                batch,
            )

            total_inserted += len(
                batch
            )

    print(
        f"Inserted "
        f"{total_inserted:,} "
        f"new payments."
    )


if __name__ == "__main__":
    generate_new_payments()