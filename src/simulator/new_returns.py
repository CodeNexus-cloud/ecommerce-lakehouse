import random
from datetime import timedelta

from sqlalchemy import text

from src.generator.utils import (
    create_database_engine,
)


RETURN_RATE = 0.08

BATCH_SIZE = 5_000


RETURN_REASONS = [
    "DAMAGED",
    "WRONG_ITEM",
    "NOT_AS_DESCRIBED",
    "CHANGED_MIND",
    "SIZE_ISSUE",
    "QUALITY_ISSUE",
]


RETURN_STATUSES = [
    "REQUESTED",
    "APPROVED",
    "RECEIVED",
    "REFUNDED",
    "REJECTED",
]


def generate_new_returns():

    engine = create_database_engine()

    insert_sql = text(
        """
        INSERT INTO returns (
            order_id,
            order_item_id,
            return_date,
            return_reason,
            quantity,
            refund_amount,
            return_status
        )
        VALUES (
            :order_id,
            :order_item_id,
            :return_date,
            :return_reason,
            :quantity,
            :refund_amount,
            :return_status
        )
        """
    )

    total_inserted = 0

    with engine.begin() as connection:

        items = connection.execute(
            text(
                """
                SELECT
                    o.order_id,
                    o.order_date,
                    oi.order_item_id,
                    oi.quantity,
                    oi.unit_price

                FROM orders o

                JOIN order_items oi
                    ON o.order_id =
                    oi.order_id

                LEFT JOIN returns r
                    ON oi.order_item_id =
                    r.order_item_id

                WHERE r.order_item_id
                    IS NULL

                AND oi.quantity > 0
                """
            )
        ).mappings()

        batch = []

        for item in items:

            if (
                random.random()
                > RETURN_RATE
            ):
                continue

            return_quantity = random.randint(
                1,
                int(item["quantity"]),
            )

            refund_amount = round(
                return_quantity
                * float(
                    item["unit_price"]
                ),
                2,
            )

            batch.append(
                {
                    "order_id": item[
                        "order_id"
                    ],
                    "order_item_id": item[
                        "order_item_id"
                    ],
                    "return_date": (
                        item["order_date"]
                        + timedelta(
                            days=random.randint(
                                1,
                                30,
                            )
                        )
                    ),
                    "return_reason": (
                        random.choice(
                            RETURN_REASONS
                        )
                    ),
                    "quantity": (
                        return_quantity
                    ),
                    "refund_amount": (
                        refund_amount
                    ),
                    "return_status": (
                        random.choice(
                            RETURN_STATUSES
                        )
                    ),
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
                    f"Returns inserted: "
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
        f"new returns."
    )


if __name__ == "__main__":
    generate_new_returns()