# EndureIT Project Structure

## 📁 Root Directory Structure

```
EndureIT/
├── .git/                       # Git repository
├── .github/                    # GitHub configuration
│   └── workflows/              # CI/CD workflows
│       ├── backend-ci.yml      # Backend continuous integration
│       └── frontend-ci.yml.disabled  # Frontend CI (to enable later)
├── .dockerignore               # Docker build exclusions
├── .editorconfig               # Editor configuration for consistent formatting
├── .gitignore                  # Git ignore rules
├── README.md                   # Main project documentation
├── CONTRIBUTING.md             # Contribution guidelines
├── CODE_OF_CONDUCT.md          # Code of conduct
├── CHANGELOG.md                # Version history and changes
├── LICENSE                     # MIT License
├── Makefile                    # Project-wide commands
├── PROJECT_STRUCTURE.md        # This file - project structure
├── docker-compose.yml          # Docker orchestration for all services
│
├── backend/                    # FastAPI Backend
│   ├── app/                    # Application code
│   │   ├── api/               # API layer
│   │   │   ├── deps.py        # Dependencies (auth, db session)
│   │   │   └── v1/            # API version 1
│   │   │       ├── api.py     # Router configuration
│   │   │       └── endpoints/ # API endpoints
│   │   │           ├── auth.py        # Authentication
│   │   │           ├── users.py       # User management
│   │   │           ├── workouts.py    # Workout tracking
│   │   │           ├── goals.py       # Goal management
│   │   │           ├── progress.py    # Progress tracking
│   │   │           ├── dashboard.py   # Dashboard stats
│   │   │           └── health.py      # Health check
│   │   │
│   │   ├── core/              # Core configuration
│   │   │   ├── config.py      # Config utilities
│   │   │   ├── logging.py     # Logging setup
│   │   │   ├── security.py    # JWT & password hashing
│   │   │   └── settings.py    # Settings management
│   │   │
│   │   ├── db/                # Database layer
│   │   │   ├── base.py        # Base model class
│   │   │   ├── database.py    # DB connection & session
│   │   │   └── init_db.py     # DB initialization script
│   │   │
│   │   ├── models/            # SQLAlchemy models
│   │   │   ├── user.py        # User model
│   │   │   └── workout.py     # Workout models (4 models)
│   │   │
│   │   ├── schemas/           # Pydantic schemas
│   │   │   ├── user.py        # User schemas
│   │   │   └── workout.py     # Workout schemas (20+ schemas)
│   │   │
│   │   └── services/          # Business logic layer ⭐
│   │       ├── __init__.py
│   │       ├── workout_service.py    # Workout operations
│   │       ├── goal_service.py       # Goal operations
│   │       ├── progress_service.py   # Progress operations
│   │       └── dashboard_service.py  # Dashboard aggregation
│   │
│   ├── nginx/                 # Nginx configuration
│   │   └── nginx.conf         # Reverse proxy config
│   │
│   ├── .env                   # Environment variables (not in git)
│   ├── .env.example           # Environment template
│   ├── .gitignore             # Backend-specific ignores
│   ├── Dockerfile             # Backend container definition
│   ├── docker-compose.yml     # Backend-specific compose (legacy)
│   ├── docker-compose.override.yml  # Development overrides
│   ├── docker-compose.prod.yml      # Production overrides
│   ├── main.py                # Application entry point
│   ├── Makefile               # Backend commands
│   ├── requirements.txt       # Python dependencies
│   ├── pyproject.toml         # Python project config
│   ├── README.md              # Backend documentation
│   ├── SETUP.md               # Detailed setup guide
│   ├── QUICK_START.md         # Quick reference
│   ├── PROJECT_OVERVIEW.md    # Architecture details
│   └── verify_setup.sh        # Setup verification script
│
└── frontend/                   # Frontend Application
    └── (to be configured based on your framework choice)
```

## 🏗️ Architecture Layers

### Backend Architecture

```
┌─────────────────────────────────────────┐
│         API Layer (Endpoints)           │
│  ┌────────────────────────────────┐    │
│  │ Authentication, Workouts,      │    │
│  │ Goals, Progress, Dashboard     │    │
│  └────────────────────────────────┘    │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│      Service Layer (Business Logic)     │
│  ┌────────────────────────────────┐    │
│  │ WorkoutService, GoalService,   │    │
│  │ ProgressService, Dashboard     │    │
│  └────────────────────────────────┘    │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│     Database Layer (SQLAlchemy ORM)     │
│  ┌────────────────────────────────┐    │
│  │ User, Workout, Exercise,       │    │
│  │ Goal, ProgressEntry            │    │
│  └────────────────────────────────┘    │
└──────────────┬──────────────────────────┘
               │
               ▼
        ┌──────────────┐
        │  PostgreSQL  │
        └──────────────┘
```

## 🐳 Docker Services

```
┌─────────────────────────────────────────┐
│            Nginx (Port 80/443)          │
│         Reverse Proxy & Load Balancer   │
└──────────────┬──────────────────────────┘
               │
        ┌──────┴──────┐
        │             │
        ▼             ▼
┌──────────────┐  ┌──────────────┐
│   Backend    │  │   Frontend   │
│   (FastAPI)  │  │   (React/    │
│   Port 8000  │  │   Vue/Next)  │
└──────┬───────┘  └──────────────┘
       │
    ┌──┴──────┬──────────┐
    │         │          │
    ▼         ▼          ▼
┌────────┐ ┌──────┐  ┌───────┐
│Postgres│ │Redis │  │Nginx  │
│  5432  │ │ 6379 │  │Config │
└────────┘ └──────┘  └───────┘
```

