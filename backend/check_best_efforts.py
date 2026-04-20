"""
Debug script to check what best_efforts distance names exist in the cache
"""
from app.db.database import SessionLocal
from app.models.user import User
from app.models.workout import Workout, Exercise, Goal, ProgressEntry
from app.models.strava_activity import StravaActivity
from collections import Counter

db = SessionLocal()

# Get first user
user = db.query(User).first()
if not user:
    print("❌ No user found")
    exit(1)

print(f"✅ Found user: {user.username} (ID: {user.id})")

# Get all activities with best_efforts
activities = db.query(StravaActivity).filter(
    StravaActivity.user_id == user.id,
    StravaActivity.best_efforts != None
).all()

print(f"\n📊 Found {len(activities)} activities with best_efforts")

# Collect all unique distance names
all_distance_names = []
for activity in activities:
    if activity.best_efforts:
        for effort in activity.best_efforts:
            name = effort.get('name')
            if name:
                all_distance_names.append(name)

# Count occurrences
distance_counts = Counter(all_distance_names)

print(f"\n🏃 All distance names found in best_efforts:\n")
for name, count in sorted(distance_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"   '{name}': {count} occurrences")

# Check specifically for anything with "half" or "mile"
print(f"\n🔍 Distances containing 'half' or 'mile':")
for name in sorted(set(all_distance_names)):
    if 'half' in name.lower() or ('mile' in name.lower() and '1' not in name and 'k' not in name):
        print(f"   • {name}")

print(f"\n💡 Use these exact names when clicking PR cards on the dashboard")

