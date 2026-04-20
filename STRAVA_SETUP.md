# Quick Strava Setup Guide

This is a quick start guide to set up Strava integration in EndureIT.

## Prerequisites

You need:
1. A Strava account
2. Strava API credentials (Client ID, Client Secret)
3. Strava access token and refresh token

## Step 1: Get Strava API Credentials

1. Go to https://www.strava.com/settings/api
2. Create a new application or use an existing one
3. Note your:
   - **Client ID**
   - **Client Secret**

## Step 2: Get Your Access Token

### Quick Method (Using Browser):

1. Replace `YOUR_CLIENT_ID` and visit this URL:
   ```
   https://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=http://localhost&approval_prompt=force&scope=activity:read_all,profile:read_email
   ```

2. Click "Authorize"

3. You'll be redirected to: `http://localhost/?code=AUTHORIZATION_CODE&scope=...`

4. Copy the `code` parameter value

5. Exchange the code for tokens (replace YOUR_CLIENT_ID, YOUR_CLIENT_SECRET, and AUTHORIZATION_CODE):
   ```bash
   curl -X POST https://www.strava.com/oauth/token \
     -d client_id=YOUR_CLIENT_ID \
     -d client_secret=YOUR_CLIENT_SECRET \
     -d code=AUTHORIZATION_CODE \
     -d grant_type=authorization_code
   ```

6. You'll get a JSON response with:
   ```json
   {
     "access_token": "your_access_token",
     "refresh_token": "your_refresh_token",
     "expires_at": 1234567890
   }
   ```

## Step 3: Add Credentials to .env

Edit your `.env` file in the project root and add:

```bash
# Strava API Configuration
STRAVA_CLIENT_ID=your_client_id_here
STRAVA_CLIENT_SECRET=your_client_secret_here
STRAVA_ACCESS_TOKEN=your_access_token_here
STRAVA_REFRESH_TOKEN=your_refresh_token_here
```

## Step 4: Test the Connection

Run the example script to verify your credentials work:

```bash
cd backend
python example_fetch_strava_activities.py
```

This will:
- Connect to Strava API
- Fetch your athlete profile
- Display your last 10 activities

## Step 5: Create a User with Strava Credentials

Run the user creation script:

```bash
cd backend
python create_strava_user.py
```

This will:
1. Read credentials from your .env file
2. Verify they work by connecting to Strava
3. Create a new user account with Strava integration
4. Test fetching activities

## Step 6: Use the API

1. Start the backend:
   ```bash
   make up-build
   ```

2. Login to get a JWT token:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=your_username&password=your_password"
   ```

3. Fetch activities:
   ```bash
   curl -X GET "http://localhost:8000/api/v1/strava/activities?per_page=10" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
   ```

## Available Endpoints

Once authenticated, you can access:

- `GET /api/v1/strava/activities` - Get your activities
- `GET /api/v1/strava/activity/{id}` - Get specific activity details
- `GET /api/v1/strava/athlete` - Get your athlete profile
- `GET /api/v1/strava/stats` - Get your statistics
- `GET /api/v1/strava/activity/{id}/streams` - Get detailed activity data

## Troubleshooting

### "Strava access token is required"
Make sure STRAVA_ACCESS_TOKEN is set in your .env file.

### "Rate limit exceeded"
Strava limits: 100 requests per 15 minutes, 1000 per day. Wait and try again.

### "Access token expired"
Access tokens expire after 6 hours. The system auto-refreshes them, but if it fails, generate a new token.

## Next Steps

- Read the full guide: `backend/STRAVA_INTEGRATION.md`
- Explore the API documentation: http://localhost:8000/docs
- Build features on top of the Strava data!

---

**Need help?** See `backend/STRAVA_INTEGRATION.md` for detailed documentation.

