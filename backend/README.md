# PharmaPricing Backend - Python (FastAPI)

## 🐍 Python Backend with FastAPI

The backend has been rebuilt in **Python with FastAPI** for better ease of integration and future extensibility.

### Tech Stack
- **Framework:** FastAPI (modern, fast Python web framework)
- **Server:** Uvicorn (ASGI server)
- **Database:** PostgreSQL with SQLAlchemy ORM
- **Authentication:** JWT tokens + Bcrypt password hashing
- **Validation:** Pydantic for request/response validation

---

## 🚀 Quick Start

### 1. Install Python Dependencies

```bash
cd backend

# Create virtual environment (recommended)
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env

# Required settings:
# - DB_HOST=localhost
# - DB_PORT=5432
# - DB_NAME=pharmapricing_dev
# - DB_USER=postgres
# - DB_PASSWORD=your_password
# - JWT_SECRET=your_secret_key
```

### 3. Start Server

```bash
# Development mode (with auto-reload)
python -m uvicorn main:app --reload --host 0.0.0.0 --port 3000

# Or using the run command
python main.py

# Server running at http://localhost:3000
```

### 4. View API Documentation

Visit in browser:
- **Swagger UI:** http://localhost:3000/docs
- **ReDoc:** http://localhost:3000/redoc
- **OpenAPI Schema:** http://localhost:3000/openapi.json

---

## 📁 Project Structure

```
backend/
├── main.py                    # FastAPI application entry point
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
│
└── app/                       # Application package
    ├── __init__.py
    ├── database.py           # PostgreSQL connection & session management
    │
    ├── routes/               # API endpoints
    │   ├── __init__.py
    │   └── auth_routes.py   # Authentication endpoints
    │
    ├── services/             # Business logic
    │   ├── __init__.py
    │   └── auth.py          # Authentication service
    │
    ├── schemas/              # Pydantic request/response models
    │   ├── __init__.py
    │   └── auth.py          # Auth schemas
    │
    ├── middleware/           # Custom middleware (future)
    │   └── __init__.py
    │
    ├── models/               # SQLAlchemy models (future)
    │   └── __init__.py
    │
    └── utils/                # Utility functions
        ├── __init__.py
        ├── auth.py           # JWT & password hashing
        └── validation.py     # Input validation
```

---

## 🔌 API Endpoints

### Authentication

**Signup:**
```bash
POST /api/auth/signup
Content-Type: application/json

{
  "email": "user@pharmapricing.com",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "company_name": "ABC Pharma",
  "phone": "9876543210",
  "city": "Bangalore",
  "state": "KA"
}
```

**Login:**
```bash
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@pharmapricing.com",
  "password": "SecurePass123!"
}
```

**Profile (Protected):**
```bash
GET /api/auth/profile
Authorization: Bearer YOUR_JWT_TOKEN
```

**Refresh Token (Protected):**
```bash
POST /api/auth/refresh-token
Authorization: Bearer YOUR_JWT_TOKEN
```

**Logout (Protected):**
```bash
POST /api/auth/logout
Authorization: Bearer YOUR_JWT_TOKEN
```

---

## 🔐 Security Features

### Password Security
- Bcrypt hashing with automatic salt generation
- Min 8 characters required
- Must contain: uppercase, lowercase, numbers
- Configurable work factor

### JWT Tokens
- Signed with HS256 algorithm
- Configurable expiration (default 7 days)
- User ID and email encoded in payload
- Token refresh support

### Input Validation
- Email format validation
- Phone number validation (Indian format by default)
- Name length validation
- XSS protection via Pydantic

### Database Security
- Parameterized queries (prevents SQL injection)
- SQLAlchemy ORM protection
- Connection pooling for performance

---

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=app
```

### Manual Testing with cURL

```bash
# Signup
curl -X POST http://localhost:3000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email":"test@test.com",
    "password":"TestPassword123!",
    "full_name":"Test User",
    "company_name":"Test Pharma",
    "phone":"9876543210",
    "city":"Bangalore",
    "state":"KA"
  }'

