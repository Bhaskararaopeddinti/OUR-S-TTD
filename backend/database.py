import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ours_ttd.db")
IS_PRODUCTION = os.getenv("RENDER") == "true" or os.getenv("ENVIRONMENT", "").lower() == "production"

def _normalize_database_url(url: str) -> str:
    """Normalize database URL for SQLAlchemy + Supabase compatibility."""
    if url.startswith("postgres://"):
        # Replace postgres:// with postgresql+psycopg2:// for proper driver specification
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://") and "+psycopg2" not in url:
        # Add psycopg2 driver if missing
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url

def _init_engine(url: str):
    # Normalize URL before processing
    url = _normalize_database_url(url)
    
    if url.startswith("postgresql"):
        try:
            # Ensure SSL is properly configured for Supabase
            if "sslmode=" not in url:
                url += "&sslmode=require" if "?" in url else "?sslmode=require"
            
            # Configure engine for Supabase/Render compatibility with psycopg2
            eng = create_engine(
                url,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
                pool_recycle=300,  # Recycle connections every 5 minutes
                connect_args={
                    "connect_timeout": 10
                }
            )
            
            # Test connection
            with eng.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✓ Using PostgreSQL database")
            return eng
        except Exception as e:
            # Provide detailed error diagnostics without exposing credentials
            error_msg = str(e)
            if "password" in error_msg.lower() or "authentication" in error_msg.lower():
                logger.error("✗ PostgreSQL authentication failed. Check DATABASE_URL credentials.")
            elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
                logger.error("✗ PostgreSQL connection failed. Database may be unreachable or firewall blocking.")
            elif "ssl" in error_msg.lower():
                logger.error("✗ PostgreSQL SSL connection failed. Check SSL configuration.")
            elif "dns" in error_msg.lower() or "host" in error_msg.lower():
                logger.error("✗ PostgreSQL hostname resolution failed. Check DATABASE_URL host.")
            else:
                logger.error(f"✗ PostgreSQL connection failed: {error_msg}")
            
            if IS_PRODUCTION:
                logger.error("Production PostgreSQL database connection failed; SQLite fallback is disabled.")
                raise RuntimeError("Production PostgreSQL database connection failed") from e
            logger.warning("Using local SQLite only because this is not production.")
            url = "sqlite:///./ours_ttd.db"
    
    eng = create_engine(url, connect_args={"check_same_thread": False}, pool_pre_ping=True)
    logger.info("Using SQLite database (%s)", url)
    return eng

class Base(DeclarativeBase):
    pass

# Initialize engine after Base is defined
engine = _init_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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

def database_kind() -> str:
    """Safe database type for health checks; never exposes connection details."""
    return "postgresql" if engine.dialect.name == "postgresql" else "sqlite"
