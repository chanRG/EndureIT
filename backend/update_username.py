#!/usr/bin/env python3
"""Update username for a user."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.db.base import Base
from app.models.user import User
# Import all models to ensure they're registered
from app.models.workout import Workout, Exercise, Goal, ProgressEntry

def update_username(user_id: int, new_username: str):
    """Update username for a user."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            old_username = user.username
            user.username = new_username
            db.commit()
            print(f"✅ Username updated: '{old_username}' → '{new_username}'")
            print(f"\nLogin credentials:")
            print(f"  Username: {new_username}")
            print(f"  Password: EndureIT2024!")
            return True
        else:
            print(f"❌ User with ID {user_id} not found")
            return False
    finally:
        db.close()

if __name__ == "__main__":
    user_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    new_username = sys.argv[2] if len(sys.argv) > 2 else "roger"
    update_username(user_id, new_username)

