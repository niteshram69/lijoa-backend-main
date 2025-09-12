from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models import Base
import os

# Select database URL. During tests (pytest) or explicit test env, use SQLite.
# Treat non-production environments as local/test by default
app_env = os.getenv("APP_ENV", settings.APP_ENV)
_is_test_env = (
    os.getenv("PYTEST_CURRENT_TEST") is not None
    or app_env.lower() in ("test", "local", "dev", "development")
)

if _is_test_env:
    database_url = "sqlite:///./test.db"
    engine = create_engine(database_url, pool_pre_ping=True, connect_args={"check_same_thread": False})
else:
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# Ensure tables exist (helps in local dev and tests)
Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

def db_ok() -> bool:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()