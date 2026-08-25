import os

from dotenv import load_dotenv

load_dotenv()

# database configuration 
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")


# generator configuration 
RANDOM_SEED = 42
BATCH_SIZE = 10_000


# Development volumes
DEV_CATEGORIES = 20
DEV_PRODUCTS = 100
DEV_CUSTOMERS = 1_000
DEV_ORDERS = 10_000


# Full Volumes

FULL_CATEGORIES = 20
FULL_PRODUCTS = 5_000
FULL_CUSTOMERS = 100_000
FULL_ORDERS = 2_000_000



CUSTOMER_START_DATE = "2023-01-01"
CUSTOMER_END_DATE = "2026-08-01"


# data quality rates

CUSTOMER_DUPLICATE_RATE = 0.02
CUSTOMER_MISSING_EMAIL_RATE = 0.03
CUSTOMER_INVALID_EMAIL_RATE = 0.01
CUSTOMER_MISSING_PHONE_RATE = 0.05
CUSTOMER_CAPITALIZATION_ERROR_RATE = 0.03
CUSTOMER_WHITESPACE_ERROR_RATE = 0.022
INVALID_QUANTITY_RATE = 0.01

DUPLICATE_PAYMENT_RATE = 0.01

MISSING_TRANSACTION_REFERENCE_RATE = 0.02

LATE_ARRIVING_RATE = 0.0


# orders
ORDER_START_DATE = "2023-01-01"
ORDER_END_DATE = "2026-08-24"

ORDER_DUPLICATE_RATE = 0.01
ORDER_MISSING_CUSTOMER_RATE = 0.005
ORDER_LATE_ARRIVAL_RATE = 0.01
ORDER_UPDATED_RATE = 0.05


# order items
MIN_ITEMS_PER_ORDER = 1
MAX_ITEMS_PER_ORDER = 5

ORDER_ITEM_INVALID_QUANTITY_RATE = 0.01
ORDER_ITEM_DUPLICATE_RATE = 0.005


# Payments

PAYMENT_DUPLICATE_RATE = 0.01
PAYMENT_MISSING_REFERENCE_RATE = 0.02
PAYMENT_AMOUNT_MISMATCH_RATE = 0.01
PAYMENT_NO_PAYMENT_RATE = 0.02


# Returns

RETURN_RATE = 0.08

RETURN_INVALID_QUANTITY_RATE = 0.01

RETURN_DUPLICATE_RATE = 0.005

MAX_RETURN_DAYS_AFTER_ORDER = 60

# ==========================================
# DEVELOPMENT DATASET
# ==========================================

DEV_CATEGORIES = 20
DEV_PRODUCTS = 100
DEV_CUSTOMERS = 1_000
DEV_ORDERS = 10_000


# ==========================================
# LARGE DATASET
# ==========================================

LARGE_CATEGORIES = 20
LARGE_PRODUCTS = 5_000
LARGE_CUSTOMERS = 100_000
LARGE_ORDERS = 2_000_000


# ==========================================
# GENERATION
# ==========================================

BATCH_SIZE = 10_000

DATASET_SIZE = "large"

def get_dataset_config():
    if DATASET_SIZE == "dev":
        return {
            "categories": DEV_CATEGORIES,
            "products": DEV_PRODUCTS,
            "customers": DEV_CUSTOMERS,
            "orders": DEV_ORDERS,
        }

    if DATASET_SIZE == "large":
        return {
            "categories": LARGE_CATEGORIES,
            "products": LARGE_PRODUCTS,
            "customers": LARGE_CUSTOMERS,
            "orders": LARGE_ORDERS,
        }

    raise ValueError(
        f"Unknown DATASET_SIZE: {DATASET_SIZE}"
    )