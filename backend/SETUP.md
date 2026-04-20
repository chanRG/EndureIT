# EndureIT Backend Setup Guide

> **⚠️ Important**: This is part of a monorepo structure. All Docker commands must be run from the **project root** (`/path/to/EndureIT/`), not from the `backend/` directory.

## Overview

Your EndureIT backend is now configured with a production-ready FastAPI template including:

- ✅ **FastAPI** - Modern, fast Python web framework
- ✅ **PostgreSQL** - Production database
- ✅ **JWT Authentication** - Secure user authentication
- ✅ **Docker & Docker Compose** - Containerized deployment
- ✅ **Nginx** - Reverse proxy
- ✅ **Redis** - Caching layer
- ✅ **SQLAlchemy ORM** - Database models and queries

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Git (already configured)
- Make (optional, for convenience commands)

### 1. Environment Configuration

The `.env` file has been created with the following configuration:

```env
PROJECT_NAME=EndureIT API
POSTGRES_DB=endureit_db
POSTGRES_USER=endureit_user
SECRET_KEY=[auto-generated secure key]
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080
```

**⚠️ Important:** Before deploying to production, update:
- `POSTGRES_PASSWORD` - Use a strong password
- `SECRET_KEY` - Generate a new one if needed
- `BACKEND_CORS_ORIGINS` - Set to your production frontend URL

### 2. Start the Services

```bash
# Navigate to PROJECT ROOT (not backend!)
cd /Users/Roger/Projects/EndureIT

# Build and start all services
make up-build

# Initialize the database
make init-db
```

### 3. Access Your API

Once services are running:

- **API Documentation**: http://localhost/docs
- **Alternative Docs**: http://localhost/redoc
- **Health Check**: http://localhost/api/v1/health
- **API Base URL**: http://localhost/api/v1

## Project Structure

```
backend/
├── app/
│   ├── api/v1/
│   │   ├── endpoints/
│   │   │   ├── auth.py      # Authentication endpoints
│   │   │   ├── users.py     # User management
│   │   │   └── health.py    # Health check
│   │   └── api.py           # API router
│   ├── core/
│   │   ├── settings.py      # Configuration
│   │   └── security.py      # JWT & password hashing
│   ├── db/
│   │   ├── database.py      # Database connection
│   │   ├── base.py          # Base model
│   │   └── init_db.py       # DB initialization
│   ├── models/
│   │   └── user.py          # User model
│   └── schemas/
│       └── user.py          # Pydantic schemas
├── nginx/
│   └── nginx.conf           # Nginx configuration
├── .env                     # Environment variables
├── docker-compose.yml       # Docker services
├── Dockerfile               # FastAPI container
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
└── Makefile                 # Convenience commands
```

## API Endpoints

### Public Endpoints

#### Health Check
```bash
GET /api/v1/health
```

#### Login
```bash
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=your_username
password=your_password

# Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### Protected Endpoints (Require Authentication)

#### Test Token
```bash
POST /api/v1/auth/test-token
Authorization: Bearer YOUR_TOKEN_HERE
```

#### List Users (Superuser only)
```bash
GET /api/v1/users
Authorization: Bearer YOUR_TOKEN_HERE
```

#### Create User (Superuser only)
```bash
POST /api/v1/users
Authorization: Bearer YOUR_TOKEN_HERE
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "newuser",
  "password": "securepassword",
  "full_name": "John Doe",
  "is_superuser": false
}
```

## Common Commands

### Service Management

```bash
make help           # Show all available commands
make up-build       # Build and start services
make up             # Start services
make down           # Stop services
make logs           # View all logs
make logs-api       # View API logs only
make logs-db        # View database logs
make logs-nginx     # View nginx logs
```

### Development

```bash
make shell          # Access FastAPI container shell
make shell-db       # Access PostgreSQL shell
make health         # Check service health
```

### Database Management

```bash
make init-db        # Initialize database tables
make reset-db       # Drop and recreate all tables
make backup-db      # Backup database to SQL file
make restore-db file=backup.sql  # Restore from backup
```

### Cleanup

```bash
make clean          # Stop and remove containers/volumes
make clean-all      # Remove everything including images
```

## Development Workflow

### 1. Add New Endpoint

Create a new file in `app/api/v1/endpoints/`:

```python
# app/api/v1/endpoints/workouts.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db

router = APIRouter()

