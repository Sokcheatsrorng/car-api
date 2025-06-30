#!/bin/bash

# Start script for the Car Selling API

echo "Starting Car Selling API with Docker Compose..."

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1q

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please edit .env file with your configuration before running again."
    exit 1
fi

# Build and start the services
echo "Building and starting services..."
docker-compose up --build -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Check if services are running
echo "Checking service status..."
docker-compose ps

echo ""
echo "🚀 Car Selling API is now running!"
echo ""
echo "📊 API Documentation: http://localhost:8000/docs"
echo "🔧 pgAdmin: http://localhost:5050"
echo "   - Email: admin@carsellingapi.com"
echo "   - Password: admin123"
echo ""
echo "🗄️  Database Connection:"
echo "   - Host: localhost"
echo "   - Port: 5432"
echo "   - Database: cardb"
echo "   - Username: caruser"
echo "   - Password: carpass"
echo ""
echo "To stop the services, run: docker-compose down"
echo "To view logs, run: docker-compose logs -f"
