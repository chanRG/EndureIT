# Contributing to EndureIT

Thank you for your interest in contributing to EndureIT! This document provides guidelines and instructions for contributing to the project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Testing](#testing)

## 🤝 Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect differing viewpoints and experiences

## 🚀 Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/EndureIT.git
cd EndureIT
```

### 2. Set Up Development Environment

```bash
# Copy environment configuration
cp backend/.env.example backend/.env

# Edit backend/.env with your settings

# Build and start services
make up-build

# Initialize database
make init-db
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

## 💻 Development Workflow

### Backend Development

```bash
# Start services
make up

# View backend logs
make logs-backend

# Access backend shell
make shell-backend

# Run backend tests
make test-backend

# Format code
make format-backend

# Lint code
make lint-backend
```

### Frontend Development

```bash
# Access frontend shell
make shell-frontend

# Run frontend tests
make test-frontend

# View frontend logs
make logs-frontend
```

### Database Changes

```bash
# Reset database after model changes
make reset-db

# Backup database
make backup-db

# Access database directly
make shell-db
```

## 📝 Coding Standards

### Python (Backend)

- Follow **PEP 8** style guide
- Use **type hints** for all functions
- Write **docstrings** for all public functions and classes
- Keep functions focused and small
- Use meaningful variable names

**Example:**

```python
def calculate_workout_duration(
    start_time: datetime,
    end_time: datetime
) -> int:
    """Calculate workout duration in seconds.
    
    Args:
        start_time: Workout start timestamp
        end_time: Workout end timestamp
        
    Returns:
        Duration in seconds
    """
    delta = end_time - start_time
    return int(delta.total_seconds())
```

### Code Formatting

- **Backend**: Use `black` and `isort`
  ```bash
  make format-backend
  ```

- **Frontend**: Use your framework's formatter (Prettier, ESLint)
  ```bash
  npm run format
  ```

### Project Structure

```
EndureIT/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── services/     # Business logic
│   │   ├── models/       # Database models
│   │   ├── schemas/      # Pydantic schemas
│   │   └── core/         # Core configuration
│   └── tests/            # Backend tests
└── frontend/
    ├── src/
    │   ├── components/   # Reusable components
    │   ├── pages/        # Page components
    │   ├── services/     # API services
    │   └── utils/        # Utility functions
    └── tests/            # Frontend tests
```

## 📦 Adding New Features

### Backend Feature Checklist

1. **Create Model** (if needed)
   ```python
   # backend/app/models/your_model.py
   class YourModel(Base):
       __tablename__ = "your_table"
       # ... fields
   ```

2. **Create Schema**
   ```python
   # backend/app/schemas/your_schema.py
   class YourModelCreate(BaseModel):
       # ... fields
   ```

3. **Create Service**
   ```python
   # backend/app/services/your_service.py
   class YourService:
       @staticmethod
       def create_item(...):
           # ... logic
   ```

4. **Create Endpoints**
   ```python
   # backend/app/api/v1/endpoints/your_endpoint.py
   @router.post("")
   def create_item(...):
       return YourService.create_item(...)
   ```

5. **Register Router**
   ```python
   # backend/app/api/v1/api.py
   api_router.include_router(
       your_endpoint.router,
       prefix="/your-endpoint",
       tags=["your-tag"]
   )
   ```

6. **Update Database**
   ```bash
   make reset-db
   ```

7. **Write Tests**
   ```python
   # backend/tests/test_your_feature.py
   def test_create_item():
       # ... test
   ```

## ✍️ Commit Guidelines

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```bash
feat(workout): add exercise duration tracking

- Add duration_seconds field to Exercise model
- Update workout service to calculate total duration
- Add duration display to workout details page

Closes #123
```

```bash
fix(auth): resolve token expiration issue

Token was expiring prematurely due to timezone mismatch.
Updated token generation to use UTC consistently.

Fixes #456
```

## 🔄 Pull Request Process

### 1. Update Your Branch

```bash
git fetch origin
git rebase origin/main
```

### 2. Run Tests

```bash
# Backend tests
make test-backend

# Frontend tests
make test-frontend
```

### 3. Push Changes

```bash
git push origin feature/your-feature-name
```

### 4. Create Pull Request

- Go to GitHub and create a Pull Request
- Fill out the PR template
- Link related issues
- Request review from maintainers

### PR Checklist

- [ ] Code follows the style guidelines
- [ ] Self-review of code completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] No new warnings
- [ ] Related issues linked

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe how to test the changes

## Screenshots (if applicable)

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Tests added/updated
- [ ] Documentation updated
```

## 🧪 Testing

### Writing Tests

#### Backend Tests

```python
# backend/tests/test_workout_service.py
import pytest
from app.services.workout_service import WorkoutService

def test_create_workout(db_session, test_user):
    """Test workout creation."""
    workout_data = WorkoutCreate(
        title="Morning Run",
        workout_type=WorkoutType.RUNNING,
        start_time=datetime.utcnow(),
        duration_seconds=1800
    )
    
    workout = WorkoutService.create_workout(
        db_session,
        test_user,
        workout_data
    )
    
    assert workout.id is not None
    assert workout.title == "Morning Run"
    assert workout.user_id == test_user.id
```

#### Frontend Tests

```javascript
// frontend/tests/WorkoutCard.test.js
import { render, screen } from '@testing-library/react';
import WorkoutCard from '../components/WorkoutCard';

test('renders workout title', () => {
  const workout = {
    title: 'Morning Run',
    duration_seconds: 1800
  };
  
  render(<WorkoutCard workout={workout} />);
  
  expect(screen.getByText('Morning Run')).toBeInTheDocument();
});
```

### Running Tests

```bash
# All tests
make test-backend
make test-frontend

# With coverage
make test-backend-cov

# Specific test file
docker-compose exec backend pytest tests/test_workout_service.py

# Specific test
docker-compose exec backend pytest tests/test_workout_service.py::test_create_workout
```

## 🐛 Reporting Bugs

### Before Reporting

1. Check existing issues
2. Ensure you're on the latest version
3. Try to reproduce in a clean environment

### Bug Report Template

```markdown
## Bug Description
Clear description of the bug

## Steps to Reproduce
1. Go to '...'
2. Click on '...'
3. See error

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Screenshots
If applicable

## Environment
- OS: [e.g., macOS 12.0]
- Browser: [e.g., Chrome 95]
- Version: [e.g., 1.0.0]

## Additional Context
Any other relevant information
```

## 💡 Feature Requests

Use the Feature Request template on GitHub Issues:

```markdown
## Feature Description
Clear description of the feature

## Use Case
Why is this feature needed?

## Proposed Solution
How should it work?

## Alternatives Considered
Other approaches considered

## Additional Context
Any other relevant information
```

## 📖 Documentation

- Update relevant `.md` files
- Add docstrings to new functions
- Update API documentation
- Add examples where helpful

## 🎯 Areas for Contribution

### Good First Issues

- UI improvements
- Documentation updates
- Test coverage
- Bug fixes

### Feature Ideas

- Nutrition tracking
- Social features
- Workout templates
- Mobile app
- Export/import data
- Third-party integrations (Strava, Fitbit)

## 🆘 Getting Help

- Check [documentation](./backend/README.md)
- Review [setup guide](./backend/SETUP.md)
- Ask in GitHub Discussions
- Open an issue

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Thank You

Thank you for contributing to EndureIT! Your efforts help make this project better for everyone.

---

**Happy Coding!** 💪🏃‍♂️

