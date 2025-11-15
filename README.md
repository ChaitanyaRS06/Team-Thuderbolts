# UVA AI Research Assistant

A smart AI research assistant designed specifically for University of Virginia (UVA) researchers and faculty. This application provides an intelligent, user-friendly interface for managing research documents, searching UVA resources, and getting AI-powered answers using multiple LLMs (GPT-4 and Claude 3.5 Sonnet).

## Features

### Core Features

#### 1. **Multi-LLM Support**
- **OpenAI GPT-4**: High-quality general-purpose AI model
- **Anthropic Claude 3.5 Sonnet**: Advanced reasoning and analysis
- Switch between models seamlessly based on your needs

#### 2. **Intelligent Document Management**
- **Categorized Upload**: Upload documents as:
  - Research Papers
  - Datasets
  - Results
  - Other
- **OneDrive Integration**: Automatic sync to UVA OneDrive via MCP server
- **Automated Processing**: PDF text extraction and intelligent chunking
- **Semantic Indexing**: Advanced vector embeddings for semantic search

#### 3. **Multi-Agent RAG System (LangGraph)**
The system uses multiple specialized AI agents:
- **Analyzer Agent**: Analyzes question complexity and requirements
- **Search Agent**: Retrieves information from local documents
- **UVA Resource Agent**: Searches UVA IT resources and guides
- **Web Search Agent**: Performs live internet search using Tavily
- **Generator Agent**: Creates comprehensive answers from retrieved context
- **Evaluator Agent**: Assesses answer quality and completeness
- **Synthesizer Agent**: Combines sources and creates final response

#### 4. **UVA-Specific Features**
- **UVA IT Resource Search**: Access indexed UVA resources:
  - OneDrive setup guides
  - VPN configuration
  - NetBadge authentication
  - Security policies
  - IT best practices
- **Campus Network Optimized**: Designed to work within UVA firewall
- **UVA Branding**: UVA orange and blue theme

#### 5. **User-Friendly Interface**
Designed for non-technical users:
- Simple, intuitive navigation
- Clear visual feedback
- Step-by-step guidance
- Confidence scores on answers
- Source citations with links
- Reasoning transparency (optional)

#### 6. **Advanced Search Capabilities**
- **Hybrid Search**: Combines local documents, UVA resources, and web search
- **Semantic Similarity**: pgvector-powered cosine similarity search
- **Multi-Source Integration**: Intelligently combines information from:
  - Uploaded research documents
  - UVA IT resources
  - Live web search results

#### 7. **OneDrive MCP Server**
Model Context Protocol (MCP) server for OneDrive integration:
- Automatic file upload to UVA OneDrive
- Organized folder structure (dataset/research_paper/results)
- Secure Microsoft Graph API integration
- Background sync

## Technology Stack

### Backend
- **FastAPI**: High-performance Python web framework
- **PostgreSQL + pgvector**: Vector database for semantic search
- **LangGraph**: Multi-agent workflow orchestration
- **LangChain**: RAG pipeline and tool integration
- **OpenAI API**: GPT-4 and embeddings
- **Anthropic API**: Claude 3.5 Sonnet
- **Tavily API**: Real-time web search
- **Microsoft Graph API**: OneDrive integration
- **SQLAlchemy**: ORM for database operations
- **JWT**: Secure authentication

### Frontend
- **React 18**: Modern UI framework
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **Vite**: Fast build tool
- **React Router**: Client-side routing
- **Axios**: HTTP client
- **Lucide Icons**: Beautiful icon library

### Infrastructure
- **Docker Compose**: Multi-service orchestration
- **PostgreSQL 16 with pgvector**: Vector similarity search
- **NGINX**: (Optional) Reverse proxy

## Project Structure

