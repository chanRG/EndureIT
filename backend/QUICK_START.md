# EndureIT Backend - Quick Start

> **Important**: All commands must be run from the **project root** (`/path/to/EndureIT/`), not from `backend/`.

## 🚀 Start the Backend (First Time)

```bash
# Navigate to project root
cd /Users/Roger/Projects/EndureIT

# 1. Ensure Docker Desktop is running

# 2. Build and start all services
make up-build

# 3. Initialize the database
make init-db

# 4. Open API docs
open http://localhost/docs
```

## 📝 Daily Development

```bash
# From project root
cd /Users/Roger/Projects/EndureIT

# Start services
make up

# View logs
make logs          # All services
make logs-backend  # Backend only

# Stop services
make down
```

## 🔑 Key URLs

- **API Docs**: http://localhost/docs
- **Health Check**: http://localhost/api/v1/health
- **API Base**: http://localhost/api/v1

## 🛠 Useful Commands

```bash
# All commands from project root
make help            # Show all commands
make logs-backend    # View backend logs
make shell-backend   # Access backend container
make shell-db        # Access database
make reset-db        # Reset database
make health          # Check service health
```

## 📦 Project Info

- **Database**: PostgreSQL (endureit_db)
- **User**: endureit_user
- **API Framework**: FastAPI
- **Auth**: JWT tokens
- **Ports**: 
  - 80 (Nginx/API)
  - 5432 (PostgreSQL)
  - 6379 (Redis)

## 📚 Full Documentation

See `SETUP.md` for complete documentation including:
- API endpoints
- Adding new models
- Development workflow
- Production deployment
- Troubleshooting

## ⚙️ Configuration

Edit `.env` file to customize:
- Database credentials
- JWT secret key
- CORS origins
- Environment settings

---

**Template Source**: https://github.com/chanRG/template-fastAPI.git

