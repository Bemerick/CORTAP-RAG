"""Database connection management."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
from typing import Generator

from .models import Base


class DatabaseManager:
    """Manage database connections and sessions."""

    def __init__(self, database_url: str = None):
        """
        Initialize database manager.

        Args:
            database_url: PostgreSQL connection string
                         Format: postgresql://user:password@host:port/dbname
        """
        self.database_url = database_url or os.getenv(
            'DATABASE_URL',
            'postgresql://localhost:5432/cortap_compliance'
        )

        # Create engine with connection pooling
        # Use NullPool for serverless/short-lived connections
        # Use default pool for long-running applications
        poolclass = NullPool if os.getenv('SERVERLESS') else None

        self.engine = create_engine(
            self.database_url,
            poolclass=poolclass,
            echo=bool(os.getenv('SQL_DEBUG')),  # Set SQL_DEBUG=1 to see SQL queries
        )

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

    def create_tables(self):
        """Create all tables in the database."""
        Base.metadata.create_all(bind=self.engine)
        print("✅ Database tables created successfully")

    def drop_tables(self):
        """Drop all tables in the database. USE WITH CAUTION!"""
        Base.metadata.drop_all(bind=self.engine)
        print("⚠️  All database tables dropped")

    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope around a series of operations.

        Usage:
            with db_manager.session_scope() as session:
                section = ComplianceSection(...)
                session.add(section)
                # Automatically commits on success, rolls back on error
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            from sqlalchemy import text
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False


# Singleton instance
_db_manager = None


def get_db_manager(database_url: str = None) -> DatabaseManager:
    """Get or create the singleton database manager."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(database_url)
    return _db_manager
