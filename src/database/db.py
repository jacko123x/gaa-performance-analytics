from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from src.settings import get_settings


settings = get_settings()
DATABASE_URL = settings.database_url

engine_options = {
    "pool_pre_ping": True,
    "pool_recycle": settings.db_pool_recycle_seconds,
    "echo": settings.sql_echo,
}
if DATABASE_URL.startswith("postgresql+psycopg://"):
    engine_options.update(
        {
            "pool_size": settings.db_pool_size,
            "max_overflow": settings.db_max_overflow,
            "connect_args": {
                "connect_timeout": settings.db_connect_timeout_seconds,
            },
        }
    )

engine = create_engine(
    DATABASE_URL,
    **engine_options,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


def test_connection():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return result.scalar()
