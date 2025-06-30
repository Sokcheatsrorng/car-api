#!/bin/bash

# Stop script for the Car Selling API

echo "Stopping Car Selling API services..."

# Stop and remove containers
docker-compose down

echo "Services stopped successfully!"
echo ""
echo "To remove all data (including database), run:"
echo "docker-compose down -v"
