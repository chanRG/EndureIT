#!/bin/bash

# EndureIT Backend Setup Verification Script

echo "======================================"
echo "EndureIT Backend Setup Verification"
echo "======================================"
echo ""

# Check if .env file exists
echo "✓ Checking .env file..."
if [ -f .env ]; then
    echo "  ✅ .env file exists"
else
    echo "  ❌ .env file not found!"
    exit 1
fi

# Check if Docker is running
echo "✓ Checking Docker..."
if docker info > /dev/null 2>&1; then
    echo "  ✅ Docker is running"
else
    echo "  ❌ Docker is not running!"
    echo "  Please start Docker Desktop and try again"
    exit 1
fi

# Check if docker-compose is available
echo "✓ Checking docker-compose..."
if command -v docker-compose &> /dev/null; then
    echo "  ✅ docker-compose is installed"
else
    echo "  ❌ docker-compose not found!"
    exit 1
fi

# Check if required files exist
echo "✓ Checking project structure..."
FILES=("docker-compose.yml" "Dockerfile" "main.py" "requirements.txt" "Makefile")
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file exists"
    else
        echo "  ❌ $file not found!"
        exit 1
    fi
done

# Check app directory structure
DIRS=("app/api" "app/core" "app/db" "app/models" "app/schemas")
for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "  ✅ $dir exists"
    else
        echo "  ❌ $dir not found!"
        exit 1
    fi
done

echo ""
echo "======================================"
echo "✅ Setup verification complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Review your .env configuration"
echo "2. Run: make up-build"
echo "3. Run: make init-db"
echo "4. Visit: http://localhost/docs"
echo ""
echo "For detailed instructions, see SETUP.md"
echo ""

