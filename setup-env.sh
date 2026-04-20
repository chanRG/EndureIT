#!/bin/bash

# EndureIT Environment Setup Script
# This script helps initialize environment configuration files

set -e  # Exit on error

echo "======================================"
echo "EndureIT Environment Setup"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the project root
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: This script must be run from the project root directory${NC}"
    echo "Current directory: $(pwd)"
    exit 1
fi

# Function to generate secret key
generate_secret_key() {
    openssl rand -hex 32
}

# Check for existing .env files
check_existing() {
    local has_existing=false
    
    if [ -f ".env" ]; then
        echo -e "${YELLOW}⚠️  Root .env file already exists${NC}"
        has_existing=true
    fi
    
    if [ -f "backend/.env" ]; then
        echo -e "${YELLOW}⚠️  Backend .env file already exists${NC}"
        has_existing=true
    fi
    
    if [ "$has_existing" = true ]; then
        echo ""
        read -p "Do you want to overwrite existing files? (y/N): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Setup cancelled. Your existing files are preserved."
            exit 0
        fi
    fi
}

# Create root .env
create_root_env() {
    echo ""
    echo "Setting up root .env (infrastructure configuration)..."
    
    # Copy template
    if [ ! -f ".env.example" ]; then
        echo -e "${RED}Error: .env.example not found${NC}"
        exit 1
    fi
    
    cp .env.example .env
    
    # Generate secret key
    SECRET_KEY=$(generate_secret_key)
    
    # Prompt for values or use defaults
    echo ""
    echo "Enter configuration values (press Enter for defaults):"
    echo ""
    
    read -p "Database user [endureit_user]: " DB_USER
    DB_USER=${DB_USER:-endureit_user}
    
    read -p "Database password [auto-generated]: " DB_PASSWORD
    if [ -z "$DB_PASSWORD" ]; then
        DB_PASSWORD=$(openssl rand -base64 24)
        echo "  Generated password: $DB_PASSWORD"
    fi
    
    read -p "Database name [endureit_db]: " DB_NAME
    DB_NAME=${DB_NAME:-endureit_db}
    
    read -p "Environment [development]: " ENVIRONMENT
    ENVIRONMENT=${ENVIRONMENT:-development}
    
    read -p "Debug mode [true]: " DEBUG
    DEBUG=${DEBUG:-true}
    
    # Update .env file
    sed -i.bak "s/POSTGRES_USER=.*/POSTGRES_USER=$DB_USER/" .env
    sed -i.bak "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$DB_PASSWORD/" .env
    sed -i.bak "s/POSTGRES_DB=.*/POSTGRES_DB=$DB_NAME/" .env
    sed -i.bak "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
    sed -i.bak "s/ENVIRONMENT=.*/ENVIRONMENT=$ENVIRONMENT/" .env
    sed -i.bak "s/DEBUG=.*/DEBUG=$DEBUG/" .env
    
    # Clean up backup file
    rm -f .env.bak
    
    echo -e "${GREEN}✅ Root .env created successfully${NC}"
}

# Create backend .env
create_backend_env() {
    echo ""
    echo "Setting up backend/.env (application configuration)..."
    
    if [ ! -f "backend/.env.example" ]; then
        echo -e "${RED}Error: backend/.env.example not found${NC}"
        exit 1
    fi
    
    cp backend/.env.example backend/.env
    
    # Generate another secret key for backend (though it can use root's)
    BACKEND_SECRET=$(generate_secret_key)
    sed -i.bak "s/SECRET_KEY=.*/SECRET_KEY=$BACKEND_SECRET/" backend/.env
    rm -f backend/.env.bak
    
    echo -e "${GREEN}✅ Backend .env created successfully${NC}"
}

# Display summary
show_summary() {
    echo ""
    echo "======================================"
    echo "Setup Complete! 🎉"
    echo "======================================"
    echo ""
    echo "Environment files created:"
    echo "  ✅ .env (root)"
    echo "  ✅ backend/.env"
    echo ""
    echo "Next steps:"
    echo "  1. Review and edit .env if needed:"
    echo "     ${YELLOW}nano .env${NC}"
    echo ""
    echo "  2. Start the services:"
    echo "     ${GREEN}make up-build${NC}"
    echo ""
    echo "  3. Initialize the database:"
    echo "     ${GREEN}make init-db${NC}"
    echo ""
    echo "  4. Access the API:"
    echo "     ${GREEN}http://localhost/docs${NC}"
    echo ""
    echo "For more information, see:"
    echo "  - ENV_CONFIGURATION.md"
    echo "  - README.md"
    echo ""
    echo "⚠️  Important: Never commit .env files to git!"
    echo ""
}

# Main execution
main() {
    check_existing
    create_root_env
    create_backend_env
    show_summary
}

# Run main function
main

