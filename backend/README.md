# EndureIT Backend

FastAPI backend for EndureIT - A comprehensive fitness tracking and workout management platform.

## Features

- 🔐 JWT authentication with user management
- 🏋️ Workout tracking with exercises and performance metrics
- 🎯 Goal setting and progress monitoring
- 📊 Body measurements and progress tracking
- 📈 Dashboard with aggregated statistics
- 🗄️ PostgreSQL database with SQLAlchemy ORM
- 🚀 FastAPI with auto-generated API docs
- 🐳 Docker & Docker Compose setup
- 🌐 Nginx reverse proxy
- 📦 Redis for caching

## Tech Stack

- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database operations
- **PostgreSQL** - Relational database
- **Pydantic** - Data validation
- **Docker & Docker Compose** - Containerization
- **Python 3.12+**

## Local Development

### Prerequisites

- Python 3.12+
- PostgreSQL (or use Docker)
- Docker & Docker Compose

### Setup

**Option 1: Using Docker (Recommended)**

1. **From the project root**, start all services:
   ```bash
   cd /path/to/EndureIT  # Navigate to project root
   make up-build
   ```

2. **Initialize database**:
   ```bash
   make init-db
   ```

3. **Access the API**:
   - API Documentation: http://localhost/docs
   - Alternative Docs: http://localhost/redoc
   - Health Check: http://localhost/api/v1/health

> **Note**: All Docker commands must be run from the project root, not from the backend directory.

**Option 2: Local Development (Without Docker)**

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   Create a `.env` file (see `.env.example`)

3. **Start PostgreSQL** and update DATABASE_URL in `.env`

4. **Run the server**:
   ```bash
   uvicorn main:app --reload
   ```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, access the interactive API documentation:
- Swagger UI: `http://localhost/docs`
- ReDoc: `http://localhost/redoc`

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py           # Authentication
│   │       │   ├── users.py          # User management
│   │       │   ├── workouts.py       # Workout tracking
│   │       │   ├── goals.py          # Goals management
│   │       │   ├── progress.py       # Progress tracking
│   │       │   ├── dashboard.py      # Dashboard stats
│   │       │   └── health.py         # Health check
│   │       └── api.py                # API router
│   ├── core/
│   │   ├── config.py                 # Configuration
│   │   ├── logging.py                # Logging setup
│   │   ├── security.py               # JWT & password hashing
│   │   └── settings.py               # Settings
│   ├── db/
│   │   ├── base.py                   # Base model
│   │   ├── database.py               # Database connection
│   │   └── init_db.py                # DB initialization
│   ├── models/
│   │   ├── user.py                   # User model
│   │   └── workout.py                # Workout models
│   ├── schemas/
│   │   ├── user.py                   # User schemas
│   │   └── workout.py                # Workout schemas
│   ├── services/
│   │   ├── workout_service.py        # Workout business logic
│   │   ├── goal_service.py           # Goal business logic
│   │   ├── progress_service.py       # Progress business logic
│   │   └── dashboard_service.py      # Dashboard aggregation
│   └── main.py                       # Application entry point
├── nginx/
│   └── nginx.conf                    # Nginx configuration
├── .env                              # Environment variables
├── .env.example                      # Environment template
├── docker-compose.yml                # Docker services
├── Dockerfile                        # FastAPI container
├── main.py                           # App entry point
├── Makefile                          # Convenience commands
├── requirements.txt                  # Python dependencies
├── SETUP.md                          # Detailed setup guide
└── QUICK_START.md                    # Quick reference
```

## Key Endpoints

### Authentication

- `POST /api/v1/auth/login` - Login and get JWT token
- `POST /api/v1/auth/test-token` - Test authentication

### Workouts

- `POST /api/v1/workouts` - Create new workout
- `GET /api/v1/workouts` - Get all workouts (with filters)
- `GET /api/v1/workouts/{id}` - Get specific workout
- `PUT /api/v1/workouts/{id}` - Update workout
- `DELETE /api/v1/workouts/{id}` - Delete workout
- `GET /api/v1/workouts/stats` - Get workout statistics
- `POST /api/v1/workouts/{id}/exercises` - Add exercise to workout

### Goals

- `POST /api/v1/goals` - Create new goal
- `GET /api/v1/goals` - Get all goals (with filters)
- `GET /api/v1/goals/{id}` - Get specific goal
- `PUT /api/v1/goals/{id}` - Update goal
- `PATCH /api/v1/goals/{id}/progress` - Update goal progress
- `DELETE /api/v1/goals/{id}` - Delete goal

### Progress Tracking

- `POST /api/v1/progress` - Create progress entry
- `GET /api/v1/progress` - Get all progress entries
- `GET /api/v1/progress/{id}` - Get specific entry
- `PUT /api/v1/progress/{id}` - Update entry
- `DELETE /api/v1/progress/{id}` - Delete entry
- `GET /api/v1/progress/weight/latest` - Get latest weight
- `GET /api/v1/progress/weight/change` - Get weight change

### Dashboard

- `GET /api/v1/dashboard` - Get comprehensive dashboard data

## Database Models

### Users
Stores user authentication and profile information.

### Workouts
Stores workout sessions including:
- Type (running, cycling, gym, etc.)
- Duration, distance, location
- Performance metrics (heart rate, pace, calories)
- Intensity and perceived exertion
- Related exercises

### Exercises
Individual exercises within a workout:
- Sets, reps, weight
- Duration and distance
- Exercise type and notes

### Goals
Fitness goals with:
- Target and current values
- Start and target dates
- Completion tracking

### Progress Entries
Body measurements and progress:
- Weight, body fat, muscle mass
- Body measurements (chest, waist, etc.)
- Resting heart rate
- Progress photos

## Common Commands

> **Important**: All commands must be run from the **project root directory**, not from `backend/`.

### Service Management

```bash
cd /path/to/EndureIT  # Navigate to project root

