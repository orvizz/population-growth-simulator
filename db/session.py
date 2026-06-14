import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

def _build_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        # Railway injects postgresql:// or postgres://; psycopg2 needs postgresql+psycopg2://
        url = url.replace("postgres://", "postgresql://", 1)
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return (
        f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
        f"@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
    )

DATABASE_URL = _build_database_url()

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
