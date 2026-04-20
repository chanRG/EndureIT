#!/usr/bin/env python3
"""
Refresh Strava Access Token

This script refreshes your Strava access token using the refresh token.
Strava access tokens expire after 6 hours, so this helps get a fresh token.

Usage:
    python refresh_strava_token.py
    
The script will:
1. Read STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, and STRAVA_REFRESH_TOKEN from .env
2. Request a new access token from Strava
3. Display the new tokens
4. Optionally update your .env file
"""
import os
import sys
import requests
from datetime import datetime

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.settings import settings


def refresh_strava_access_token():
    """Refresh the Strava access token using the refresh token."""
    
    print("\n" + "="*70)
    print("🔄 Strava Access Token Refresh")
    print("="*70 + "\n")
    
    # Get credentials from environment
    client_id = settings.STRAVA_CLIENT_ID
    client_secret = settings.STRAVA_CLIENT_SECRET
    refresh_token = settings.STRAVA_REFRESH_TOKEN
    
    # Validate credentials
    if not client_id or not client_secret or not refresh_token:
        print("❌ Error: Missing Strava credentials in .env file\n")
        print("Required environment variables:")
        print("  - STRAVA_CLIENT_ID")
        print("  - STRAVA_CLIENT_SECRET")
        print("  - STRAVA_REFRESH_TOKEN")
        print("\nPlease add these to your .env file.")
        return None
    
    print("📋 Using credentials from .env:")
    print(f"   Client ID: {client_id[:10]}...")
    print(f"   Refresh Token: {refresh_token[:20]}...")
    
    # Prepare the request
    token_url = "https://www.strava.com/api/v3/oauth/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    
    print("\n🔌 Requesting new access token from Strava...")
    
    try:
        response = requests.post(token_url, data=payload, timeout=30)
        response.raise_for_status()
        
        token_data = response.json()
        
        print("✅ Success! Received new tokens\n")
        print("="*70)
        print("New Token Information:")
        print("="*70)
        print(f"Access Token:  {token_data['access_token']}")
        print(f"Refresh Token: {token_data['refresh_token']}")
        print(f"Expires At:    {token_data['expires_at']} ({datetime.fromtimestamp(token_data['expires_at']).strftime('%Y-%m-%d %H:%M:%S')})")
        print(f"Token Type:    {token_data.get('token_type', 'Bearer')}")
        print("="*70 + "\n")
        
        # Display athlete info if available
        if 'athlete' in token_data:
            athlete = token_data['athlete']
            print("👤 Athlete Information:")
            print(f"   Name: {athlete.get('firstname', '')} {athlete.get('lastname', '')}")
            print(f"   Username: @{athlete.get('username', 'N/A')}")
            print(f"   Athlete ID: {athlete.get('id')}")
            print()
        
        # Ask if user wants to update .env file
        print("📝 Update .env file with new tokens?")
        print("   This will update your .env file with the new access and refresh tokens.")
        update_env = input("   Update .env file? (y/N): ").strip().lower()
        
        if update_env == 'y':
            update_env_file(token_data)
        else:
            print("\n💡 To use these tokens, update your .env file manually:")
            print(f"   STRAVA_ACCESS_TOKEN={token_data['access_token']}")
            print(f"   STRAVA_REFRESH_TOKEN={token_data['refresh_token']}")
        
        return token_data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error refreshing token: {e}\n")
        
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Response: {e.response.text}")
        
        print("\nTroubleshooting:")
        print("  1. Check that your STRAVA_CLIENT_ID is correct")
        print("  2. Check that your STRAVA_CLIENT_SECRET is correct")
        print("  3. Verify your STRAVA_REFRESH_TOKEN is valid")
        print("  4. Refresh tokens don't expire, but they can be revoked")
        print("  5. You may need to re-authorize your application\n")
        
        return None


def update_env_file(token_data):
    """Update the .env file with new tokens."""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    
    if not os.path.exists(env_path):
        print(f"❌ Error: .env file not found at {env_path}")
        return
    
    try:
        # Read existing .env file
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        # Update tokens
        updated = False
        new_lines = []
        
        for line in lines:
            if line.startswith('STRAVA_ACCESS_TOKEN='):
                new_lines.append(f'STRAVA_ACCESS_TOKEN={token_data["access_token"]}\n')
                updated = True
            elif line.startswith('STRAVA_REFRESH_TOKEN='):
                new_lines.append(f'STRAVA_REFRESH_TOKEN={token_data["refresh_token"]}\n')
                updated = True
            else:
                new_lines.append(line)
        
        # Write back to file
        with open(env_path, 'w') as f:
            f.writelines(new_lines)
        
        print(f"\n✅ Updated .env file: {env_path}")
        print("   New tokens have been saved.")
        print("\n⚠️  Note: You may need to restart your backend container for changes to take effect:")
        print("   docker-compose restart backend")
        
    except Exception as e:
        print(f"\n❌ Error updating .env file: {e}")
        print("Please update manually.")


def test_new_token(access_token):
    """Test the new access token by fetching athlete data."""
    print("\n🧪 Testing new access token...")
    
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(
            "https://www.strava.com/api/v3/athlete",
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        
        athlete = response.json()
        print("✅ Token is valid!")
        print(f"   Logged in as: {athlete.get('firstname', '')} {athlete.get('lastname', '')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Token test failed: {e}")
        return False


def main():
    """Main function."""
    try:
        token_data = refresh_strava_access_token()
        
        if token_data:
            # Optionally test the new token
            test = input("\n🧪 Test the new access token? (Y/n): ").strip().lower()
            if test != 'n':
                test_new_token(token_data['access_token'])
            
            print("\n" + "="*70)
            print("✅ Token Refresh Complete!")
            print("="*70)
            print("\nNext steps:")
            print("  1. If you updated .env, restart backend: docker-compose restart backend")
            print("  2. Create user: python create_first_strava_user.py")
            print("  3. Or test connection: python quick_strava_demo.py")
            print()
            
            return 0
        else:
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user\n")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

