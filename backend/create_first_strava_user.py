#!/usr/bin/env python3
"""
Script to create the first user with Strava API credentials from .env file.

This script automatically creates a user using credentials from the environment.
It's designed for quick setup without manual prompts.

Usage:
    python create_first_strava_user.py
    
    Or provide custom values:
    python create_first_strava_user.py --username myuser --email user@example.com
"""
import os
import sys
import argparse

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine
from app.models.user import User
from app.core.security import get_password_hash
from app.services.strava_service import create_strava_service, StravaAPIError
from app.core.settings import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def create_first_user(
    username: str = None,
    email: str = None,
    password: str = None,
    full_name: str = None
) -> User:
    """Create the first user with Strava credentials from environment."""
    
    print("\n" + "="*70)
    print("Creating First User with Strava Integration")
    print("="*70 + "\n")
    
    # Get Strava credentials from environment
    strava_access_token = settings.STRAVA_ACCESS_TOKEN
    strava_refresh_token = settings.STRAVA_REFRESH_TOKEN
    
    if not strava_access_token:
        print("❌ Error: STRAVA_ACCESS_TOKEN not found in environment")
        print("\nPlease add Strava credentials to your .env file:")
        print("  STRAVA_CLIENT_ID=your_client_id")
        print("  STRAVA_CLIENT_SECRET=your_client_secret")
        print("  STRAVA_ACCESS_TOKEN=your_access_token")
        print("  STRAVA_REFRESH_TOKEN=your_refresh_token")
        sys.exit(1)
    
    # Verify Strava credentials
    print("🔍 Verifying Strava credentials...")
    try:
        strava_service = create_strava_service(
            access_token=strava_access_token,
            refresh_token=strava_refresh_token
        )
        athlete = strava_service.get_athlete()
        
        print(f"✓ Strava credentials verified!")
        print(f"  Athlete: {athlete.get('firstname', '')} {athlete.get('lastname', '')}")
        print(f"  Athlete ID: {athlete.get('id')}")
        
        strava_athlete_id = athlete.get('id')
        
        # Use athlete data for defaults if not provided
        if not username:
            username = f"strava_{athlete.get('username', athlete.get('id'))}"
        if not email:
            email = athlete.get('email', f"user_{athlete.get('id')}@strava.com")
        if not full_name:
            full_name = f"{athlete.get('firstname', '')} {athlete.get('lastname', '')}".strip() or None
        
    except StravaAPIError as e:
        print(f"⚠️  Warning: Could not verify Strava credentials: {e}")
        print("Continuing anyway...")
        strava_athlete_id = None
        
        # Use defaults if not provided
        if not username:
            username = "strava_user"
        if not email:
            email = "user@example.com"
    
    # Default password if not provided
    if not password:
        password = "EndureIT2024!"  # Default password
    
    print("\n👤 User Details:")
    print(f"  Username:   {username}")
    print(f"  Email:      {email}")
    print(f"  Full Name:  {full_name or 'Not set'}")
    print(f"  Password:   {'*' * len(password)}")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            print(f"\n⚠️  User with username '{username}' or email '{email}' already exists!")
            print(f"   Existing user ID: {existing_user.id}")
            print(f"   Username: {existing_user.username}")
            print(f"   Email: {existing_user.email}")
            
            # Update Strava credentials for existing user
            update = input("\nUpdate Strava credentials for existing user? (Y/n): ").strip().lower()
            if update != 'n':
                existing_user.strava_access_token = strava_access_token
                existing_user.strava_refresh_token = strava_refresh_token
                existing_user.strava_athlete_id = strava_athlete_id
                db.commit()
                db.refresh(existing_user)
                print("✅ Strava credentials updated!")
                return existing_user
            else:
                return existing_user
        
        # Create new user
        print("\n💾 Creating user...")
        user = User(
            email=email,
            username=username,
            full_name=full_name,
            hashed_password=get_password_hash(password),
            is_active=True,
            is_superuser=False,
            strava_access_token=strava_access_token,
            strava_refresh_token=strava_refresh_token,
            strava_athlete_id=strava_athlete_id,
            strava_token_expires_at=None
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print("\n" + "="*70)
        print("✅ User created successfully!")
        print("="*70)
        print(f"  ID:                {user.id}")
        print(f"  Username:          {user.username}")
        print(f"  Email:             {user.email}")
        print(f"  Password:          {password}")
        print(f"  Strava Athlete ID: {user.strava_athlete_id}")
        print(f"  Strava Connected:  ✓")
        print("="*70 + "\n")
        
        return user
        
    finally:
        db.close()


def test_strava_activities(user: User):
    """Test fetching Strava activities."""
    print("\n🧪 Testing Strava API - Fetching Activities...")
    print("-" * 70)
    
    try:
        strava_service = create_strava_service(
            access_token=user.strava_access_token,
            refresh_token=user.strava_refresh_token
        )
        
        activities = strava_service.get_activities(page=1, per_page=5)
        
        print(f"\n✅ Successfully fetched {len(activities)} activities!")
        
        if activities:
            print("\nRecent activities:")
            print("-" * 70)
            for i, activity in enumerate(activities, 1):
                print(f"{i}. {activity.get('name', 'Unnamed')}")
                print(f"   Type: {activity.get('type', 'Unknown')}")
                print(f"   Date: {activity.get('start_date', 'Unknown')}")
                print(f"   Distance: {activity.get('distance', 0) / 1000:.2f} km")
                print()
        
        return True
        
    except StravaAPIError as e:
        print(f"❌ Failed to fetch activities: {e}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Create first user with Strava credentials')
    parser.add_argument('--username', help='Username for the new user')
    parser.add_argument('--email', help='Email for the new user')
    parser.add_argument('--password', help='Password for the new user')
    parser.add_argument('--full-name', help='Full name for the new user')
    parser.add_argument('--skip-test', action='store_true', help='Skip Strava API test')
    
    args = parser.parse_args()
    
    # Create database tables if they don't exist
    from app.db.base import Base
    Base.metadata.create_all(bind=engine)
    
    try:
        # Create user
        user = create_first_user(
            username=args.username,
            email=args.email,
            password=args.password,
            full_name=args.full_name
        )
        
        # Test Strava connection
        if not args.skip_test:
            test_strava_activities(user)
        
        print("\n🎉 Setup complete!")
        print("\n📝 Login Credentials:")
        print(f"   Username: {user.username}")
        print(f"   Password: {args.password or 'EndureIT2024!'}")
        print("\nNext steps:")
        print("  1. Login via API: POST /api/v1/auth/login")
        print("  2. Access Strava data: GET /api/v1/strava/activities")
        print("  3. View API docs: http://localhost/docs")
        print()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

