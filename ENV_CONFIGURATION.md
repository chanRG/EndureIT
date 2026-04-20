# Environment Configuration Guide

This guide explains how environment variables are organized in the EndureIT monorepo.

## 📁 Environment File Structure

```
EndureIT/
├── .env                    # Root: Infrastructure config (gitignored)
├── .env.example            # Root: Infrastructure template (in git)
├── backend/
│   ├── .env               # Backend: App-specific config (gitignored)
│   └── .env.example       # Backend: App template (in git)
└── frontend/
    ├── .env               # Frontend: App config (gitignored, when added)
    └── .env.example       # Frontend: Template (in git, when added)
```

## 🎯 Purpose of Each File

### Root `.env` (Infrastructure Level)
**Location**: `/EndureIT/.env`  
**Purpose**: Shared configuration for docker-compose services  
**Used by**: docker-compose.yml  
**Contains**:
- Database credentials (POSTGRES_*)
- Redis configuration
- Shared secrets (SECRET_KEY)
- Environment settings (ENVIRONMENT, DEBUG)
- CORS origins

**Example**:
```env
POSTGRES_USER=endureit_user
POSTGRES_PASSWORD=my_secure_password
POSTGRES_DB=endureit_db
SECRET_KEY=abc123...
BACKEND_CORS_ORIGINS=http://localhost:3000
ENVIRONMENT=development
DEBUG=true
```

### Root `.env.example` (Template)
**Location**: `/EndureIT/.env.example`  
**Purpose**: Template showing what infrastructure variables are needed  
**Status**: ✅ Committed to git  
**Used by**: Developers setting up the project  

### Backend `.env` (Application Level)
**Location**: `/EndureIT/backend/.env`  
**Purpose**: Backend-specific configuration  
**Used by**: FastAPI application  
**Contains**:
- API configuration (PROJECT_NAME, VERSION)
- Backend-specific settings
- Can reference root .env variables
- Additional backend-only settings

**Example**:
```env
PROJECT_NAME=EndureIT API
VERSION=1.0.0
API_V1_STR=/api/v1
ACCESS_TOKEN_EXPIRE_MINUTES=43200
LOG_LEVEL=DEBUG
```

### Backend `.env.example` (Template)
**Location**: `/EndureIT/backend/.env.example`  
**Purpose**: Template for backend-specific variables  
**Status**: ✅ Committed to git  

## 🔄 How They Work Together

### 1. Docker Compose Setup
```bash
# docker-compose.yml reads from root .env
POSTGRES_USER=${POSTGRES_USER:-endureit_user}
SECRET_KEY=${SECRET_KEY:-default}
```

### 2. Backend Application
The backend can access variables from:
- Docker Compose environment variables (passed through)
- Its own backend/.env file
- Environment variables set in docker-compose.yml

### 3. Variable Precedence
```
1. Docker Compose environment section (highest priority)
2. Root .env file
3. Default values in docker-compose.yml (lowest priority)
```

## 📋 Setup Instructions

### First Time Setup

```bash
# 1. Navigate to project root
cd /path/to/EndureIT

# 2. Copy root environment template
cp .env.example .env

# 3. Copy backend environment template
cp backend/.env.example backend/.env

# 4. Generate a secure secret key
openssl rand -hex 32

# 5. Edit root .env with your values
nano .env
# or
code .env

# 6. Edit backend .env if needed
nano backend/.env

# 7. Start services
make up-build
```

### Quick Setup (uses defaults)
```bash
cp .env.example .env
cp backend/.env.example backend/.env
# Edit .env with at least: POSTGRES_PASSWORD and SECRET_KEY
make up-build
```

## 🔐 Security Best Practices

### ✅ DO
- ✅ Keep `.env` files in `.gitignore`
- ✅ Commit `.env.example` files to git
- ✅ Use strong passwords and keys
- ✅ Generate unique SECRET_KEY for each environment
- ✅ Use different credentials for dev/staging/production
- ✅ Rotate secrets periodically

### ❌ DON'T
- ❌ Never commit actual `.env` files
- ❌ Never hardcode secrets in code
- ❌ Never use default passwords in production
- ❌ Never share `.env` files via email/chat
- ❌ Never commit secrets to version control

## 📝 Variable Reference

