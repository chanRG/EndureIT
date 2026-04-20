#!/bin/bash
# Test login script

echo "Testing EndureIT API Login"
echo "=========================="
echo ""

# Check if API is accessible
echo "1. Testing API health..."
curl -s http://localhost/api/v1/health | python3 -m json.tool 2>/dev/null || echo "API not responding"
echo ""

# Test login
echo "2. Testing login..."
echo "   Username: strava_None"
echo "   Password: EndureIT2024!"
echo ""

response=$(curl -s -X POST "http://localhost/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=strava_None&password=EndureIT2024!")

echo "Response:"
echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
echo ""

# Extract token if successful
token=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -n "$token" ]; then
    echo "✅ Login successful!"
    echo ""
    echo "Your JWT token:"
    echo "$token"
    echo ""
    echo "3. Testing Strava activities endpoint..."
    curl -s -X GET "http://localhost/api/v1/strava/activities?per_page=3" \
      -H "Authorization: Bearer $token" | python3 -m json.tool 2>/dev/null
    echo ""
    echo "✅ All tests passed!"
else
    echo "❌ Login failed"
    echo ""
    echo "Troubleshooting:"
    echo "  - Check if backend is running: docker-compose ps"
    echo "  - Check backend logs: docker-compose logs backend"
    echo "  - Verify user exists: docker-compose exec backend python -c \"from app.db.database import SessionLocal; from app.models.user import User; db = SessionLocal(); print([u.username for u in db.query(User).all()])\""
fi