make help             # Show all available commands
make up-build         # Build and start services
make up               # Start services
make down             # Stop services
make logs             # View all logs
make logs-backend     # View backend logs only
make logs-db          # View database logs
```

### Development

```bash
make shell-backend    # Access backend container shell
make shell-db         # Access PostgreSQL shell
make health           # Check service health
```

### Database Management

```bash
make init-db          # Initialize database tables
make reset-db         # Drop and recreate all tables
make backup-db        # Backup database to SQL file
```

## Docker

Build and run with Docker:

```bash
# Development
make up-build

# Production
make build-prod
make up-prod
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PROJECT_NAME` | Application name | `EndureIT API` |
| `POSTGRES_SERVER` | PostgreSQL host | `postgres` |
| `POSTGRES_PORT` | PostgreSQL port | `5432` |
| `POSTGRES_USER` | Database user | `endureit_user` |
| `POSTGRES_PASSWORD` | Database password | (required) |
| `POSTGRES_DB` | Database name | `endureit_db` |
| `SECRET_KEY` | JWT secret key | (required) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry | `43200` |
| `BACKEND_CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000,...` |
| `DEBUG` | Debug mode | `true` |
| `LOG_LEVEL` | Logging level | `DEBUG` |

## Authentication Example

```bash
# Login
curl -X POST "http://localhost/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your_username&password=your_password"

# Use token for authenticated requests
curl -X GET "http://localhost/api/v1/dashboard" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Create a workout
curl -X POST "http://localhost/api/v1/workouts" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Morning Run",
    "workout_type": "running",
    "start_time": "2024-11-04T06:00:00",
    "duration_seconds": 1800,
    "distance_meters": 5000
  }'
```

## Testing

```bash
# Run tests (when implemented)
make test

# Run with coverage
make test-cov
```

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

2. Build and start production services:
```bash
make build-prod
make up-prod
```

3. Enable HTTPS in nginx configuration
4. Set up SSL certificates
5. Configure production database backups

## Troubleshooting

**Services won't start:**
```bash
make logs            # Check logs
make clean           # Clean and rebuild
make up-build        # Rebuild containers
```

**Database issues:**
```bash
docker-compose ps postgres    # Check PostgreSQL status
make reset-db                 # Reset database
```

**Port already in use:**
Edit `docker-compose.yml` to change port mappings.

## Documentation

- `SETUP.md` - Comprehensive setup and development guide
- `QUICK_START.md` - Quick reference for daily use
- Interactive API docs at `/docs` when running

## License

MIT License

---

**Built with the FastAPI Template**: https://github.com/chanRG/template-fastAPI.git
