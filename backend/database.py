import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ours_ttd.db")

# Configure engine based on database type
if DATABASE_URL.startswith("sqlite"):
    # SQLite configuration
    connect_args = {"check_same_thread": False}
    engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
    logger.info("Using SQLite database")
elif DATABASE_URL.startswith("postgresql"):
    # PostgreSQL configuration
    connect_args = {}
    engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True, pool_size=5, max_overflow=10)
    logger.info("Using PostgreSQL database")
else:
    raise ValueError(f"Unsupported database URL scheme: {DATABASE_URL}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try: 
        yield db
    finally: 
        db.close()

def test_connection():
    """Test database connection and log results."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✓ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return False
