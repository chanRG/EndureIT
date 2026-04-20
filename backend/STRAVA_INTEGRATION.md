# Strava API Integration Guide

This guide explains how to integrate Strava API with EndureIT to fetch training data.

## 🎯 Overview

The Strava integration allows users to:
- Connect their Strava account to EndureIT
- Fetch their activities (runs, rides, swims, etc.)
- Access detailed activity data including streams (heart rate, power, GPS, etc.)
- View athlete statistics and profile information

## 📋 Prerequisites

1. **Strava API Application**
   - Create a Strava API application at https://www.strava.com/settings/api
   - Note your Client ID and Client Secret
   - Set the Authorization Callback Domain

2. **Strava Access Token**
   - You need an access token and refresh token for your Strava account
   - Follow the OAuth flow or use the authorization code method

## 🔧 Setup Instructions

### Step 1: Get Strava API Credentials

1. Go to https://www.strava.com/settings/api
2. Create a new application if you haven't already
3. Note down:
   - Client ID
   - Client Secret

### Step 2: Get Access Token

You can get your access token using one of these methods:

#### Method A: Using the Authorization Code Flow (Recommended)

1. Visit this URL in your browser (replace YOUR_CLIENT_ID):
   ```
   https://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=http://localhost&approval_prompt=force&scope=activity:read_all,profile:read_email
   ```

2. Authorize the application

3. You'll be redirected to a URL like:
   ```
   http://localhost/?state=&code=AUTHORIZATION_CODE&scope=read,activity:read_all,profile:read_email
   ```

4. Copy the AUTHORIZATION_CODE from the URL

5. Exchange the code for tokens:
   ```bash
   curl -X POST https://www.strava.com/oauth/token \
     -d client_id=YOUR_CLIENT_ID \
     -d client_secret=YOUR_CLIENT_SECRET \
     -d code=AUTHORIZATION_CODE \
     -d grant_type=authorization_code
   ```

6. You'll receive a JSON response with:
   - `access_token`
   - `refresh_token`
   - `expires_at`

#### Method B: Using Existing Token

If you already have a Strava access token, you can use it directly.

### Step 3: Add Credentials to .env File

Add your Strava credentials to the root `.env` file:

```bash
# Strava API Configuration
STRAVA_CLIENT_ID=your_client_id
STRAVA_CLIENT_SECRET=your_client_secret
STRAVA_ACCESS_TOKEN=your_access_token
STRAVA_REFRESH_TOKEN=your_refresh_token
```

### Step 4: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 5: Update Database Schema

Run database migrations to add Strava fields to the User model:

```bash
# If using Alembic (recommended)
alembic revision --autogenerate -m "Add Strava fields to User model"
alembic upgrade head

# OR recreate database (development only!)
make db-reset
```

### Step 6: Create User with Strava Credentials

Run the user creation script:

```bash
cd backend
python create_strava_user.py
```

The script will:
1. Read Strava credentials from environment variables or prompt you
2. Verify the credentials by fetching your athlete profile
3. Create a user account with Strava integration
4. Optionally test the connection by fetching recent activities

## 🚀 Usage

### Start the Backend

```bash
# From project root
make up-build

# OR from backend directory
uvicorn main:app --reload
```

### API Endpoints

Once your user is created, you can access these endpoints:

#### 1. Get Activities List

```bash
GET /api/v1/strava/activities
```

Query parameters:
- `page`: Page number (default: 1)
- `per_page`: Activities per page (default: 30, max: 200)
- `after`: Unix timestamp to get activities after
- `before`: Unix timestamp to get activities before

Example:
```bash
curl -X GET "http://localhost:8000/api/v1/strava/activities?per_page=10" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### 2. Get Specific Activity

```bash
GET /api/v1/strava/activity/{activity_id}
```

Example:
```bash
curl -X GET "http://localhost:8000/api/v1/strava/activity/123456789" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### 3. Get Athlete Profile

```bash
GET /api/v1/strava/athlete
```

