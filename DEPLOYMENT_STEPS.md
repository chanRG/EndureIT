# Deployment Steps for Strava Caching & Activity Details

## What's New

### 1. Database Caching for Strava Activities
- **Problem Solved**: Rate limits from fetching all activities every time
- **Solution**: Store activities in the database and only sync hourly
- **Files Added**:
  - `backend/app/models/strava_activity.py` - Database model for caching
  - `backend/app/services/strava_sync_service.py` - Sync service
  - `backend/migrations/add_strava_activities_cache.sql` - Migration script

### 2. Activity Details Modal
- **Feature**: Click any activity to view full details
- **Files Added**:
  - `frontend/src/components/ActivityDetailModal.tsx` - Modal component
- **Files Updated**:
  - `frontend/src/app/dashboard/page.tsx` - Added click handlers and modal integration

### 3. Load More Activities
- **Feature**: Pagination with "Load More" button
- **Shows**: 20 activities at a time instead of just 10
- **Files Updated**:
  - `frontend/src/app/dashboard/page.tsx` - Pagination logic

## Deployment Commands

Run these commands in order:

### 1. Create the Cache Table in Database

```bash
# Copy migration to postgres container
docker cp backend/migrations/add_strava_activities_cache.sql endureit_postgres:/tmp/

# Run the migration
docker-compose exec db psql -U endureit_user -d endureit_db -f /tmp/add_strava_activities_cache.sql
```

### 2. Restart Services

```bash
# Restart backend to load new models
docker-compose restart backend

# Restart frontend to load new components
docker-compose restart frontend
```

### 3. Test the Features

1. Visit `http://localhost:3000/dashboard`
2. **First load**: Will sync all activities from Strava (may take a moment)
3. **Subsequent loads**: Will use cached data (instant!)
4. **Click any activity**: Opens detailed modal with all stats
5. **Scroll down**: Click "Load More" to see more activities

## How Caching Works

```
First Request:
├─ Fetch all activities from Strava API
├─ Store in database (strava_activities table)
├─ Fetch details for top 20 activities with achievements
└─ Return data to frontend

Subsequent Requests (within 1 hour):
├─ Read from database (no API calls!)
└─ Return cached data instantly

After 1 Hour:
├─ Fetch only NEW activities since last sync
├─ Update database
└─ Return updated data
```

## Database Schema

The new `strava_activities` table stores:
- Basic activity info (name, type, date, distance, time)
- Heart rate data (average, max)
- Speed metrics
- Best efforts (PRs) as JSON
- Metadata (achievement count, kudos, etc.)

## API Endpoints Updated

- `/api/v1/strava/best-efforts` - Now uses cached data
  - Add `?force_sync=true` to force a fresh sync
- `/api/v1/strava/pr-history/{distance}` - Now uses cached data

## Troubleshooting

### If activities don't load:
```bash
# Check backend logs
docker-compose logs -f backend

# Manually trigger sync (in Django/Python shell if needed)
docker-compose exec backend python
>>> from app.db.database import SessionLocal
>>> from app.models.user import User
>>> from app.services.strava_sync_service import StravaSyncService
>>> db = SessionLocal()
>>> user = db.query(User).first()
>>> sync = StravaSyncService(db, user)
>>> result = sync.sync_activities()
>>> print(result)
```

### Clear cache and force resync:
```bash
# Delete cached activities
docker-compose exec db psql -U endureit_user -d endureit_db -c "DELETE FROM strava_activities;"

# Restart and reload dashboard
docker-compose restart backend
```

## Benefits

✅ **No more rate limits** - Activities stored in DB
✅ **Much faster loading** - No API calls for cached data  
✅ **Detailed activity view** - Click to see full stats
✅ **Load more activities** - Pagination for browsing history
✅ **Automatic updates** - Syncs new activities hourly
✅ **Smart syncing** - Only fetches what's new

## Next Steps

After deployment, you can:
1. Browse all your activities with pagination
2. Click any activity to see detailed stats, heart rate, best efforts, etc.
3. PRs are calculated from cached data (instant!)
4. Force a manual sync with the Refresh button if needed

