"""
Database initialization script.
Creates all tables defined in the models.
"""
from app.db.database import engine
from app.db.base import Base
from app.models.user import User  # Import all models to ensure they're registered
from app.models.workout import Workout, Exercise, Goal, ProgressEntry


def init_db() -> None:
    """Initialize database by creating all tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


def reset_db() -> None:
    """Reset database by dropping and recreating all tables."""
    print("Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database reset successfully!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        reset_db()
    else:
        init_db()
