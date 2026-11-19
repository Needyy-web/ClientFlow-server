from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
from sqlalchemy.engine import URL

load_dotenv()

user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
name = os.getenv("DB_NAME")

database_url = URL.create(
    drivername="postgresql+psycopg",
    username=user,
    password=password,
    host=host,
    port=int(port),
    database=name
)

engine = create_engine(database_url)