@router.get("/workouts")
def get_workouts(db: Session = Depends(get_db)):
    return {"workouts": []}
```

Register it in `app/api/v1/api.py`:

```python
from app.api.v1.endpoints import workouts

api_router.include_router(workouts.router, prefix="/workouts", tags=["workouts"])
```

### 2. Add New Model

Create model in `app/models/`:

```python
# app/models/workout.py
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class Workout(Base):
    __tablename__ = "workouts"
    
    name: Mapped[str] = mapped_column(nullable=False)
    duration: Mapped[int] = mapped_column(nullable=False)
```

Import it in `app/db/init_db.py`:

```python
from app.models.workout import Workout
```

Run database initialization:

```bash
make reset-db  # or make init-db if just adding new tables
```

### 3. Add Pydantic Schema

Create schema in `app/schemas/`:

```python
# app/schemas/workout.py
from pydantic import BaseModel

class WorkoutCreate(BaseModel):
    name: str
    duration: int

class WorkoutResponse(BaseModel):
    id: int
    name: str
    duration: int
    
    class Config:
        from_attributes = True
```

## Testing

### Manual Testing with cURL

```bash
# Login
curl -X POST "http://localhost/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=password"

# Use the returned token
TOKEN="your_token_here"

curl -X GET "http://localhost/api/v1/auth/test-token" \
  -H "Authorization: Bearer $TOKEN"
```

### Using the Interactive API Docs

1. Go to http://localhost/docs
2. Click "Authorize" button
3. Enter username and password
4. Click "Authorize" again
5. Now you can test all endpoints interactively!

## Database Models

### Current User Model

The template includes a User model with:

- `id` - Primary key
- `email` - Unique email address
- `username` - Unique username
- `full_name` - Optional full name
- `hashed_password` - Bcrypt hashed password
- `is_active` - Account active status
- `is_superuser` - Admin privileges

### Adding Models for EndureIT

You'll want to add models for:

- **Workouts** - Exercise sessions
- **Exercises** - Individual exercises
- **Goals** - Fitness goals
- **Progress** - Tracking metrics
- **Nutrition** - Diet tracking (if applicable)

## Security Features

### JWT Authentication

- Tokens expire after 30 days (configurable in `.env`)
- Passwords are hashed using bcrypt
- Protected endpoints require valid JWT token

### CORS Configuration

Currently configured to allow:
- http://localhost:3000 (React/Next.js default)
- http://localhost:5173 (Vite default)
- http://localhost:8080 (Vue/general dev)

Update `BACKEND_CORS_ORIGINS` in `.env` for your needs.

## Production Deployment

### Before Production

1. Update `.env` with production values:
```env
ENVIRONMENT=production
DEBUG=false
POSTGRES_PASSWORD=<strong-password>
SECRET_KEY=<new-secure-key>
BACKEND_CORS_ORIGINS=https://your-domain.com
```

2. Build production images:
```bash
make build-prod
make up-prod
```

3. Enable HTTPS in nginx configuration
4. Set up SSL certificates
5. Configure production database backups

## Troubleshooting

### Services Won't Start

```bash
# Check logs
make logs

# Clean and rebuild
make clean
make up-build
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Check database logs
make logs-db

# Reset database
make reset-db
```

### Port Already in Use

If port 80 is already in use, edit `docker-compose.yml`:

```yaml
nginx:
  ports:
    - "8080:80"  # Change 80 to another port
```

## Next Steps

### For EndureIT Fitness App

1. **Add Workout Models**
   - Create workout tracking models
   - Add exercise library
   - Implement progress tracking

2. **Add Endpoints**
   - Workout CRUD operations
   - Progress tracking endpoints
   - User dashboard data

3. **Integrate with Frontend**
   - Update CORS settings
   - Connect frontend authentication
   - Implement API calls

4. **Add Features**
   - File uploads (profile pictures, workout photos)
   - WebSocket support for real-time updates
   - Email notifications
   - Social features

## Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/
- **Pydantic Documentation**: https://docs.pydantic.dev/
- **Docker Documentation**: https://docs.docker.com/

## Support

For issues or questions:
1. Check the logs: `make logs`
2. Review the FastAPI docs at http://localhost/docs
3. Check the template repository: https://github.com/chanRG/template-fastAPI

---

**Your EndureIT backend is ready to go! 🚀**

