"""
Utility script to sync best efforts for ALL activities with achievements.
Run this once to backfill best efforts data for existing cached activities.
"""
from app.db.database import SessionLocal

# Import ALL models to ensure they are registered with SQLAlchemy
from app.models.user import User
from app.models.workout import Workout, Exercise, Goal, ProgressEntry
from app.models.strava_activity import StravaActivity
from app.services.strava_sync_service import StravaSyncService

db = SessionLocal()

# Get first user
user = db.query(User).first()
if not user:
    print("❌ No user found")
    exit(1)

print(f"✅ Found user: {user.username} (ID: {user.id})")

# Create sync service
sync_service = StravaSyncService(db, user)

# Check how many activities need best efforts
total_runs = db.query(StravaActivity).filter(
    StravaActivity.user_id == user.id,
    StravaActivity.activity_type.ilike('%run%')
).count()

activities_needing_sync = db.query(StravaActivity).filter(
    StravaActivity.user_id == user.id,
    StravaActivity.activity_type.ilike('%run%'),
    StravaActivity.best_efforts == None
).count()

activities_with_efforts = db.query(StravaActivity).filter(
    StravaActivity.user_id == user.id,
    StravaActivity.activity_type.ilike('%run%'),
    StravaActivity.best_efforts != None
).count()

print(f"\n📊 Current Status:")
print(f"   Total running activities: {total_runs}")
print(f"   Activities WITH best_efforts: {activities_with_efforts}")
print(f"   Activities NEEDING best_efforts: {activities_needing_sync}")

if activities_needing_sync == 0:
    print(f"\n✅ All running activities already have best_efforts cached!")
    print(f"   No API calls needed.")
    exit(0)

print(f"\n⚠️  This will make {activities_needing_sync} API calls to Strava")
print(f"   Fetching best_efforts for ALL runs (not just those with achievements)")
print(f"   Strava limits: 100 requests/15min, 1000/day")
response = input("\nContinue? (y/n): ")

if response.lower() != 'y':
    print("❌ Cancelled")
    exit(0)

print(f"\n🔄 Syncing best efforts for {activities_needing_sync} activities...")
print(f"   This may take a minute...\n")

try:
    updated = sync_service.sync_best_efforts(limit=None)
    print(f"\n🎉 Successfully synced best efforts for {updated} activities!")
    
    # Show final count
    final_count = db.query(StravaActivity).filter(
        StravaActivity.user_id == user.id,
        StravaActivity.best_efforts != None
    ).count()
    
    print(f"\n📊 Final Status:")
    print(f"   Total activities with best_efforts: {final_count}")
    print(f"\n💡 Now refresh your dashboard to see all your PRs!")
    
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    if "rate limit" in str(e).lower():
        print(f"\n⏰ Strava rate limit exceeded!")
        print(f"   Wait 15 minutes and run this script again.")
        print(f"   Progress has been saved - it will resume where it left off.")
    exit(1)

