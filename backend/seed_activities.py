"""
Seed script to populate strava_activities with test data
Run this while rate limited to see the dashboard features working

NOTE: This adds FAKE test data. Once rate limit resets (15 min),
click Refresh on dashboard to sync your REAL Strava activities.
"""
from datetime import datetime, timedelta
from app.db.database import SessionLocal
from app.models.user import User
from app.models.strava_activity import StravaActivity

db = SessionLocal()

# Get first user
user = db.query(User).first()
if not user:
    print("❌ No user found")
    exit(1)

print(f"✅ Found user: {user.username} (ID: {user.id})")

# Check if activities already exist
existing = db.query(StravaActivity).filter(StravaActivity.user_id == user.id).count()
if existing > 0:
    print(f"ℹ️  {existing} activities already in cache")
    print("⚠️  This will DELETE existing cached data and add fake test data")
    response = input("Continue? (y/n): ")
    if response.lower() == 'y':
        db.query(StravaActivity).filter(StravaActivity.user_id == user.id).delete()
        db.commit()
        print("✅ Cleared existing activities")
    else:
        print("❌ Cancelled")
        exit(0)

# Create test activities with realistic best_efforts
# November 1st 5k PR
nov_1st = datetime(2024, 11, 1, 7, 30, 0)

test_activities = [
    {
        'strava_id': 10000001,
        'name': '5K PR Run - November 1st',
        'activity_type': 'Run',
        'distance': 5000,
        'moving_time': 1200,  # 20:00 (4:00/km pace)
        'elapsed_time': 1230,
        'start_date': nov_1st,
        'start_date_local': nov_1st,
        'total_elevation_gain': 30,
        'average_heartrate': 165,
        'max_heartrate': 182,
        'has_heartrate': True,
        'average_speed': 4.17,  # 4:00/km pace
        'max_speed': 5.0,
        'achievement_count': 3,
        'kudos_count': 15,
        'best_efforts': [
            {
                'name': '400m',
                'distance': 400,
                'elapsed_time': 72,
                'moving_time': 72,
                'start_date': nov_1st.isoformat() + 'Z',
                'start_date_local': nov_1st.isoformat(),
                'pr_rank': 1
            },
            {
                'name': '1k',
                'distance': 1000,
                'elapsed_time': 240,
                'moving_time': 240,
                'start_date': nov_1st.isoformat() + 'Z',
                'start_date_local': nov_1st.isoformat(),
                'pr_rank': 1
            },
            {
                'name': '1 mile',
                'distance': 1609,
                'elapsed_time': 387,
                'moving_time': 387,
                'start_date': nov_1st.isoformat() + 'Z',
                'start_date_local': nov_1st.isoformat(),
                'pr_rank': 1
            },
            {
                'name': '5k',
                'distance': 5000,
                'elapsed_time': 1200,
                'moving_time': 1200,
                'start_date': nov_1st.isoformat() + 'Z',
                'start_date_local': nov_1st.isoformat(),
                'pr_rank': 1
            }
        ]
    },
    {
        'strava_id': 10000002,
        'name': '10K Long Run',
        'activity_type': 'Run',
        'distance': 10000,
        'moving_time': 2700,  # 45:00
        'elapsed_time': 2760,
        'start_date': datetime(2024, 10, 28, 8, 0, 0),
        'start_date_local': datetime(2024, 10, 28, 8, 0, 0),
        'total_elevation_gain': 85,
        'average_heartrate': 155,
        'max_heartrate': 172,
        'has_heartrate': True,
        'average_speed': 3.70,  # 4:30/km pace
        'max_speed': 4.5,
        'achievement_count': 2,
        'kudos_count': 8,
        'best_efforts': [
            {
                'name': '10k',
                'distance': 10000,
                'elapsed_time': 2700,
                'moving_time': 2700,
                'start_date': datetime(2024, 10, 28, 8, 0, 0).isoformat() + 'Z',
                'start_date_local': datetime(2024, 10, 28, 8, 0, 0).isoformat(),
                'pr_rank': 1
            }
        ]
    },
    {
        'strava_id': 10000003,
        'name': 'Easy Recovery 5k',
        'activity_type': 'Run',
        'distance': 5000,
        'moving_time': 1500,  # 25:00 (5:00/km - slower than PR)
        'elapsed_time': 1560,
        'start_date': datetime(2024, 10, 25, 7, 15, 0),
        'start_date_local': datetime(2024, 10, 25, 7, 15, 0),
        'total_elevation_gain': 20,
        'average_heartrate': 142,
        'max_heartrate': 158,
        'has_heartrate': True,
        'average_speed': 3.33,  # 5:00/km pace
        'max_speed': 4.0,
        'achievement_count': 0,
        'kudos_count': 3,
        'best_efforts': [
            {
                'name': '5k',
                'distance': 5000,
                'elapsed_time': 1500,
                'moving_time': 1500,
                'start_date': datetime(2024, 10, 25, 7, 15, 0).isoformat() + 'Z',
                'start_date_local': datetime(2024, 10, 25, 7, 15, 0).isoformat(),
                'pr_rank': None
            }
        ]
    },
    {
        'strava_id': 10000004,
        'name': 'Half Marathon',
        'activity_type': 'Run',
        'distance': 21097,
        'moving_time': 5400,  # 1:30:00
        'elapsed_time': 5520,
        'start_date': datetime(2024, 10, 20, 7, 0, 0),
        'start_date_local': datetime(2024, 10, 20, 7, 0, 0),
        'total_elevation_gain': 150,
        'average_heartrate': 160,
        'max_heartrate': 178,
        'has_heartrate': True,
        'average_speed': 3.91,  # 4:16/km pace
        'max_speed': 4.8,
        'achievement_count': 4,
        'kudos_count': 25,
        'best_efforts': [
            {
                'name': '10k',
                'distance': 10000,
                'elapsed_time': 2560,
                'moving_time': 2560,
                'start_date': datetime(2024, 10, 20, 7, 0, 0).isoformat() + 'Z',
                'start_date_local': datetime(2024, 10, 20, 7, 0, 0).isoformat(),
                'pr_rank': 2
            },
            {
                'name': 'Half-Marathon',
                'distance': 21097,
                'elapsed_time': 5400,
                'moving_time': 5400,
                'start_date': datetime(2024, 10, 20, 7, 0, 0).isoformat() + 'Z',
                'start_date_local': datetime(2024, 10, 20, 7, 0, 0).isoformat(),
                'pr_rank': 1
            }
        ]
    },
]

# Insert activities
for data in test_activities:
    best_efforts = data.pop('best_efforts', None)
    start_date = data.pop('start_date')
    start_date_local = data.pop('start_date_local')
    
    activity = StravaActivity(
        user_id=user.id,
        start_date=start_date,
        start_date_local=start_date_local,
        last_synced=datetime.utcnow(),
        best_efforts=best_efforts,
        **data
    )
    db.add(activity)
    print(f"✅ Added: {data['name']}")

db.commit()
print(f"\n🎉 Successfully seeded {len(test_activities)} test activities with PRs!")
print(f"\n📊 Test PRs included:")
print(f"   - 5k: 20:00 (Nov 1st) ⭐ PR")
print(f"   - 10k: 45:00 (Oct 28th)")
print(f"   - Half Marathon: 1:30:00 (Oct 20th)")
print(f"\n⚠️  This is FAKE test data!")
print(f"💡 Once Strava rate limit resets (~15 min), click Refresh to get your REAL data")
print(f"\n🌐 Visit http://localhost:3000/dashboard")

