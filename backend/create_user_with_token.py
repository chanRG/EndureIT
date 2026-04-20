#!/usr/bin/env python3
"""
Create user with provided Strava access token.
The system will auto-refresh the token when needed.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine
from app.db.base import Base
from app.models.user import User
# Import all models to ensure they're registered with SQLAlchemy
from app.models.workout import Workout, Exercise, Goal, ProgressEntry
from app.core.security import get_password_hash
from app.services.strava_service import create_strava_service, StravaAPIError
from app.core.settings import settings

# Initial access token — loaded from env, never hardcoded
INITIAL_ACCESS_TOKEN = os.environ.get("STRAVA_ACCESS_TOKEN", "")

def main():
    print("\n" + "="*70)
    print("Creating User with Strava Token")
    print("="*70 + "\n")
    
    # Get refresh token and client credentials from env
    refresh_token = settings.STRAVA_REFRESH_TOKEN
    client_id = settings.STRAVA_CLIENT_ID
    client_secret = settings.STRAVA_CLIENT_SECRET
    
    if not refresh_token:
        print("⚠️  Warning: STRAVA_REFRESH_TOKEN not set. Auto-refresh won't work.")
    
    # Verify token by fetching athlete
    print("🔍 Verifying Strava token...")
    try:
        strava_service = create_strava_service(
            access_token=INITIAL_ACCESS_TOKEN,
            refresh_token=refresh_token
        )
        athlete = strava_service.get_athlete()
        
        print(f"✅ Token verified!")
        print(f"   Athlete: {athlete.get('firstname', '')} {athlete.get('lastname', '')}")
        print(f"   Athlete ID: {athlete.get('id')}")
        print(f"   Username: @{athlete.get('username', 'N/A')}")
        
        username = f"strava_{athlete.get('username', athlete.get('id'))}"
        email = athlete.get('email', f"athlete_{athlete.get('id')}@strava.com")
        full_name = f"{athlete.get('firstname', '')} {athlete.get('lastname', '')}".strip() or None
        strava_athlete_id = athlete.get('id')
        
    except StravaAPIError as e:
        print(f"❌ Error: {e}")
        return
    
    # Create database session
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if user exists
        existing = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing:
            print(f"\n⚠️  User already exists: {existing.username}")
            print("Updating Strava credentials...")
            existing.strava_access_token = INITIAL_ACCESS_TOKEN
            existing.strava_refresh_token = refresh_token
            existing.strava_athlete_id = strava_athlete_id
            db.commit()
            print("✅ Updated!")
            user = existing
        else:
            # Create new user
            password = "EndureIT2024!"
            user = User(
                email=email,
                username=username,
                full_name=full_name,
                hashed_password=get_password_hash(password),
                is_active=True,
                is_superuser=False,
                strava_access_token=INITIAL_ACCESS_TOKEN,
                strava_refresh_token=refresh_token,
                strava_athlete_id=strava_athlete_id,
                strava_token_expires_at=None
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            print("\n" + "="*70)
            print("✅ User Created!")
            print("="*70)
            print(f"  Username:  {user.username}")
            print(f"  Email:     {user.email}")
            print(f"  Password:  {password}")
            print(f"  Strava ID: {user.strava_athlete_id}")
            print("="*70)
        
        # Test fetching activities
        print("\n🧪 Testing activity fetch...")
        activities = strava_service.get_activities(page=1, per_page=3)
        print(f"✅ Fetched {len(activities)} activities")
        
        if activities:
            print("\nRecent activities:")
            for i, act in enumerate(activities[:3], 1):
                print(f"  {i}. {act.get('name')} - {act.get('type')}")
        
        print("\n🎉 Setup Complete!")
        print("\nThe system will auto-refresh the token when it expires.")
        print("Token refresh happens automatically via POST to:")
        print("  https://www.strava.com/api/v3/oauth/token")
        print("\nLogin with:")
        print(f"  Username: {user.username}")
        print(f"  Password: EndureIT2024!")
        print()
        
    finally:
        db.close()


if __name__ == "__main__":
    main()

