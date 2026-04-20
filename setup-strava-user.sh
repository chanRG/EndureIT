#!/bin/bash
# Automated Strava User Setup Script
# This script automates the process of creating a user with Strava credentials

set -e  # Exit on any error

echo ""
echo "========================================================================"
echo "🏃 Strava User Setup Automation"
echo "========================================================================"
echo ""

# Check if backend container is running
if ! docker ps | grep -q endureit_backend; then
    echo "❌ Error: Backend container is not running"
    echo "   Please start it first: docker-compose up -d"
    exit 1
fi

echo "✓ Backend container is running"
echo ""

# Copy required scripts to container
echo "📦 Copying scripts to container..."
docker cp backend/create_user_with_token.py endureit_backend:/app/ 2>/dev/null || true
docker cp backend/refresh_strava_token.py endureit_backend:/app/ 2>/dev/null || true
docker cp backend/create_first_strava_user.py endureit_backend:/app/ 2>/dev/null || true
docker cp backend/app/services/strava_service.py endureit_backend:/app/app/services/ 2>/dev/null || true

echo "✓ Scripts copied"
echo ""

# Run the user creation script
echo "🚀 Creating Strava user..."
echo ""
docker-compose exec -T backend python create_user_with_token.py

echo ""
echo "========================================================================"
echo "✅ Setup Complete!"
echo "========================================================================"
echo ""
echo "Next steps:"
echo "  1. Test the API: curl http://localhost/api/v1/health"
echo "  2. Login: POST http://localhost/api/v1/auth/login"
echo "  3. Get activities: GET http://localhost/api/v1/strava/activities"
echo "  4. View API docs: http://localhost/docs"
echo ""

