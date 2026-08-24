import random
from datetime import datetime, timedelta

from faker import Faker
from sqlalchemy import create_engine

from src.generator.config import (
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
)


fake= Faker()


def create_database_engine():
    """create and return a database engine"""

    database_url = (f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")

    return create_engine(database_url, pool_pre_ping=True)


def initialize_random_seed(seed:int) -> None:
    """Initialize deterministic random generation"""
    random.seed(seed)
    Faker.seed(seed)


def random_datetime(start:datetime, end:datetime)-> datetime:
    """Generate a random datetime betwee start and end"""

    delta = end - start

    random_seconds = random.randint(0,int(delta.total_seconds()))

    return start+timedelta(seconds=random_seconds)


def weighted_choice(options:list, weights:list):
    """Select an item from options based on weighted probabilities"""
    return random.choices(options, weights=weights, k=1)[0]


def random_bool(probability:float) -> bool:
    """Random True based on the supplied probability"""
    return random.random()< probability


def batch_records(records, batch_size: int):
    """
    Yield records in batches.
    """

    for start in range(0, len(records), batch_size):
        yield records[start:start + batch_size]