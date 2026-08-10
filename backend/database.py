import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ours_ttd.db")

# Render uses postgres://, SQLAlchemy 2.0 requires postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

def _init_engine(url: str):
    if url.startswith("postgresql"):
        try:
            eng = create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=10)
            with eng.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✓ Using PostgreSQL database")
            return eng
        except Exception as e:
            logger.warning("✗ PostgreSQL connection failed (%s). Falling back to local SQLite database.", e)
            url = "sqlite:///./ours_ttd.db"
    
    eng = create_engine(url, connect_args={"check_same_thread": False}, pool_pre_ping=True)
    logger.info("Using SQLite database (%s)", url)
    return eng

engine = _init_engine(DATABASE_URL)
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

