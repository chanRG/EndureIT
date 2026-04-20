#!/usr/bin/env python3
"""
Script to create a user with Strava API credentials.

This script creates a user in the database with Strava authentication tokens,
allowing them to fetch training data from Strava.

Usage:
    python create_strava_user.py

Environment variables required:
    STRAVA_ACCESS_TOKEN: Your Strava access token
    STRAVA_REFRESH_TOKEN: Your Strava refresh token
    STRAVA_CLIENT_ID: Your Strava application client ID
    STRAVA_CLIENT_SECRET: Your Strava application client secret
"""
import os
import sys
from getpass import getpass

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine
from app.models.user import User
from app.core.security import get_password_hash
from app.services.strava_service import create_strava_service, StravaAPIError
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_env_or_prompt(env_var: str, prompt_text: str, secret: bool = False) -> str:
    """Get value from environment or prompt user."""
    value = os.getenv(env_var)
    if value:
        print(f"✓ Using {env_var} from environment")
        return value
    
    if secret:
        return getpass(f"{prompt_text}: ")
    else:
        return input(f"{prompt_text}: ")


def create_user_with_strava(db: Session) -> User:
    """Create a user with Strava credentials."""
    
    print("\n" + "="*60)
    print("Create User with Strava Integration")
    print("="*60 + "\n")
    
    # Get Strava credentials
    print("📍 Strava API Credentials")
    print("-" * 60)
    strava_access_token = get_env_or_prompt(
        "STRAVA_ACCESS_TOKEN",
        "Enter your Strava access token",
        secret=True
    )
    strava_refresh_token = get_env_or_prompt(
        "STRAVA_REFRESH_TOKEN",
        "Enter your Strava refresh token",
        secret=True
    )
    
    # Optional: Verify Strava credentials by fetching athlete info
    print("\n🔍 Verifying Strava credentials...")
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
        suggested_username = f"strava_{athlete.get('username', athlete.get('id'))}"
        suggested_email = athlete.get('email', '')
        
    except StravaAPIError as e:
        print(f"⚠️  Warning: Could not verify Strava credentials: {e}")
        print("Continuing anyway...")
        strava_athlete_id = None
        suggested_username = "strava_user"
        suggested_email = ""
    
    # Get user details
    print("\n👤 User Account Details")
    print("-" * 60)
    
    username = input(f"Username [{suggested_username}]: ").strip() or suggested_username
    email = input(f"Email [{suggested_email}]: ").strip() or suggested_email
    
    # Ensure email is provided
    while not email:
        email = input("Email (required): ").strip()
    
    full_name = input("Full name (optional): ").strip() or None
    password = getpass("Password: ")
    
    # Confirm password
    password_confirm = getpass("Confirm password: ")
    if password != password_confirm:
        print("❌ Passwords do not match!")
        sys.exit(1)
    
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()
    
    if existing_user:
        print(f"❌ User with username '{username}' or email '{email}' already exists!")
        sys.exit(1)
    
    # Create user
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
        strava_token_expires_at=None  # Will be updated on token refresh
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    print("\n" + "="*60)
    print("✅ User created successfully!")
    print("="*60)
    print(f"  ID: {user.id}")
    print(f"  Username: {user.username}")
    print(f"  Email: {user.email}")
    print(f"  Strava Athlete ID: {user.strava_athlete_id}")
    print(f"  Strava Connected: ✓")
    print("="*60 + "\n")
    
    return user


def test_strava_connection(user: User):
    """Test the Strava connection by fetching activities."""
    print("\n🧪 Testing Strava API connection...")
    print("-" * 60)
    
    try:
        strava_service = create_strava_service(
            access_token=user.strava_access_token,
            refresh_token=user.strava_refresh_token
        )
        
        # Fetch first page of activities
        print("Fetching recent activities...")
        activities = strava_service.get_activities(page=1, per_page=5)
        
        print(f"\n✅ Successfully fetched {len(activities)} activities!")
        
        if activities:
            print("\nRecent activities:")
            print("-" * 60)
            for i, activity in enumerate(activities, 1):
                activity_type = activity.get('type', 'Unknown')
                activity_name = activity.get('name', 'Unnamed')
                activity_date = activity.get('start_date', '')
                distance_km = activity.get('distance', 0) / 1000
                
                print(f"{i}. {activity_name}")
                print(f"   Type: {activity_type}")
                print(f"   Date: {activity_date}")
                print(f"   Distance: {distance_km:.2f} km")
                print()
        else:
            print("No activities found.")
        
        return True
        
    except StravaAPIError as e:
        print(f"❌ Failed to fetch activities: {e}")
        return False


def main():
    """Main function."""
    # Create database tables if they don't exist
    from app.db.base import Base
    Base.metadata.create_all(bind=engine)
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Create user
        user = create_user_with_strava(db)
        
        # Test Strava connection
        test_connection = input("\nTest Strava API connection? (Y/n): ").strip().lower()
        if test_connection != 'n':
            test_strava_connection(user)
        
        print("\n🎉 Setup complete!")
        print("\nNext steps:")
        print("  1. Start the backend server")
        print("  2. Login with your username and password")
        print("  3. Access Strava data via /api/v1/strava/activities")
        print()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        db.rollback()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