### Root `.env` Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `POSTGRES_USER` | Yes | endureit_user | Database username |
| `POSTGRES_PASSWORD` | Yes | *(must set)* | Database password |
| `POSTGRES_DB` | Yes | endureit_db | Database name |
| `SECRET_KEY` | Yes | *(must generate)* | JWT signing key |
| `BACKEND_CORS_ORIGINS` | No | localhost URLs | Allowed CORS origins |
| `ENVIRONMENT` | No | development | Environment name |
| `DEBUG` | No | true | Debug mode |

### Backend `.env` Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PROJECT_NAME` | No | EndureIT API | API project name |
| `VERSION` | No | 1.0.0 | API version |
| `API_V1_STR` | No | /api/v1 | API prefix |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | 43200 | JWT expiration (30 days) |
| `LOG_LEVEL` | No | DEBUG | Logging level |

## 🌍 Environment-Specific Configuration

### Development
```env
# Root .env
ENVIRONMENT=development
DEBUG=true
POSTGRES_PASSWORD=dev_password
SECRET_KEY=dev_secret_key

# Backend .env
LOG_LEVEL=DEBUG
ACCESS_TOKEN_EXPIRE_MINUTES=43200
```

### Production
```env
# Root .env
ENVIRONMENT=production
DEBUG=false
POSTGRES_PASSWORD=strong_random_password_here
SECRET_KEY=unique_production_secret_key_here
BACKEND_CORS_ORIGINS=https://endureit.com

# Backend .env
LOG_LEVEL=INFO
ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 7 days
```

## 🔧 Troubleshooting

### Problem: Variables not being read
**Solution**:
```bash
# Check if .env exists
ls -la .env backend/.env

# Verify docker-compose picks up variables
docker-compose config | grep POSTGRES_USER

# Restart services to reload environment
make down
make up
```

### Problem: Database connection fails
**Check**:
1. Root `.env` has correct POSTGRES_* variables
2. Backend can reach database (check docker network)
3. Credentials match in both root and backend .env

### Problem: CORS errors
**Solution**:
```bash
# Update root .env with correct frontend URL
BACKEND_CORS_ORIGINS=http://localhost:3000,https://your-domain.com

# Restart backend
docker-compose restart backend
```

## 📖 Examples

### Example Root `.env` (Development)
```env
# Database
POSTGRES_USER=endureit_dev
POSTGRES_PASSWORD=dev_secure_password_123
POSTGRES_DB=endureit_dev_db

# Security
SECRET_KEY=cbbb76fbd9301edd5184b42b779572b448475b9ecbac983a773b12cb91c4811a

# CORS
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Environment
ENVIRONMENT=development
DEBUG=true
```

### Example Backend `.env` (Development)
```env
# API Configuration
PROJECT_NAME=EndureIT API
VERSION=1.0.0
DESCRIPTION=EndureIT Fitness Tracking Application API
API_V1_STR=/api/v1

# Database (inherits from docker-compose)
POSTGRES_SERVER=db
POSTGRES_PORT=5432
# POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB set by docker-compose

# Security (inherits SECRET_KEY from docker-compose)
ACCESS_TOKEN_EXPIRE_MINUTES=43200
ALGORITHM=HS256

# CORS (inherits from docker-compose)
# BACKEND_CORS_ORIGINS set by docker-compose

# Redis
REDIS_URL=redis://redis:6379

# Environment (inherits from docker-compose)
# ENVIRONMENT and DEBUG set by docker-compose
LOG_LEVEL=DEBUG

# Email (optional)
SMTP_TLS=true
SMTP_PORT=587
SMTP_HOST=
SMTP_USER=
SMTP_PASSWORD=
EMAILS_FROM_EMAIL=
EMAILS_FROM_NAME=EndureIT
```

## 🎯 Key Takeaways

1. **Root `.env`** is for infrastructure (Docker Compose, databases, shared secrets)
2. **Backend `.env`** is for application-specific settings
3. Never commit actual `.env` files to git
4. Always commit `.env.example` templates
5. Use strong, unique passwords and keys
6. Different configurations for dev/staging/production

## 🔗 Related Files

- `.env.example` - Root environment template
- `backend/.env.example` - Backend template
- `docker-compose.yml` - Uses root .env
- `.gitignore` - Ignores all .env files
- `backend/app/core/settings.py` - Reads environment variables

---

**Remember**: Never share or commit your actual `.env` files! 🔒

