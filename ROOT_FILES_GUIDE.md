# Root-Level Files Guide

This document explains the purpose of each file and directory at the root level of the EndureIT project.

## 📂 Directories

### `.git/`
Git version control metadata. Do not modify manually.

### `.github/`
GitHub-specific configuration files.

#### `.github/workflows/`
CI/CD automation workflows for GitHub Actions.

- **`backend-ci.yml`** - Automated testing, linting, and building for backend
  - Runs on push/PR to main/develop branches
  - Tests with PostgreSQL and Redis services
  - Includes: linting (flake8), formatting (black), type checking (mypy), pytest
  - Builds Docker image for validation

- **`frontend-ci.yml.disabled`** - Frontend CI workflow (disabled until frontend is ready)
  - Rename to `frontend-ci.yml` to activate
  - Will run npm tests, linting, and build checks

### `backend/`
FastAPI backend application. See `backend/README.md` for details.

### `frontend/`
Frontend application (to be configured with your chosen framework).

## 📄 Configuration Files

### `.env` (gitignored)
**Purpose**: Contains actual secrets and configuration values.

**Status**: ❌ Never commit to git  
**Location**: `/EndureIT/.env`  
**Created from**: `.env.example`

**Contains**:
- Database credentials
- Secret keys
- Environment settings
- CORS origins

**Setup**:
```bash
./setup-env.sh  # Automated
# or
cp .env.example .env  # Manual
```

### `.env.example`
**Purpose**: Template showing required environment variables.

**Status**: ✅ Committed to git  
**Location**: `/EndureIT/.env.example`

**Usage**: Developers copy this to `.env` and fill in actual values.

### `.dockerignore`
**Purpose**: Excludes files from Docker build context for faster builds and smaller images.

**Key exclusions**:
- Documentation files (*.md)
- Git files (.git, .gitignore)
- IDE configurations
- Test coverage reports
- Node modules and Python cache

**When to update**: Add new patterns when you have files that shouldn't be in Docker images.

### `.editorconfig`
**Purpose**: Ensures consistent coding style across different editors and IDEs.

**Configurations**:
- Python: 4 spaces, UTF-8, LF line endings
- JavaScript/TypeScript: 2 spaces
- JSON/YAML: 2 spaces
- Markdown: No trailing whitespace trim

**Benefits**: Automatic formatting in supported editors (VS Code, IntelliJ, etc.)

### `.gitignore`
**Purpose**: Specifies files and directories that Git should ignore.

**Key patterns**:
- Environment files (.env)
- Python cache (__pycache__, *.pyc)
- Node modules
- Build artifacts
- Database files
- IDE configurations
- OS-specific files

**When to update**: Add new patterns when you create files that shouldn't be version controlled.

### `docker-compose.yml`
**Purpose**: Orchestrates all services (database, backend, frontend, nginx, redis).

**Services defined**:
- `db` - PostgreSQL 15 database (port 5432)
- `redis` - Redis 7 cache (port 6379)
- `backend` - FastAPI application (internal port 8000)
- `nginx` - Reverse proxy (ports 80/443)
- `frontend` - Frontend app (commented out, port 3000)

**Usage**: `make up-build` or `docker-compose up -d`

### `Makefile`
**Purpose**: Provides convenient commands for common development tasks.

**Key commands**:
```bash
make help          # Show all commands
make setup-env     # Setup environment files
make setup         # Complete initial setup
make up-build      # Build and start all services
make init-db       # Initialize database
make logs          # View all logs
make shell-backend # Access backend container
make clean         # Clean up everything
```

**Benefits**: Simplified workflow, consistent commands across team.

### `setup-env.sh`
**Purpose**: Interactive script to create and configure `.env` files.

**Status**: ✅ Executable script  
**Usage**:
```bash
./setup-env.sh
```

**What it does**:
- Creates `.env` from `.env.example`
- Creates `backend/.env` from `backend/.env.example`
- Generates secure SECRET_KEY
- Prompts for database credentials
- Auto-generates strong passwords
- Provides setup summary

**Benefits**:
- Fast setup for new developers
- Ensures secure key generation
- Reduces configuration errors
- Interactive and user-friendly

## 📚 Documentation Files

### `README.md`
**Purpose**: Main project overview and quick start guide.

**Contents**:
- Project overview
- Features list
- Quick start instructions
- Tech stack
- Common commands
- Service descriptions

**Audience**: New developers, project visitors, GitHub viewers.