Example:
```bash
curl -X GET "http://localhost:8000/api/v1/strava/athlete" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### 4. Get Athlete Statistics

```bash
GET /api/v1/strava/stats
```

Returns all-time, recent, and year-to-date statistics.

#### 5. Get Activity Streams

```bash
GET /api/v1/strava/activity/{activity_id}/streams?keys=time,distance,heartrate,watts
```

Available stream types:
- `time`: Time in seconds
- `distance`: Distance in meters
- `latlng`: GPS coordinates [lat, lng]
- `altitude`: Elevation in meters
- `velocity_smooth`: Smoothed velocity
- `heartrate`: Heart rate in BPM
- `cadence`: Cadence (RPM for cycling, SPM for running)
- `watts`: Power in watts
- `temp`: Temperature in Celsius
- `moving`: Boolean for moving/not moving
- `grade_smooth`: Smoothed grade

## 🔐 Authentication Flow

1. **User Login**: Get JWT token from `/api/v1/auth/login`
2. **Use Token**: Include JWT token in Authorization header
3. **Auto Token Refresh**: The system automatically refreshes expired Strava tokens

## 📊 Example Response: Activities List

```json
[
  {
    "id": 123456789,
    "name": "Morning Run",
    "type": "Run",
    "distance": 5000.0,
    "moving_time": 1800,
    "elapsed_time": 1900,
    "total_elevation_gain": 50.0,
    "start_date": "2024-11-09T06:30:00Z",
    "average_speed": 2.78,
    "max_speed": 4.5,
    "average_heartrate": 145.0,
    "max_heartrate": 175.0,
    "elev_high": 100.0,
    "elev_low": 50.0,
    "calories": 350.0
  }
]
```

## 🔄 Token Refresh

The system automatically handles token refresh:
- When a request fails due to expired token
- The system uses the refresh_token to get a new access_token
- New tokens are saved to the database
- The original request is retried

## 🧪 Testing

### Test Script

You can test the Strava connection using the creation script:

```bash
cd backend
python create_strava_user.py
```

It will prompt to test the connection after creating the user.

### Manual Testing

```bash
# Login to get JWT token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your_username&password=your_password"

# Use the token to fetch activities
curl -X GET "http://localhost:8000/api/v1/strava/activities?per_page=5" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 📝 Database Schema

The User model includes these Strava fields:

```python
class User(Base):
    # ... existing fields ...
    
    # Strava Integration
    strava_access_token: Mapped[Optional[str]]
    strava_refresh_token: Mapped[Optional[str]]
    strava_athlete_id: Mapped[Optional[int]]
    strava_token_expires_at: Mapped[Optional[int]]
```

## 🚨 Troubleshooting

### Error: "Strava access token is required"

**Solution**: Ensure STRAVA_ACCESS_TOKEN is set in your .env file or provided during user creation.

### Error: "Rate limit exceeded"

**Solution**: Strava API has rate limits (100 requests per 15 minutes, 1000 per day). Wait before retrying.

### Error: "Access token expired or invalid"

**Solution**: The system should auto-refresh, but if it fails:
1. Generate a new access token using the authorization flow
2. Update the user's strava_access_token in the database

### Error: "User does not have Strava credentials"

**Solution**: The logged-in user doesn't have Strava tokens. Create a new user with Strava credentials or add tokens to existing user.

## 🔗 Useful Links

- [Strava API Documentation](https://developers.strava.com/docs/reference/)
- [Strava API Settings](https://www.strava.com/settings/api)
- [Strava OAuth Documentation](https://developers.strava.com/docs/authentication/)

## 💡 Tips

1. **Rate Limits**: Be mindful of Strava's rate limits (100 req/15min, 1000 req/day)
2. **Scopes**: Ensure you request appropriate OAuth scopes:
   - `activity:read_all`: Read all activities
   - `profile:read_email`: Read email address
3. **Token Expiry**: Access tokens expire in 6 hours, refresh tokens don't expire
4. **Webhook**: Consider implementing Strava webhooks for real-time updates

## 📈 Next Steps

1. **Sync Activities**: Create a background job to periodically sync activities
2. **Webhooks**: Implement Strava webhook subscriptions for real-time updates
3. **Data Storage**: Store activities in your database for offline access
4. **Analytics**: Build analytics on top of the activity data
5. **Multi-Sport Support**: Handle different activity types (Run, Ride, Swim, etc.)

---

**Happy Training! 🏃‍♂️ 🚴‍♀️ 🏊‍♂️**

