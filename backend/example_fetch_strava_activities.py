#!/usr/bin/env python3
"""
Example script to fetch Strava activities using credentials from .env file.

This script demonstrates how to use the Strava service to fetch activities
without requiring a database connection.

Usage:
    1. Add Strava credentials to your .env file:
       STRAVA_CLIENT_ID=your_client_id
       STRAVA_CLIENT_SECRET=your_client_secret
       STRAVA_ACCESS_TOKEN=your_access_token
       STRAVA_REFRESH_TOKEN=your_refresh_token
    
    2. Run the script:
       python example_fetch_strava_activities.py
"""
import os
import sys
import json
from datetime import datetime, timedelta

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.strava_service import create_strava_service, StravaAPIError
from app.core.settings import settings


def format_duration(seconds):
    """Format duration in seconds to readable format."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def format_distance(meters):
    """Format distance in meters to km."""
    return f"{meters / 1000:.2f} km"


def format_speed(meters_per_second):
    """Format speed to km/h and pace (min/km)."""
    kmh = meters_per_second * 3.6
    
    if meters_per_second > 0:
        pace_seconds = 1000 / meters_per_second  # seconds per km
        pace_minutes = int(pace_seconds // 60)
        pace_secs = int(pace_seconds % 60)
        pace = f"{pace_minutes}:{pace_secs:02d} min/km"
    else:
        pace = "N/A"
    
    return f"{kmh:.1f} km/h ({pace})"


def display_activity(activity, index):
    """Display a single activity in a formatted way."""
    print(f"\n{'='*70}")
    print(f"Activity #{index}")
    print(f"{'='*70}")
    
    print(f"📝 Name:          {activity.get('name', 'Unnamed')}")
    print(f"🏃 Type:          {activity.get('type', 'Unknown')}")
    print(f"📅 Date:          {activity.get('start_date_local', activity.get('start_date', 'Unknown'))}")
    
    # Distance
    if activity.get('distance'):
        print(f"📏 Distance:      {format_distance(activity['distance'])}")
    
    # Time
    if activity.get('moving_time'):
        print(f"⏱️  Moving Time:   {format_duration(activity['moving_time'])}")
    
    if activity.get('elapsed_time'):
        print(f"⏰ Elapsed Time:  {format_duration(activity['elapsed_time'])}")
    
    # Speed
    if activity.get('average_speed'):
        print(f"🚀 Avg Speed:     {format_speed(activity['average_speed'])}")
    
    if activity.get('max_speed'):
        print(f"⚡ Max Speed:     {format_speed(activity['max_speed'])}")
    
    # Heart Rate
    if activity.get('average_heartrate'):
        print(f"❤️  Avg HR:        {activity['average_heartrate']:.0f} bpm")
    
    if activity.get('max_heartrate'):
        print(f"💗 Max HR:        {activity['max_heartrate']:.0f} bpm")
    
    # Elevation
    if activity.get('total_elevation_gain'):
        print(f"⛰️  Elevation:     {activity['total_elevation_gain']:.0f} m")
    
    # Calories
    if activity.get('calories'):
        print(f"🔥 Calories:      {activity['calories']:.0f}")
    
    # Kudos
    if activity.get('kudos_count'):
        print(f"👍 Kudos:         {activity['kudos_count']}")
    
    print(f"🔗 Strava ID:     {activity.get('id')}")


def main():
    """Main function to fetch and display Strava activities."""
    
    print("\n" + "="*70)
    print("🏃 Strava Activities Fetcher")
    print("="*70)
    
    # Check if credentials are available
    if not settings.STRAVA_ACCESS_TOKEN:
        print("\n❌ Error: STRAVA_ACCESS_TOKEN not found in environment")
        print("\nPlease add the following to your .env file:")
        print("  STRAVA_CLIENT_ID=your_client_id")
        print("  STRAVA_CLIENT_SECRET=your_client_secret")
        print("  STRAVA_ACCESS_TOKEN=your_access_token")
        print("  STRAVA_REFRESH_TOKEN=your_refresh_token")
        print("\nSee STRAVA_INTEGRATION.md for detailed setup instructions.")
        sys.exit(1)
    
    try:
        # Create Strava service
        print("\n🔌 Connecting to Strava API...")
        strava_service = create_strava_service()
        
        # Get athlete information
        print("👤 Fetching athlete information...")
        athlete = strava_service.get_athlete()
        
        print(f"\n✅ Connected as: {athlete.get('firstname', '')} {athlete.get('lastname', '')}")
        print(f"   Athlete ID: {athlete.get('id')}")
        print(f"   Username: @{athlete.get('username', 'N/A')}")
        
        # Get activities
        print("\n📋 Fetching recent activities...")
        
        # Fetch last 10 activities
        activities = strava_service.get_activities(page=1, per_page=10)
        
        if not activities:
            print("\n ℹ️  No activities found.")
            return
        
        print(f"\n✅ Found {len(activities)} recent activities")
        
        # Display activities
        for i, activity in enumerate(activities, 1):
            display_activity(activity, i)
        
        # Summary statistics
        print(f"\n{'='*70}")
        print("📊 Summary Statistics (last 10 activities)")
        print(f"{'='*70}")
        
        total_distance = sum(a.get('distance', 0) for a in activities)
        total_time = sum(a.get('moving_time', 0) for a in activities)
        total_elevation = sum(a.get('total_elevation_gain', 0) for a in activities)
        
        print(f"Total Distance:     {format_distance(total_distance)}")
        print(f"Total Moving Time:  {format_duration(total_time)}")
        print(f"Total Elevation:    {total_elevation:.0f} m")
        
        # Activity type breakdown
        activity_types = {}
        for activity in activities:
            activity_type = activity.get('type', 'Unknown')
            activity_types[activity_type] = activity_types.get(activity_type, 0) + 1
        
        print(f"\nActivity Breakdown:")
        for activity_type, count in sorted(activity_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {activity_type}: {count}")
        
        print(f"\n{'='*70}")
        print("✅ Success!")
        print(f"{'='*70}\n")
        
        # Optionally save to JSON
        save_json = input("Save activities to JSON file? (y/N): ").strip().lower()
        if save_json == 'y':
            filename = f"strava_activities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(activities, f, indent=2)
            print(f"✅ Activities saved to {filename}")
        
    except StravaAPIError as e:
        print(f"\n❌ Strava API Error: {e}")
        print("\nPossible solutions:")
        print("  1. Check that your access token is valid")
        print("  2. Ensure you have the required OAuth scopes")
        print("  3. Check if your token has expired (tokens expire after 6 hours)")
        print("  4. Try refreshing your token or generating a new one")
        print("\nSee STRAVA_INTEGRATION.md for more information.")
        sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