```
Team-Thunderbolts/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI application entry
│   │   ├── config.py                  # Configuration settings
│   │   ├── models.py                  # SQLAlchemy database models
│   │   ├── database.py                # Database connection
│   │   ├── auth.py                    # JWT authentication
│   │   ├── routers/                   # API endpoints
│   │   │   ├── auth.py                # Authentication routes
│   │   │   ├── documents.py           # Document management
│   │   │   ├── embeddings.py          # Embedding generation
│   │   │   ├── search.py              # Semantic search
│   │   │   ├── rag.py                 # RAG question answering
│   │   │   └── uva_resources.py       # UVA resource search
│   │   ├── services/                  # Business logic
│   │   │   ├── pdf_processing.py      # PDF extraction
│   │   │   ├── embeddings.py          # OpenAI embeddings
│   │   │   ├── search.py              # Vector search
│   │   │   ├── web_search.py          # Tavily integration
│   │   │   ├── uva_scraper.py         # UVA resource scraper
│   │   │   ├── langgraph_workflow.py  # Multi-agent workflow
│   │   │   └── onedrive_service.py    # OneDrive wrapper
│   │   ├── mcp_servers/               # MCP servers
│   │   │   └── onedrive_mcp.py        # OneDrive MCP server
│   │   └── utils/                     # Utilities
│   └── requirements.txt               # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.tsx                    # Main app component
│   │   ├── main.tsx                   # Entry point
│   │   ├── lib/
│   │   │   └── api.ts                 # API client
│   │   └── pages/                     # React pages
│   │       ├── Login.tsx              # Authentication
│   │       ├── Dashboard.tsx          # Main dashboard
│   │       ├── Upload.tsx             # File upload
│   │       ├── Documents.tsx          # Document management
│   │       ├── Assistant.tsx          # AI chat interface
│   │       └── UVAResources.tsx       # UVA resource search
│   ├── package.json                   # Node.js dependencies
│   └── tailwind.config.js             # Tailwind configuration
├── docker-compose.yml                 # Service orchestration
├── Dockerfile.backend                 # Backend container
├── Dockerfile.frontend                # Frontend container
├── init-db.sql                        # Database initialization
├── .env.example                       # Environment template
└── README.md                          # This file
```

## Prerequisites

- **Docker** and **Docker Compose** installed
- **API Keys**:
  - OpenAI API key (required)
  - Anthropic API key (required)
  - Tavily API key (required)
  - Microsoft Graph API credentials (optional, for OneDrive)

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Team-Thunderbolts
```

### 2. Environment Setup

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-...your-key-here

# Anthropic Configuration
ANTHROPIC_API_KEY=sk-ant-...your-key-here

# Tavily Web Search
TAVILY_API_KEY=tvly-...your-key-here

# Microsoft Graph/OneDrive (Optional)
MICROSOFT_CLIENT_ID=your-client-id
MICROSOFT_CLIENT_SECRET=your-client-secret
MICROSOFT_TENANT_ID=your-tenant-id

# JWT Secret
SECRET_KEY=your-secret-key-change-this-in-production

# Database
DATABASE_URL=postgresql://uva_user:uva_password@db:5432/uva_research_assistant
```

### 3. Start the Application

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 4. Access the Application

- **Frontend**: http://localhost:5174
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 5. Create an Account

1. Go to http://localhost:5174
2. Click "Sign up"
3. Enter your email, name, and password
4. Start using the assistant!

## Usage Guide

### For Non-Technical Users

#### Step 1: Upload Your Documents

1. Click **"Upload Documents"** in the sidebar
2. Select document type:
   - **Research Paper**: Published papers, articles
   - **Dataset**: Research data files
   - **Results**: Experimental results
   - **Other**: Any other documents
3. Click or drag to upload PDF file
4. Click **"Upload and Process"**
5. Wait for processing to complete (file is uploaded, text extracted, and indexed)

#### Step 2: Ask Questions

1. Click **"Ask Questions"** in the sidebar
2. Choose your preferred AI model (GPT-4 or Claude)
3. Type your question in the input box
4. Click **"Send"** or press Enter
5. The AI will:
   - Search your uploaded documents
   - Check UVA resources if relevant
   - Search the web if needed
   - Provide an answer with source citations

#### Step 3: Search UVA Resources

1. Click **"UVA Resources"** in the sidebar
2. Select resource type (IT Guides, OneDrive, VPN, etc.)
3. Enter your question (e.g., "How do I set up OneDrive?")
4. View indexed UVA IT resources with relevance scores

## API Endpoints

### Authentication
- `POST /auth/register` - Create new account
- `POST /auth/login` - Login and get JWT token
- `GET /auth/me` - Get current user info

