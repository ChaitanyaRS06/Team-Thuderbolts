#!/bin/bash

echo "🎓 UVA AI Research Assistant - Starting All Services"
echo "===================================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ ERROR: Docker is not running!"
    echo "Please start Docker Desktop and try again."
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and add your API keys!"
    echo "Required: OPENAI_API_KEY, ANTHROPIC_API_KEY, TAVILY_API_KEY"
    echo ""
    read -p "Press Enter after you've added your API keys to .env (or press Ctrl+C to exit)..."
fi

echo "🐳 Building and starting all services..."
echo ""

# Build and start all services
docker-compose up -d --build

echo ""
echo "⏳ Waiting for services to initialize..."
sleep 8

# Check service status
echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "✅ All services started successfully!"
echo ""
echo "📱 Access Information:"
echo "   Frontend:  http://localhost:5174"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "🔑 Login Credentials:"
echo "   Email:     admin@uva.edu"
echo "   Password:  admin"
echo ""
echo "📋 Useful Commands:"
echo "   View logs:        docker-compose logs -f"
echo "   Stop services:    docker-compose down"
echo "   Restart:          ./start.sh"
echo ""
echo "🎉 Ready to use! Open http://localhost:5174 in your browser"
