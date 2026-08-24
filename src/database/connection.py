import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

print("ENV HOST:", os.getenv("POSTGRES_HOST"))
print("ENV DB:", os.getenv("POSTGRES_DB"))
print("ENV USER:", os.getenv("POSTGRES_USER"))
print("ENV PASSWORD:", os.getenv("POSTGRES_PASSWORD"))

POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")


DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)


engine = create_engine(DATABASE_URL)

if __name__ == "__main__":
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT current_database(), current_user")
        )

        database, user = result.fetchone()

        print(f"Database:{database}")
        print(f"User:{user}")

