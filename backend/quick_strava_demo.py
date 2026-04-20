#!/usr/bin/env python3
"""
Quick Strava Demo - Demonstrates the Strava integration in action.

This script provides a simple demonstration of:
1. Connecting to Strava API
2. Fetching athlete information
3. Retrieving activities list
4. Displaying formatted results

Requirements:
    - Strava credentials in .env file (STRAVA_ACCESS_TOKEN, etc.)
    - No database connection required

Usage:
    python quick_strava_demo.py
"""
import os
import sys
from datetime import datetime

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.strava_service import create_strava_service, StravaAPIError
from app.core.settings import settings


def print_header(text):
    """Print a formatted header."""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")


def print_section(text):
    """Print a formatted section header."""
    print(f"\n{text}")
    print(f"{'-'*70}")


def demo():
    """Run the Strava integration demo."""
    
    print_header("🏃 Strava Integration Demo for EndureIT")
    
    # Check credentials
    if not settings.STRAVA_ACCESS_TOKEN:
        print("❌ Error: Strava credentials not found!")
        print("\nPlease add these to your .env file:")
        print("  STRAVA_CLIENT_ID=your_client_id")
        print("  STRAVA_CLIENT_SECRET=your_client_secret")
        print("  STRAVA_ACCESS_TOKEN=your_access_token")
        print("  STRAVA_REFRESH_TOKEN=your_refresh_token")
        print("\n📚 See STRAVA_SETUP.md for setup instructions.")
        return False
    
    try:
        # Initialize Strava service
        print("🔌 Connecting to Strava API...")
        strava = create_strava_service()
        print("✅ Connected!\n")
        
        # 1. Get Athlete Information
        print_section("👤 Athlete Profile")
        athlete = strava.get_athlete()
        
        print(f"Name:           {athlete.get('firstname', '')} {athlete.get('lastname', '')}")
        print(f"Username:       @{athlete.get('username', 'N/A')}")
        print(f"Athlete ID:     {athlete.get('id')}")
        print(f"Location:       {athlete.get('city', 'N/A')}, {athlete.get('country', 'N/A')}")
        print(f"Follower Count: {athlete.get('follower_count', 0)}")
        print(f"Friend Count:   {athlete.get('friend_count', 0)}")
        
        athlete_id = athlete.get('id')
        
        # 2. Get Athlete Statistics
        if athlete_id:
            print_section("📊 Athlete Statistics")
            stats = strava.get_athlete_stats(athlete_id)
            
            # Recent totals (last 4 weeks)
            recent = stats.get('recent_run_totals', {})
            print("\n🏃 Recent Running (Last 4 weeks):")
            print(f"  Count:       {recent.get('count', 0)} runs")
            print(f"  Distance:    {recent.get('distance', 0) / 1000:.1f} km")
            print(f"  Time:        {recent.get('moving_time', 0) / 3600:.1f} hours")
            print(f"  Elevation:   {recent.get('elevation_gain', 0):.0f} m")
            
            recent_ride = stats.get('recent_ride_totals', {})
            print("\n🚴 Recent Cycling (Last 4 weeks):")
            print(f"  Count:       {recent_ride.get('count', 0)} rides")
            print(f"  Distance:    {recent_ride.get('distance', 0) / 1000:.1f} km")
            print(f"  Time:        {recent_ride.get('moving_time', 0) / 3600:.1f} hours")
            print(f"  Elevation:   {recent_ride.get('elevation_gain', 0):.0f} m")
            
            # All-time totals
            all_time = stats.get('all_run_totals', {})
            print("\n🏆 All-Time Running:")
            print(f"  Count:       {all_time.get('count', 0)} runs")
            print(f"  Distance:    {all_time.get('distance', 0) / 1000:.1f} km")
            print(f"  Time:        {all_time.get('moving_time', 0) / 3600:.1f} hours")
        
        # 3. Get Recent Activities
        print_section("📋 Recent Activities (Last 5)")
        activities = strava.get_activities(page=1, per_page=5)
        
        if not activities:
            print("No activities found.")
        else:
            for i, activity in enumerate(activities, 1):
                print(f"\n{i}. {activity.get('name', 'Unnamed Activity')}")
                print(f"   Type:     {activity.get('type', 'Unknown')}")
                
                # Date
                start_date = activity.get('start_date_local', activity.get('start_date', ''))
                if start_date:
                    try:
                        dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                        print(f"   Date:     {dt.strftime('%Y-%m-%d %H:%M')}")
                    except:
                        print(f"   Date:     {start_date}")
                
                # Distance
                distance = activity.get('distance', 0)
                if distance > 0:
                    print(f"   Distance: {distance / 1000:.2f} km")
                
                # Time
                moving_time = activity.get('moving_time', 0)
                if moving_time > 0:
                    hours = moving_time // 3600
                    minutes = (moving_time % 3600) // 60
                    if hours > 0:
                        print(f"   Time:     {hours}h {minutes}m")
                    else:
                        print(f"   Time:     {minutes}m")
                
                # Heart rate
                avg_hr = activity.get('average_heartrate')
                if avg_hr:
                    print(f"   Avg HR:   {avg_hr:.0f} bpm")
                
                # Speed/Pace
                avg_speed = activity.get('average_speed', 0)
                if avg_speed > 0:
                    kmh = avg_speed * 3.6
                    pace_sec = 1000 / avg_speed
                    pace_min = int(pace_sec // 60)
                    pace_sec_remainder = int(pace_sec % 60)
                    print(f"   Pace:     {pace_min}:{pace_sec_remainder:02d} min/km ({kmh:.1f} km/h)")
        
        # 4. Activity Summary
        print_section("📈 Activities Summary (Last 20)")
        all_activities = strava.get_activities(page=1, per_page=20)
        
        if all_activities:
            # Calculate totals
            total_distance = sum(a.get('distance', 0) for a in all_activities)
            total_time = sum(a.get('moving_time', 0) for a in all_activities)
            total_elevation = sum(a.get('total_elevation_gain', 0) for a in all_activities)
            
            print(f"Total Activities:  {len(all_activities)}")
            print(f"Total Distance:    {total_distance / 1000:.1f} km")
            print(f"Total Time:        {total_time / 3600:.1f} hours")
            print(f"Total Elevation:   {total_elevation:.0f} m")
            
            # Activity types breakdown
            activity_types = {}
            for activity in all_activities:
                act_type = activity.get('type', 'Unknown')
                activity_types[act_type] = activity_types.get(act_type, 0) + 1
            
            print("\nActivity Types:")
            for act_type, count in sorted(activity_types.items(), key=lambda x: x[1], reverse=True):
                print(f"  {act_type}: {count}")
        
        # Success!
        print_header("✅ Demo Complete!")
        print("The Strava integration is working correctly!\n")
        print("Next steps:")
        print("  1. Run 'python create_strava_user.py' to create a user")
        print("  2. Start the backend server: 'make up-build'")
        print("  3. Login and access Strava data via API endpoints")
        print("  4. See STRAVA_INTEGRATION.md for full documentation\n")
        
        return True
        
    except StravaAPIError as e:
        print(f"\n❌ Strava API Error: {e}\n")
        print("Troubleshooting:")
        print("  • Check that your access token is valid")
        print("  • Verify you have the required OAuth scopes")
        print("  • Your token may have expired (tokens last 6 hours)")
        print("  • See STRAVA_SETUP.md for token generation\n")
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point."""
    try:
        success = demo()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo cancelled by user\n")
        sys.exit(1)


if __name__ == "__main__":
    main()