### `CONTRIBUTING.md`
**Purpose**: Guidelines for contributing to the project.

**Contents**:
- How to set up development environment
- Coding standards and conventions
- Commit message format
- Pull request process
- Testing requirements
- How to report bugs

**Audience**: Contributors, open-source collaborators.

### `CODE_OF_CONDUCT.md`
**Purpose**: Establishes community standards and behavior expectations.

**Based on**: Contributor Covenant v2.0

**Contents**:
- Community pledge
- Standards of behavior
- Enforcement policies
- Reporting procedures

**Audience**: All community members and contributors.

### `CHANGELOG.md`
**Purpose**: Documents all notable changes to the project.

**Format**: Based on [Keep a Changelog](https://keepachangelog.com/)

**Structure**:
- Unreleased changes
- Version releases with dates
- Categorized changes (Added, Changed, Fixed, etc.)

**When to update**: After each feature, fix, or release.

### `PROJECT_STRUCTURE.md`
**Purpose**: Detailed explanation of the entire project structure.

**Contents**:
- Directory structure with descriptions
- Architecture diagrams
- File organization principles
- Database schema overview
- Request flow examples

**Audience**: Developers who need to understand the architecture.

### `ROOT_FILES_GUIDE.md`
**Purpose**: This file - explains each root-level file and directory.

### `ENV_CONFIGURATION.md`
**Purpose**: Comprehensive guide to environment variable configuration.

**Contents**:
- File structure explanation
- Variable reference tables
- Setup instructions
- Security best practices
- Environment-specific configs (dev/prod)
- Troubleshooting guide
- Examples

**Audience**: Developers configuring the application.

**Key sections**:
- Root vs backend .env files
- How variables flow between services
- Variable precedence rules
- Security guidelines

## ⚖️ Legal Files

### `LICENSE`
**Purpose**: Defines the legal terms under which the software can be used.

**License**: MIT License

**Key points**:
- Free to use, modify, and distribute
- Must include original license
- No warranty provided

**When to update**: Generally never, unless changing license type.

## 🎯 File Organization Principles

### What Goes in Root

✅ **Should be at root**:
- Project-wide configuration (docker-compose, Makefile)
- Documentation (README, CONTRIBUTING, etc.)
- Legal files (LICENSE, CODE_OF_CONDUCT)
- CI/CD workflows (.github/)
- Editor/IDE configs (.editorconfig)
- Version control configs (.gitignore)

❌ **Should NOT be at root**:
- Application code (goes in backend/ or frontend/)
- Language-specific configs (goes in respective directories)
- Build artifacts (ignored by .gitignore)
- Test files (goes in respective test directories)

### Backend vs Root Configuration

| File Type | Location | Reason |
|-----------|----------|--------|
| docker-compose.yml | Root | Orchestrates all services |
| .env | backend/ | Backend-specific secrets |
| .env.example | backend/ | Backend environment template |
| Dockerfile | backend/ | Backend container definition |
| requirements.txt | backend/ | Python dependencies |
| package.json | frontend/ | Node dependencies |
| Makefile | Root | Commands for entire project |

## 🔄 Maintenance Guidelines

### Regular Updates

**Monthly**:
- Review and update CHANGELOG.md
- Check for outdated dependencies
- Review open issues/PRs

**Per Release**:
- Update CHANGELOG.md with version
- Update README.md if features changed
- Review and update documentation

**As Needed**:
- Add new patterns to .gitignore
- Update .dockerignore for new file types
- Add new Makefile commands
- Update CI/CD workflows

### Version Control

All root-level files should be version controlled **EXCEPT**:
- `.env` files (contain secrets)
- Build artifacts
- Cache directories
- OS-specific files

## 🆘 Troubleshooting

### "File not found" errors
- Ensure you're in project root: `cd /path/to/EndureIT`
- Check file exists: `ls -la`

### Docker build issues
- Check .dockerignore isn't excluding necessary files
- Verify Dockerfile paths are correct

### CI/CD failures
- Check .github/workflows/*.yml syntax
- Verify secrets are configured in GitHub

### Editor not respecting formatting
- Install EditorConfig plugin for your editor
- Check .editorconfig syntax

## 📖 Further Reading

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [EditorConfig Specification](https://editorconfig.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Semantic Versioning](https://semver.org/)
- [Contributor Covenant](https://www.contributor-covenant.org/)

---

**Last Updated**: 2024-11-04

For questions or clarifications, open an issue on GitHub.

