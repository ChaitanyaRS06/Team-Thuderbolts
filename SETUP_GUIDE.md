# Setup Guide for UVA AI Research Assistant

This guide will help you get started with the UVA AI Research Assistant.

## Prerequisites Checklist

Before you begin, make sure you have:

- [ ] Docker Desktop installed and running
- [ ] Docker Compose installed (included with Docker Desktop)
- [ ] OpenAI API key
- [ ] Anthropic API key
- [ ] Tavily API key
- [ ] (Optional) Microsoft Graph API credentials for OneDrive

## Step-by-Step Setup

### 1. Get API Keys

#### OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy and save the key (starts with `sk-...`)

#### Anthropic API Key
1. Go to https://console.anthropic.com/
2. Sign in or create an account
3. Navigate to API Keys
4. Create a new API key
5. Copy and save the key (starts with `sk-ant-...`)

#### Tavily API Key
1. Go to https://tavily.com/
2. Sign up for an account
3. Get your API key from the dashboard
4. Copy and save the key (starts with `tvly-...`)

#### Microsoft Graph (Optional - for OneDrive)
1. Go to https://portal.azure.com/
2. Register an application in Azure AD
3. Get Client ID, Client Secret, and Tenant ID
4. Grant Microsoft Graph API permissions for Files.ReadWrite.All

### 2. Configure Environment

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your API keys:
   ```bash
   # Use your favorite text editor
   nano .env
   # or
   vim .env
   # or
   code .env
   ```

3. Replace the placeholder values:
   ```env
   OPENAI_API_KEY=sk-your-actual-openai-key-here
   ANTHROPIC_API_KEY=sk-ant-your-actual-anthropic-key-here
   TAVILY_API_KEY=tvly-your-actual-tavily-key-here
   ```

4. Generate a secure JWT secret key:
   ```bash
   # On Mac/Linux:
   openssl rand -hex 32

   # Or use Python:
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

   Add it to `.env`:
   ```env
   SECRET_KEY=<your-generated-key>
   ```

### 3. Start the Application

1. Make sure Docker Desktop is running

2. Start all services:
   ```bash
   docker-compose up -d
   ```

3. Wait for services to start (about 30 seconds):
   ```bash
   # Watch the logs
   docker-compose logs -f

   # Press Ctrl+C to stop watching logs
   ```

4. Check that all services are running:
   ```bash
   docker-compose ps
   ```

   You should see:
   - `uva-research-assistant-db` - running
   - `uva-research-assistant-backend` - running
   - `uva-research-assistant-frontend` - running

### 4. Access the Application

1. Open your browser and go to: http://localhost:5174

2. You should see the login page

3. Create a new account:
   - Click "Don't have an account? Sign up"
   - Enter your email, full name, and password
   - Click "Create Account"

4. You're ready to use the assistant!

### 5. First Steps

#### Upload Your First Document

1. Click "Upload Documents" in the sidebar
2. Select document type (e.g., "Research Paper")
3. Choose a PDF file from your computer
4. Click "Upload and Process"
5. Wait for processing to complete (~30 seconds)

#### Ask Your First Question

1. Click "Ask Questions" in the sidebar
2. Type a question about your document, e.g.:
   - "What are the main findings?"
   - "Summarize the methodology"
   - "What conclusions are drawn?"
3. Click "Send"
4. Wait for the AI to generate an answer with citations

#### Search UVA Resources (Optional)

1. First, index UVA resources (if you're an admin):
   ```bash
   curl -X POST http://localhost:8000/uva/scrape-it-resources \
     -H "Authorization: Bearer <your-token>"
   ```

2. Click "UVA Resources" in the sidebar
3. Select a resource type (e.g., "OneDrive")
4. Search for UVA-specific information

## Troubleshooting

### Issue: "Connection refused" or cannot access frontend

**Solution:**
```bash
# Check if services are running
docker-compose ps

# Restart frontend
docker-compose restart frontend

# Check frontend logs
docker-compose logs frontend
```

### Issue: Backend API errors

**Solution:**
```bash
# Check backend logs
docker-compose logs backend

# Verify API keys are set
docker exec -it uva-research-assistant-backend env | grep API_KEY

# Restart backend
docker-compose restart backend
```

### Issue: Database connection errors

**Solution:**
```bash
# Stop all services
docker-compose down

# Remove volumes (WARNING: This deletes all data)
docker-compose down -v

# Start fresh
docker-compose up -d
```

### Issue: PDF processing fails

**Solution:**
- Ensure PDF is not password-protected
- Check file size (very large PDFs may take longer)
- Check backend logs: `docker-compose logs backend | grep -i pdf`

### Issue: Slow response times

**Solution:**
- Check your internet connection (for web search)
- Verify API keys are valid
- Reduce max_iterations in the Assistant settings
- Consider using a faster model for simple queries

## Stopping the Application

To stop all services:
```bash
docker-compose down
```

To stop and remove all data (including uploaded documents):
```bash
docker-compose down -v
```

## Updating the Application

1. Pull latest changes:
   ```bash
   git pull origin main
   ```

2. Rebuild containers:
   ```bash
   docker-compose up -d --build
   ```

## Next Steps

- Explore the API documentation: http://localhost:8000/docs
- Upload multiple documents to build your knowledge base
- Try different AI models (GPT-4 vs Claude)
- Experiment with UVA resource search
- Check out the README.md for advanced features

## Getting Help

If you encounter issues:

1. Check the logs: `docker-compose logs -f`
2. Review the main README.md
3. Check the API docs: http://localhost:8000/docs
4. Ensure all API keys are valid and have sufficient credits

## Security Reminders

- Never commit your `.env` file to version control
- Keep your API keys secure
- Use strong passwords for user accounts
- In production, use HTTPS and secure the SECRET_KEY

Happy researching! 🎓