### Documents
- `GET /documents/` - List user's documents
- `POST /documents/upload` - Upload PDF document
- `POST /documents/{id}/process` - Extract text and create chunks
- `DELETE /documents/{id}` - Delete document

### Embeddings
- `POST /embeddings/generate/{document_id}` - Generate vector embeddings
- `GET /embeddings/stats` - Get embedding statistics

### Search
- `POST /search/` - Semantic similarity search

### RAG (AI Question Answering)
- `POST /rag/ask` - Ask a question using multi-agent RAG
- `GET /rag/history` - Get query history

### UVA Resources
- `POST /uva/search` - Search UVA resources
- `POST /uva/scrape-it-resources` - Scrape and index UVA IT resources (admin only)

## Multi-Agent Workflow

The LangGraph workflow orchestrates multiple specialized agents:

```
User Question
    ↓
[Analyzer Agent] → Analyzes complexity
    ↓
[Local Search Agent] → Searches uploaded documents
    ↓
[UVA Resource Agent] → Searches UVA IT resources
    ↓
[Evaluator Agent] → Assesses if more info needed
    ↓
[Web Search Agent] → Performs live web search (if needed)
    ↓
[Generator Agent] → Creates answer from all sources
    ↓
[Evaluator Agent] → Assesses answer quality
    ↓
[Synthesizer Agent] → Compiles final response with citations
    ↓
Answer + Sources + Confidence Score
```

## Development

### Backend Development

```bash
# Enter backend container
docker exec -it uva-research-assistant-backend bash

# Install dependencies
pip install -r requirements.txt

# Run locally (outside Docker)
cd backend
uvicorn app.main:app --reload
```

### Frontend Development

```bash
# Enter frontend container
docker exec -it uva-research-assistant-frontend sh

# Install dependencies
npm install

# Run locally (outside Docker)
cd frontend
npm run dev
```

### Database Operations

```bash
# Connect to PostgreSQL
docker exec -it uva-research-assistant-db psql -U uva_user -d uva_research_assistant

# View tables
\dt

# Check documents
SELECT id, original_filename, status FROM documents;

# Check embeddings
SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL;
```

## Troubleshooting

### Backend won't start

```bash
# Check logs
docker-compose logs backend

# Verify API keys are set
docker exec -it uva-research-assistant-backend env | grep API_KEY
```

### Frontend can't connect

```bash
# Check CORS settings in backend
# Verify backend is running
docker-compose ps

# Check frontend proxy config in vite.config.ts
```

### Database connection issues

```bash
# Reset database
docker-compose down -v
docker-compose up -d db
# Wait for DB to be ready
docker-compose up -d backend
```

### PDF processing fails

```bash
# Check PDF file is valid
# Check backend logs
docker-compose logs backend | grep -i "pdf"
```

## Security Considerations

- **JWT Authentication**: Secure token-based auth
- **User Isolation**: Users only access their own documents
- **API Key Management**: Never commit `.env` to version control
- **CORS Protection**: Configured allowed origins
- **Input Validation**: Comprehensive request validation
- **SQL Injection Protection**: SQLAlchemy ORM prevents injection

## Performance & Scaling

### Current Capacity
- **Documents**: Unlimited per user
- **Vector Search**: Sub-second similarity search
- **Concurrent Users**: Scales with container resources
- **API Throughput**: ~100 requests/second

### Optimization Tips
- Use pgvector indexing for fast searches
- Adjust chunk size for optimal retrieval
- Cache embeddings in database
- Use connection pooling

## Future Enhancements

- [ ] GitHub integration via MCP server
- [ ] Multi-file upload
- [ ] Export chat history
- [ ] Advanced analytics dashboard
- [ ] Mobile app
- [ ] Voice input/output
- [ ] Collaborative features
- [ ] Custom model fine-tuning

## Contributing

### Code Standards
- **Backend**: Follow PEP 8 and FastAPI conventions
- **Frontend**: Use TypeScript strict mode
- **Documentation**: Update README for new features
- **Testing**: Add tests for new endpoints

## License

This project is developed for University of Virginia research purposes.

## Support

For issues, questions, or feature requests:
- Check the logs: `docker-compose logs -f`
- Review API docs: http://localhost:8000/docs
- Contact: UVA IT Support

---

**Built for UVA researchers with advanced AI capabilities**
