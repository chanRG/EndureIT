# EndureIT

A comprehensive fitness tracking and workout management platform built with FastAPI (backend) and modern frontend technologies.

## 🎯 Overview

EndureIT helps users track their fitness journey with features for:
- 🏋️ **Workout Tracking** - Log exercises with detailed metrics
- 🎯 **Goal Setting** - Set and track fitness goals
- 📊 **Progress Monitoring** - Track body measurements and weight
- 📈 **Analytics Dashboard** - Visualize your fitness progress
- 🔐 **Secure Authentication** - JWT-based user management

## 🏗️ Project Structure

```
EndureIT/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Configuration
│   │   ├── db/          # Database
│   │   ├── models/      # SQLAlchemy models
│   │   ├── schemas/     # Pydantic schemas
│   │   └── services/    # Business logic
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md        # Backend documentation
├── frontend/            # Frontend application
│   └── (your frontend framework)
├── docker-compose.yml   # Docker orchestration
├── .gitignore
└── README.md           # This file
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Git

### Installation

#### Option 1: Automated Setup (Recommended)

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd EndureIT
   ```

2. **Run the setup script**
   ```bash
   ./setup-env.sh
   ```
   This will:
   - Create `.env` files from templates
   - Generate secure SECRET_KEY
   - Prompt for database credentials
   - Set up configuration

3. **Start all services**
   ```bash
   make up-build
   ```

4. **Initialize the database**
   ```bash
   make init-db
   ```

5. **Access the application**
   - **API Documentation**: http://localhost/docs
   - **API Base URL**: http://localhost/api/v1
   - **Frontend**: http://localhost:3000 (when configured)

#### Option 2: Manual Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd EndureIT
   ```

2. **Set up environment variables**
   ```bash
   # Copy root environment template
   cp .env.example .env
   
   # Copy backend environment template
   cp backend/.env.example backend/.env
   
   # Generate a secure SECRET_KEY
   openssl rand -hex 32
   
   # Edit .env with your configuration
   # At minimum, set: POSTGRES_PASSWORD and SECRET_KEY
   nano .env
   ```

3. **Start all services**
   ```bash
   make up-build
   ```

4. **Initialize the database**
   ```bash
   make init-db
   ```

5. **Access the application**
   - **API Documentation**: http://localhost/docs
   - **API Base URL**: http://localhost/api/v1
   - **Frontend**: http://localhost:3000 (when configured)

> **📖 For detailed environment configuration, see [ENV_CONFIGURATION.md](./ENV_CONFIGURATION.md)**

## 🐳 Docker Services

The application consists of the following services:

| Service | Description | Port | Container Name |
|---------|-------------|------|----------------|
| **db** | PostgreSQL database | 5432 | endureit_postgres |
| **redis** | Redis cache | 6379 | endureit_redis |
| **backend** | FastAPI application | 8000 (internal) | endureit_backend |
| **nginx** | Reverse proxy | 80, 443 | endureit_nginx |
| **frontend** | Frontend app | 3000 | endureit_frontend |

## 📚 Documentation

### Backend
- [Backend README](./backend/README.md) - Complete backend documentation
- [Setup Guide](./backend/SETUP.md) - Detailed setup instructions
- [Quick Start](./backend/QUICK_START.md) - Quick reference
- [Project Overview](./backend/PROJECT_OVERVIEW.md) - Architecture details

### API Documentation
Once running, interactive API docs are available at:
- **Swagger UI**: http://localhost/docs
- **ReDoc**: http://localhost/redoc

## 🔧 Common Commands

### Start/Stop Services

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Backend Development

```bash
# Access backend shell
docker-compose exec backend /bin/bash

# Initialize database
docker-compose exec backend python app/db/init_db.py

# Reset database
docker-compose exec backend python app/db/init_db.py reset

# Access PostgreSQL
docker-compose exec db psql -U endureit_user -d endureit_db
```

### Database Management

```bash
# Backup database
docker-compose exec db pg_dump -U endureit_user endureit_db > backup.sql