## 📊 Database Schema

```
┌──────────────────┐
│      Users       │
│──────────────────│
│ id              ├───┐
│ email           │   │
│ username        │   │
│ password_hash   │   │
│ is_active       │   │
│ is_superuser    │   │
└──────────────────┘   │
                       │ 1:N
         ┌─────────────┼─────────────┬─────────────┐
         │             │             │             │
         ▼             ▼             ▼             ▼
┌──────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│   Workouts   │ │  Goals   │ │ Progress │ │   (future)   │
│──────────────│ │──────────│ │──────────│ │──────────────│
│ id          ├─┐│ id       │ │ id       │ │ Nutrition    │
│ user_id     │ ││ user_id  │ │ user_id  │ │ Social       │
│ title       │ ││ title    │ │ weight_kg│ │ Templates    │
│ type        │ ││ target   │ │ body_fat │ │              │
│ duration    │ ││ current  │ │ date     │ │              │
│ distance    │ ││ deadline │ │ notes    │ │              │
└─────────────┘ │└──────────┘ └──────────┘ └──────────────┘
       │ 1:N    │
       │        │
       ▼        │
┌──────────────┐│
│  Exercises   ││
│──────────────││
│ id           ││
│ workout_id  ─┘│
│ name         │
│ sets         │
│ reps         │
│ weight       │
└──────────────┘
```

## 📦 Key Files and Their Purpose

### Root Level

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Orchestrates all services (db, redis, backend, nginx, frontend) |
| `Makefile` | Project-wide commands for development |
| `README.md` | Main project documentation and quick start |
| `CONTRIBUTING.md` | Guidelines for contributors |
| `.gitignore` | Files to exclude from version control |

### Backend Core Files

| File | Purpose |
|------|---------|
| `main.py` | Application entry point, FastAPI app creation |
| `requirements.txt` | Python dependencies |
| `Dockerfile` | Backend container definition |
| `.env` | Environment variables (secrets, config) |

### Backend App Structure

| Directory | Purpose |
|-----------|---------|
| `api/` | HTTP endpoints and request handling |
| `services/` | Business logic and operations |
| `models/` | Database table definitions |
| `schemas/` | Request/response validation |
| `core/` | Configuration, security, logging |
| `db/` | Database connection and initialization |

## 🔄 Request Flow Example

### Creating a Workout

```
1. HTTP Request
   POST /api/v1/workouts
   ↓

2. API Endpoint
   endpoints/workouts.py::create_workout()
   - Validates JWT token
   - Parses request body
   ↓

3. Service Layer
   services/workout_service.py::create_workout()
   - Business logic
   - Validation
   - Calculations
   ↓

4. Database Layer
   models/workout.py::Workout
   - SQLAlchemy ORM
   - Database operations
   ↓

5. PostgreSQL
   - Stores data
   ↓

6. Response
   ← Returns WorkoutResponse schema
   ← JSON response to client
```

## 🎯 Development Workflow

### Adding a New Feature

```
1. Create/Update Model        → backend/app/models/
2. Create Pydantic Schema     → backend/app/schemas/
3. Implement Service Logic    → backend/app/services/
4. Create API Endpoints        → backend/app/api/v1/endpoints/
5. Register Router            → backend/app/api/v1/api.py
6. Reset Database             → make reset-db
7. Write Tests                → backend/tests/
8. Update Documentation       → *.md files
```

## 📚 Documentation Files

| File | Content |
|------|---------|
| `README.md` (root) | Project overview, quick start, tech stack |
| `backend/README.md` | Backend-specific documentation |
| `backend/SETUP.md` | Detailed setup and development guide |
| `backend/QUICK_START.md` | Quick reference for daily use |
| `backend/PROJECT_OVERVIEW.md` | Architecture and design details |
| `CONTRIBUTING.md` | Contribution guidelines |
| `PROJECT_STRUCTURE.md` | This file - project structure |

## 🚀 Quick Commands

```bash
# Setup and start
make setup              # Initial setup
make up-build          # Build and start all services
make init-db           # Initialize database

# Development
make logs              # View all logs
make logs-backend      # View backend logs
make shell-backend     # Access backend container
make health            # Check service health

# Database
make reset-db          # Reset database
make backup-db         # Backup database
make shell-db          # Access PostgreSQL

# Cleanup
make down              # Stop services
make clean             # Remove containers and volumes
make clean-build       # Clean and rebuild
```

## 🔐 Environment Configuration

Configuration priority:
1. Environment variables
2. `.env` file
3. Default values in `settings.py`

Key variables:
- `POSTGRES_*` - Database connection
- `SECRET_KEY` - JWT signing
- `BACKEND_CORS_ORIGINS` - CORS configuration
- `DEBUG` - Debug mode
- `ENVIRONMENT` - Environment (dev/prod)

## 📈 Current Statistics

- **Total Python Files**: 25+
- **API Endpoints**: 30+
- **Database Models**: 5
- **Pydantic Schemas**: 20+
- **Service Classes**: 4
- **Lines of Code**: 2500+
- **Docker Services**: 5
- **Supported Workout Types**: 9

## 🎯 Next Steps

1. **Frontend Setup**
   - Choose framework (React/Vue/Next.js)
   - Set up development environment
   - Connect to backend API

2. **Testing**
   - Add unit tests
   - Add integration tests
   - Set up CI/CD

3. **Features**
   - Nutrition tracking
   - Social features
   - Workout templates
   - Third-party integrations

---

**EndureIT** - Well-architected, production-ready fitness tracking platform 💪

