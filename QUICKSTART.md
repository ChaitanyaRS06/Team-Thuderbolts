# Quick Start Guide

## One-Command Startup ⚡

```bash
./start.sh
```

This single command will:
- ✅ Check if Docker is running
- ✅ Check if .env file exists
- ✅ Build all services (frontend, backend, database)
- ✅ Start all containers
- ✅ Show service status and access information

## One-Command Stop 🛑

```bash
./stop.sh
```

## Login Credentials 🔑

- **Email**: `admin@uva.edu`
- **Password**: `admin`

## Access URLs 🌐

- **Frontend**: http://localhost:5174
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Monitor Logs 📊

```bash
# View all logs
docker-compose logs -f

# View backend logs only
docker-compose logs -f backend

# View frontend logs only
docker-compose logs -f frontend
```

## Other Useful Commands

```bash
# Restart services
docker-compose restart

# Rebuild and restart
docker-compose up -d --build

# Stop and remove all data
docker-compose down -v

# Check service status
docker-compose ps
```

## First Time Setup

1. Make sure you have your API keys in `.env`:
   - `OPENAI_API_KEY`
   - `ANTHROPIC_API_KEY`
   - `TAVILY_API_KEY`

2. Run the startup script:
   ```bash
   ./start.sh
   ```

3. Open http://localhost:5174 and login!

That's it! 🎉