# Login
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email":"test@test.com",
    "password":"TestPassword123!"
  }'

# Get Profile (replace TOKEN with actual JWT)
curl -X GET http://localhost:3000/api/auth/profile \
  -H "Authorization: Bearer TOKEN"
```

---

## 🛠️ Development Guide

### Adding New Endpoint

1. **Create Schema** (`app/schemas/your_feature.py`):
```python
from pydantic import BaseModel

class MyRequest(BaseModel):
    field1: str
    field2: int
```

2. **Create Service** (`app/services/your_feature.py`):
```python
class MyService:
    @staticmethod
    async def my_operation(param1, param2, db: Session):
        # Business logic here
        pass
```

3. **Create Route** (`app/routes/your_routes.py`):
```python
from fastapi import APIRouter, Depends

router = APIRouter()

@router.post("/my-endpoint")
async def my_endpoint(request: MyRequest, db: Session = Depends(get_db)):
    # Call service
    result = await MyService.my_operation(...)
    return {"success": True, "data": result}
```

4. **Include in Main App** (`main.py`):
```python
from app.routes import your_routes

app.include_router(
    your_routes.router,
    prefix="/api/your-prefix",
    tags=["Your Feature"]
)
```

---

## 📦 Dependencies

### Core
- **fastapi** - Web framework
- **uvicorn** - ASGI server
- **sqlalchemy** - ORM
- **psycopg2-binary** - PostgreSQL adapter
- **pydantic** - Data validation

### Security
- **PyJWT** - JWT tokens
- **passlib** - Password hashing
- **bcrypt** - Bcrypt implementation

### Development
- **black** - Code formatter
- **flake8** - Linter
- **pytest** - Testing framework
- **pytest-asyncio** - Async test support

---

## 🚢 Production Deployment

### Using Gunicorn

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:3000 main:app
```

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]
```

Build and run:
```bash
docker build -t pharmapricing-backend .
docker run -p 3000:3000 pharmapricing-backend
```

---

## 📝 Code Standards

### Python Style
- Follow PEP 8
- Use type hints
- Docstrings on all functions/classes
- Max line length: 100 characters

### Naming Conventions
- Classes: PascalCase
- Functions/variables: snake_case
- Constants: UPPER_CASE
- Private: _leading_underscore

### Async/Await
- Use async for database operations
- Use `await` for async function calls
- Keep route handlers async

### Error Handling
- Always handle exceptions in services
- Use FastAPI HTTPException for API errors
- Log errors with logger
- Return meaningful error messages

---

## 🔄 Integration with Frontend

The Python backend is fully compatible with the existing React frontend. No changes needed:

```javascript
// Frontend can use same API
const response = await axios.post(
  'http://localhost:3000/api/auth/signup',
  { email, password, ... }
);
```

---

## 📚 Key Features of Python Version

✨ **Better for Integration:**
- Easy to extend with ML/AI models
- Large ecosystem of libraries
- Easy to add Celery for background tasks
- Easy to integrate with data science tools

✨ **Production Ready:**
- Automatic API documentation
- Type safety with Pydantic
- Excellent testing framework
- Easy to scale with Gunicorn/Uvicorn

✨ **Developer Friendly:**
- Clean, readable code
- Excellent error messages
- Great debugging tools
- Large community support

---

## 🆘 Troubleshooting

### Port Already in Use
```bash
# Find process using port 3000
lsof -i :3000

# Kill process
kill -9 <PID>
```

### Database Connection Error
```bash
# Check PostgreSQL is running
psql -U postgres -d pharmapricing_dev

# Check .env has correct credentials
cat .env
```

### Module Not Found
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### ImportError
```bash
# Add app directory to Python path
export PYTHONPATH="${PYTHONPATH}:/path/to/backend"
```

---

## 📖 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [JWT Documentation](https://jwt.io/)

---

**Python Backend with FastAPI - Ready for Production! 🚀**
