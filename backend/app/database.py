"""
Database configuration and connection management
PostgreSQL with SQLAlchemy
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
import logging

logger = logging.getLogger(__name__)

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL")


# Create engine
_use_nullpool = os.getenv("APP_ENV") == "testing"
_engine_kwargs = dict(
    echo=os.getenv("SQL_ECHO", "False") == "True",
    pool_pre_ping=True,
)
if _use_nullpool:
    from sqlalchemy.pool import NullPool as _NullPool
    _engine_kwargs["poolclass"] = _NullPool
else:
    _engine_kwargs["pool_size"] = 5
    _engine_kwargs["max_overflow"] = 10

try:
    engine = create_engine(DATABASE_URL, **_engine_kwargs)
    logger.info("✅ Database engine created")
except Exception as e:
    logger.error(f"❌ Failed to create database engine: {e}")
    raise

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """
    Dependency to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def test_connection():
    """
    Test database connection
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info("✅ Database connection successful")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def init_db():
    """
    Initialize database (create tables if they don't exist)
    """
    try:
        # Read schema file
        schema_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "database",
            "schema.sql"
        )
        
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as f:
                schema = f.read()
            
            # Execute schema
            with engine.connect() as connection:
                # Split by semicolon and execute each statement
                statements = schema.split(';')
                for statement in statements:
                    statement = statement.strip()
                    if statement:
                        connection.execute(text(statement))
                connection.commit()
            
            logger.info("✅ Database schema initialized")
            return True
        else:
            logger.warning("⚠️ Schema file not found")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        return False