# Restore database
docker-compose exec -T db psql -U endureit_user endureit_db < backup.sql
```

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - SQL toolkit and ORM
- **PostgreSQL** - Relational database
- **Redis** - Caching and session storage
- **Pydantic** - Data validation
- **JWT** - Authentication
- **Nginx** - Reverse proxy

### Frontend
- **[Your Framework]** - React/Vue/Angular/Next.js/etc.
- **[State Management]** - Redux/Vuex/Zustand/etc.
- **[UI Library]** - Material-UI/Tailwind/etc.

## 🔐 Environment Variables

EndureIT uses a layered environment configuration:

### Root `.env` (Infrastructure)
Contains shared configuration for Docker Compose services:
```env
POSTGRES_USER=endureit_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=endureit_db
SECRET_KEY=your_generated_secret_key
BACKEND_CORS_ORIGINS=http://localhost:3000
ENVIRONMENT=development
DEBUG=true
```

### Backend `.env` (Application)
Contains backend-specific settings:
```env
PROJECT_NAME=EndureIT API
VERSION=1.0.0
API_V1_STR=/api/v1
ACCESS_TOKEN_EXPIRE_MINUTES=43200
LOG_LEVEL=DEBUG
```

### Quick Setup
```bash
# Automated (recommended)
./setup-env.sh

# Or manual
cp .env.example .env
cp backend/.env.example backend/.env
# Edit .env files with your values
```

Generate a secure secret key:
```bash
openssl rand -hex 32
```

**📖 For complete environment configuration guide, see [ENV_CONFIGURATION.md](./ENV_CONFIGURATION.md)**

## 🎨 Features

### Implemented
- ✅ User authentication and authorization
- ✅ Workout tracking with exercises
- ✅ Multiple workout types (Running, Cycling, Gym, etc.)
- ✅ Goal setting and tracking
- ✅ Progress monitoring (weight, body measurements)
- ✅ Dashboard with statistics
- ✅ REST API with full documentation

### Planned
- 🔄 Nutrition tracking
- 🔄 Social features (follow users, share workouts)
- 🔄 Workout templates and programs
- 🔄 Third-party integrations (Strava, Fitbit)
- 🔄 Mobile app
- 🔄 Export/import data

## 📊 API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/test-token` - Validate token

### Workouts
- `POST /api/v1/workouts` - Create workout
- `GET /api/v1/workouts` - List workouts
- `GET /api/v1/workouts/{id}` - Get workout details
- `PUT /api/v1/workouts/{id}` - Update workout
- `DELETE /api/v1/workouts/{id}` - Delete workout
- `GET /api/v1/workouts/stats` - Get statistics

### Goals
- `POST /api/v1/goals` - Create goal
- `GET /api/v1/goals` - List goals
- `GET /api/v1/goals/{id}` - Get goal details
- `PUT /api/v1/goals/{id}` - Update goal
- `PATCH /api/v1/goals/{id}/progress` - Update progress

### Progress
- `POST /api/v1/progress` - Log progress entry
- `GET /api/v1/progress` - List progress entries
- `GET /api/v1/progress/weight/latest` - Get latest weight
- `GET /api/v1/progress/weight/change` - Get weight trend

### Dashboard
- `GET /api/v1/dashboard` - Get dashboard data

## 🧪 Testing

### Backend Tests
```bash
# Run tests
docker-compose exec backend pytest

# Run with coverage
docker-compose exec backend pytest --cov=app
```

### Frontend Tests
```bash
# Run tests
docker-compose exec frontend npm test

# Run E2E tests
docker-compose exec frontend npm run test:e2e
```

## 🚢 Production Deployment

### Build for Production

```bash
# Build production images
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Start production services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Important Security Steps

1. **Update Environment Variables**
   - Set strong `POSTGRES_PASSWORD`
   - Generate new `SECRET_KEY`
   - Set `DEBUG=false`
   - Set `ENVIRONMENT=production`
   - Update `BACKEND_CORS_ORIGINS` to production URLs

2. **Enable HTTPS**
   - Configure SSL certificates in nginx
   - Update nginx configuration for HTTPS

3. **Database Backups**
   - Set up automated backups
   - Test restore procedures

4. **Monitoring**
   - Set up logging
   - Configure error tracking
   - Monitor performance

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [FastAPI Template](https://github.com/chanRG/template-fastAPI.git) - Base template

## 📧 Support

For support and questions:
- Open an issue on GitHub
- Check the documentation in `/backend/SETUP.md`
- Review API docs at http://localhost/docs

---

**EndureIT** - Track your fitness, reach your goals 💪🏃‍♂️

