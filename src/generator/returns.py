import random
from datetime import timedelta

from sqlalchemy import text


from src.generator.config import (
    MAX_RETURN_DAYS_AFTER_ORDER,
    RETURN_DUPLICATE_RATE,
    RETURN_INVALID_QUANTITY_RATE,
    RETURN_RATE,
)


from src.generator.utils import (
    create_database_engine,
    initialize_random_seed,
    random_bool,
    weighted_choice,
)


RETURN_REASONS = [
    "DAMAGED",
    "DEFECTIVE",
    "WRONG_ITEM",
    "NOT_AS_DESCRIBED",
    "CHANGED_MIND",
    "SIZE_ISSUE",
]

RETURN_REASON_WEIGHTS = [
    15,
    15,
    10,
    15,
    30,
    15,
]


RETURN_STATUSES = [
    "REQUESTED",
    "APPROVED",
    "REJECTED",
    "COMPLETED",
]

RETURN_STATUS_WEIGHTS = [
    10,
    15,
    5,
    70,
]


def generate_returns():
    """
    Generate return records for existing order items.
    """

    initialize_random_seed(45)

    engine = create_database_engine()

    # -----------------------------------------
    # Load order items with order information
    # -----------------------------------------

    with engine.connect() as connection:

        order_items = [
            {
                "order_item_id": row[0],
                "order_id": row[1],
                "quantity": row[2],
                "unit_price": float(row[3]),
                "order_date": row[4],
                "order_status": row[5],
            }
            for row in connection.execute(
                text(
                    """
                    SELECT
                        oi.order_item_id,
                        oi.order_id,
                        oi.quantity,
                        oi.unit_price,
                        o.order_date,
                        o.order_status
                    FROM order_items oi
                    INNER JOIN orders o
                        ON oi.order_id = o.order_id
                    """
                )
            )
        ]

    if not order_items:
        raise RuntimeError(
            "No order items found. "
            "Generate order items first."
        )

    records = []

    # -----------------------------------------
    # Generate returns
    # -----------------------------------------

    for item in order_items:

        # Don't normally allow returns for
        # cancelled orders.
        if item["order_status"] == "CANCELLED":
            continue

        # Invalid/zero quantities already represent
        # bad source records, so skip them here.
        if item["quantity"] <= 0:
            continue

        # Only some order items are returned.
        if not random_bool(RETURN_RATE):
            continue

        # Return quantity cannot normally exceed
        # the purchased quantity.
        return_quantity = random.randint(
            1,
            item["quantity"],
        )

        # Intentionally introduce invalid returns.
        if random_bool(
            RETURN_INVALID_QUANTITY_RATE
        ):
            return_quantity = random.choice(
                [
                    0,
                    -1,
                    item["quantity"] + 1,
                ]
            )

        return_status = weighted_choice(
            RETURN_STATUSES,
            RETURN_STATUS_WEIGHTS,
        )

        return_reason = weighted_choice(
            RETURN_REASONS,
            RETURN_REASON_WEIGHTS,
        )

        return_date = (
            item["order_date"]
            + timedelta(
                days=random.randint(
                    1,
                    MAX_RETURN_DAYS_AFTER_ORDER,
                )
            )
        )

        # Refund amount is normally based on
        # quantity returned and item unit price.
        refund_amount = round(
            return_quantity * item["unit_price"],
            2,
        )

        # A rejected/requested return may not
        # actually have a completed refund.
        if return_status in ["REQUESTED", "REJECTED"]:
            refund_amount = 0

        records.append(
            {
                "order_item_id": item["order_item_id"],
                "return_date": return_date,
                "return_reason": return_reason,
                "return_status": return_status,
                "return_quantity": return_quantity,
                "refund_amount": refund_amount,
            }
        )

    # -----------------------------------------
    # Introduce duplicate return records
    # -----------------------------------------

    duplicate_count = int(
        len(records) * RETURN_DUPLICATE_RATE
    )

    for _ in range(duplicate_count):

        duplicate = random.choice(
            records
        ).copy()

        records.append(duplicate)

    # -----------------------------------------
    # Insert records
    # -----------------------------------------

    insert_sql = text(
        """
            INSERT INTO returns (
                order_item_id,
                return_date,
                return_reason,
                return_status,
                quantity,
                refund_amount
            )
            VALUES (
                :order_item_id,
                :return_date,
                :return_reason,
                :return_status,
                :return_quantity,
                :refund_amount
            )
        """
    )

    with engine.begin() as connection:

        connection.execute(
            insert_sql,
            records,
        )

    print(
        f"Inserted {len(records):,} returns "
        f"({duplicate_count:,} duplicate records)."
    )


if __name__ == "__main__":
    generate_returns()
