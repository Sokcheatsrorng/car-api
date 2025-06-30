# 🚗 Car Selling API

A comprehensive FastAPI-based REST API for a car selling platform with JWT authentication, file uploads, and PostgreSQL database.

## ✨ Features

- **🔐 JWT Authentication** - Register, login, refresh tokens
- **🚗 Car Management** - CRUD operations for car listings  
- **📸 Image Upload** - Car photo upload with validation
- **🔍 Search** - Search cars by make, model, color, description
- **👤 User Management** - User profiles and authentication
- **🗄️ PostgreSQL Database** - Robust data persistence
- **📊 API Documentation** - Auto-generated Swagger/OpenAPI docs
- **🐳 Docker Support** - Easy deployment with Docker Compose

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- Git

### 🐳 Docker Deployment (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/Sokcheatsrorng/car-api.git
   cd car-api
   ```

2. **Start the services**
   ```bash
   docker-compose up -d --build
   ```

3. **Access the API**
   - API: http://localhost:8998
   - Documentation: http://localhost:8998/docs
   - Database: localhost:5432

### Docker Services

The Docker Compose setup includes:

- **FastAPI Application** (port 8000)
- **PostgreSQL Database** (port 5432)
- **Redis Cache** (port 6379) - Optional
- **pgAdmin** (port 5050) - Database management UI

### Docker Commands

\`\`\`bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove all data
docker-compose down -v

# Rebuild and restart
docker-compose up --build -d

# Access database directly
docker-compose exec db psql -U caruser -d cardb
\`\`\`

### Environment Variables

Key environment variables in `.env`:

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT secret key (change in production!)
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`: Database credentials

### Production Deployment

For production deployment:

1. Change all default passwords in `.env`
2. Use a strong `SECRET_KEY`
3. Configure proper SSL/TLS
4. Set up proper backup strategies
5. Configure monitoring and logging
6. Use Docker secrets for sensitive data

## Installation

1. Install dependencies:
\`\`\`bash
pip install -r requirements.txt
\`\`\`

2. Run the application:
\`\`\`bash
python main.py
\`\`\`

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:
- Interactive API docs: `http://localhost:8000/docs`
- ReDoc documentation: `http://localhost:8000/redoc`

## Endpoints

### Authentication
- `POST /register` - Register a new user
- `POST /login` - Login and get access token
- `GET /me` - Get current user info (requires auth)

### Cars
- `POST /cars` - Create a new car listing (requires auth)
- `GET /cars` - Get all cars (public)
- `GET /cars/{car_id}` - Get specific car (public)
- `GET /my-cars` - Get current user's cars (requires auth)
- `PUT /cars/{car_id}` - Update car (requires auth, owner only)
- `DELETE /cars/{car_id}` - Delete car (requires auth, owner only)
- `GET /cars/search/{query}` - Search cars by make, model, color, or description

## Usage Example

1. Register a user:
\`\`\`bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com", 
    "password": "password123",
    "full_name": "John Doe"
  }'
\`\`\`

2. Login to get token:
\`\`\`bash
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "password123"
  }'
\`\`\`

3. Create a car listing:
\`\`\`bash
curl -X POST "http://localhost:8000/cars" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "make": "Toyota",
    "model": "Camry", 
    "year": 2020,
    "price": 25000.00,
    "mileage": 30000,
    "description": "Well maintained car",
    "color": "Silver",
    "fuel_type": "Gasoline",
    "transmission": "Automatic"
  }'
\`\`\`

## Security Notes

- Change the SECRET_KEY in production
- Use environment variables for sensitive configuration
- Consider using a real database instead of in-memory storage
- Implement rate limiting for production use
- Add input validation and sanitization

## Testing

Run the test script to verify API functionality:
\`\`\`bash
python test_api.py
\`\`\`

Make sure the API server is running before executing the tests.
