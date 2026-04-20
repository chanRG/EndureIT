#!/bin/bash
# Quick start script for EndureIT
# Starts both backend and frontend in Docker

set -e

echo ""
echo "========================================================================"
echo "🚀 Starting EndureIT (Backend + Frontend)"
echo "========================================================================"
echo ""

# Check if any services are already running
if docker ps | grep -q endureit; then
    echo "⚠️  Some services are already running"
    read -p "Restart all services? (y/N): " restart
    if [[ "$restart" =~ ^[Yy]$ ]]; then
        echo "🔄 Restarting services..."
        docker-compose restart
    fi
else
    echo "🚀 Starting all services..."
    docker-compose up -d
fi

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check health
echo ""
echo "🔍 Checking service status..."
docker-compose ps

echo ""
echo "========================================================================"
echo "✅ EndureIT is running!"
echo "========================================================================"
echo ""
echo "📍 Access points:"
echo "   🌐 Frontend:  http://localhost:3000"
echo "   🔌 Backend:   http://localhost/api/v1"
echo "   📚 API Docs:  http://localhost/docs"
echo ""
echo "👤 Login credentials:"
echo "   Username: roger"
echo "   Password: EndureIT2024!"
echo ""
echo "🛑 To stop: make down  or  docker-compose down"
echo ""

