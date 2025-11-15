# UVA AI Research Assistant - Complete Project Documentation

## 🎯 Project Overview

**UVA AI Research Assistant** is an advanced Retrieval-Augmented Generation (RAG) system specifically designed for University of Virginia researchers. It combines local document processing, web search, GitHub integration, and UVA-specific resource scraping to provide comprehensive research assistance powered by Claude AI.

## 🏗️ System Architecture

### Technology Stack

#### Backend
- **Framework**: FastAPI (Python 3.10+)
- **Database**: PostgreSQL with pgvector extension for vector similarity search
- **ORM**: SQLAlchemy 2.0
- **AI Models**:
  - **Primary LLM**: Anthropic Claude 3.5 Sonnet (via Anthropic API)
  - **Embeddings**: HuggingFace Sentence Transformers (all-MiniLM-L6-v2, 384 dimensions)
  - **Alternative LLM**: OpenAI GPT-4o (configurable)
- **Orchestration**: LangGraph for multi-agent workflows
- **Web Search**: Tavily Search API
- **Authentication**: JWT (JSON Web Tokens)

#### Frontend
- **Framework**: React 18 with TypeScript
- **Routing**: React Router v6
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Build Tool**: Vite

#### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Backend Container**: Python 3.10 with uvicorn
- **Database Container**: pgvector/pgvector:pg16
- **Frontend Container**: Node.js with Nginx

## 🚀 Core Features

### 1. Document Management & RAG Pipeline

#### Document Upload
- **Supported Formats**: PDF documents
- **Multiple File Upload**: Process multiple documents sequentially
- **Document Types**:
  - Research Papers
  - Datasets
  - Results/Reports
  - Embeddings Data
  - General Uploads

#### Processing Pipeline
1. **PDF Parsing**: Extract text using pypdf
2. **Text Chunking**:
   - Chunk size: 1000 characters
   - Overlap: 200 characters
   - Preserves context across chunks
3. **Embedding Generation**:
   - Model: `all-MiniLM-L6-v2` (HuggingFace)
   - Dimension: 384
   - Local processing (no API calls)
   - Stored in pgvector for similarity search
4. **Metadata Storage**:
   - Document name, type, upload date
   - Page numbers
   - File paths (local or Google Drive)
   - User ownership

#### Vector Search
- **Engine**: pgvector extension for PostgreSQL
- **Similarity Metric**: Cosine similarity
- **Search Parameters**:
  - Default similarity threshold: 0.4
  - Max results per query: 5
  - User-scoped search (privacy)

### 2. LangGraph Agentic Workflow

The system uses **LangGraph** to orchestrate a multi-agent RAG workflow with specialized agents for different tasks.

#### Workflow Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER QUESTION                                │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│  NODE 1: ANALYZE QUESTION                                            │
│  ────────────────────────────                                        │
│  • Analyze question complexity (1-5 scale)                           │
│  • Determine information type (factual/analytical/procedural)        │
│  • Identify likely sources needed                                    │
│  • Agent: Planning Agent (Claude)                                    │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│  NODE 2: LOCAL DOCUMENT SEARCH                                       │
│  ──────────────────────────────                                      │
│  • Search user's uploaded documents using vector similarity          │
│  • Retrieve top 5 most relevant chunks                               │
│  • Calculate average similarity score                                │
│  • Agent: Local Search Agent (pgvector)                              │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│  NODE 3: UVA RESOURCE SEARCH                                         │
│  ─────────────────────────────                                       │
│  • Detect UVA-related keywords (uva, virginia, netbadge, etc.)      │
│  • Scrape UVA IT resources (its.virginia.edu)                       │
│  • Extract relevant articles and guides                              │
│  • Agent: UVA Scraper Agent (BeautifulSoup/Selenium)                │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│  NODE 4: GITHUB SEARCH                                               │
│  ───────────────────────                                             │
│  • Detect GitHub-related keywords (repo, code, github, etc.)        │
│  • List user's repositories (if connected)                           │
│  • Search code within user's repos                                   │
│  • Get README files and metadata                                     │
│  • Agent: GitHub MCP Agent (GitHub API)                              │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│  NODE 5: EVALUATE LOCAL SOURCES                                      │
│  ────────────────────────────────                                    │
│  • Count total results from local + UVA + GitHub                     │
│  • Calculate average relevance score                                 │
│  • Decision: Need web search? (Yes if < 3 results or low scores)    │
│  • Agent: Evaluator Agent (Claude)                                   │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
            ┌─────────┴──────────┐
            │                    │
    ┌───────▼────────┐   ┌──────▼──────────┐
    │  Sufficient    │   │  Need More Info │
    │  Information   │   │                 │
    └───────┬────────┘   └──────┬──────────┘
            │                    │
            │                    ▼
            │          ┌─────────────────────────────────────────────┐
            │          │  NODE 6: WEB SEARCH (TAVILY)                │
            │          │  ─────────────────────────────               │
            │          │  • Search internet using Tavily API         │
            │          │  • Retrieve top 5 web results               │
            │          │  • Extract content and URLs                 │
            │          │  • Agent: Web Search Agent (Tavily)         │
            │          └─────────┬───────────────────────────────────┘
            │                    │
            └────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│  NODE 7: GENERATE ANSWER                                             │
│  ─────────────────────────                                           │
│  • Compile context from ALL sources:                                 │
│    - Uploaded documents (with page numbers)                          │
│    - UVA resources (with URLs)                                       │
│    - GitHub repositories (with repo names)                           │
│    - Web search results (with URLs)                                  │
│  • Generate comprehensive answer with citations                      │
│  • Agent: Generator Agent (Claude)                                   │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│  NODE 8: EVALUATE ANSWER                                             │
│  ─────────────────────────                                           │
│  • Assess completeness (0-1 scale)                                   │
│  • Assess accuracy (0-1 scale)                                       │
│  • Assess clarity (0-1 scale)                                        │
│  • Calculate overall confidence score                                │
│  • Decision: Iterate or finish? (Finish if score ≥ 0.8)             │
│  • Agent: Evaluator Agent (Claude)                                   │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
            ┌─────────┴──────────┐
            │                    │
    ┌───────▼────────┐   ┌──────▼──────────┐
    │  High Quality  │   │  Needs Improve  │
    │  (≥ 0.8)       │   │  (< 0.8)        │
    └───────┬────────┘   └──────┬──────────┘
            │                    │
            │                    │ (Currently disabled -
            │                    │  would loop back to
            │                    │  web search for iteration)
            │                    │
            └────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│  NODE 9: SYNTHESIZE FINAL                                            │
│  ──────────────────────────────                                      │
│  • Select best answer (latest iteration)                             │
│  • Compile all sources with metadata:                                │
│    - Document sources (type, title, page, relevance)                │
│    - UVA sources (type, title, URL, relevance)                      │
│    - GitHub sources (type, repo, URL, relevance)                    │
│    - Web sources (type, title, URL, relevance)                      │
│  • Create reasoning steps timeline                                   │
│  • Return complete response with citations                           │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FINAL RESPONSE TO USER                            │
│  ───────────────────────────────────────────                         │
│  • Answer: Comprehensive response                                    │
│  • Confidence: 0.0-1.0 score                                         │
│  • Sources: All citations with links                                 │
│  • Reasoning Steps: Detailed workflow trace (optional)              │
│  • Iterations Used: Number of refinement cycles                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### Agent Descriptions

1. **Planning Agent** (Analyze Question)
   - Uses Claude to understand question intent
   - Determines complexity and required sources
   - Sets workflow strategy

2. **Local Search Agent** (Document Search)
   - Uses pgvector for semantic similarity
   - Returns relevant document chunks
   - Maintains user privacy (user-scoped search)

3. **UVA Scraper Agent** (UVA Resources)
   - Detects UVA-specific queries
   - Scrapes its.virginia.edu
   - Extracts structured information

4. **GitHub MCP Agent** (GitHub Integration)
   - Lists user's repositories
   - Searches code within repos
   - Fetches README files
   - OAuth 2.0 authenticated

5. **Web Search Agent** (Tavily)
   - Searches internet for additional context
   - Only activated when local sources insufficient
   - Returns top 5 relevant results

6. **Generator Agent** (Answer Creation)
   - Uses Claude to synthesize answer
   - Combines all sources
   - Includes proper citations

7. **Evaluator Agent** (Quality Assessment)
   - Assesses answer completeness
   - Calculates confidence score
   - Determines if iteration needed

#### State Management

The workflow maintains a shared state object:
```python
{
    "question": str,           # User's question
    "user_id": int,           # User identifier
    "iteration": int,         # Current iteration number
    "local_results": List,    # Document search results
    "web_results": List,      # Tavily search results
    "uva_results": List,      # UVA resource results
    "github_results": List,   # GitHub search results
    "intermediate_answers": List,  # Answers from each iteration
    "reasoning_steps": List,  # Detailed workflow trace
    "final_answer": str,      # Final synthesized answer
    "confidence_score": float,  # 0.0-1.0 quality score
    "sources": List           # All citations
}
```

#### Conditional Routing

- **After Evaluate Local**: If sufficient info → Generate Answer, else → Web Search
- **After Evaluate Answer**: If high quality (≥0.8) → Synthesize Final, else → Continue (iteration)
- **Max Iterations**: 3 (prevents infinite loops)

### 3. Web Search Integration (Tavily)

#### Features
- **API**: Tavily Search (tavily-python SDK)
- **Triggers**: Automatically activated when local sources insufficient
- **Results**: Top 5 most relevant web pages
- **Data Extracted**:
  - Title
  - Content snippet
  - URL
  - Relevance score

#### Configuration
```env
TAVILY_API_KEY=tvly-dev-***
```

### 4. GitHub Integration (MCP Server)

#### Architecture: Model Context Protocol (MCP)

The GitHub integration uses **MCP (Model Context Protocol)**, a server pattern that provides standardized access to external services.

#### GitHub MCP Server Features

**Class**: `GitHubMCPServer` (backend/app/mcp_servers/github_mcp.py)

**Capabilities**:
1. **List Repositories**
   - Get all user's repositories (public + private)
   - Includes metadata (language, stars, description)
   - Supports pagination

2. **Get Repository Details**
   - Fetch specific repository information
   - Owner, name, description, stats

3. **Search Code**
   - Search code across user's repositories
   - Returns file paths and code snippets

4. **Get File Content**
   - Read file contents from repositories
   - Supports any file type

5. **List Issues**
   - View open/closed issues
   - Filter by state

6. **List Pull Requests**
   - View open/closed PRs
   - Includes PR metadata

7. **Get README**
   - Fetch repository README files
   - Markdown content extraction

#### OAuth 2.0 Flow

**Setup** (One-time, admin):
1. Create GitHub OAuth App at https://github.com/settings/developers
2. Configure callback URL: `http://localhost:5174/settings/github/callback`
3. Add Client ID and Secret to `.env`

**User Flow**:
1. User clicks "Connect GitHub" in Settings
2. Backend generates OAuth URL with state token (CSRF protection)
3. User redirected to GitHub authorization page
4. User grants permissions (scopes: `repo`, `read:user`, `read:org`)
5. GitHub redirects to callback URL with authorization code
6. Backend exchanges code for access token
7. Token stored encrypted in `github_tokens` table
8. User-specific token used for all GitHub API calls

**Security**:
- State token verification prevents CSRF attacks
- Tokens encrypted in database
- User-scoped token access (isolation)
- OAuth 2.0 standard compliance

#### Integration with LangGraph

The GitHub MCP is automatically initialized when:
- User has connected GitHub account
- Question contains GitHub-related keywords
- Workflow reaches GitHub search node

**Example Queries**:
- "List my GitHub repositories"
- "Show my Python projects on GitHub"
- "What's in my research-assistant repo?"
- "Find authentication code in my repos"

### 5. Google Drive Integration (OAuth 2.0)

#### Status
Currently **ON HOLD** per user request. System configured but not active.

#### Implemented Features (Ready for activation)
- OAuth 2.0 authentication flow
- Drive file upload/download
- Folder organization
- Token management
- User-scoped access

#### Fallback: Local Storage
- **Active Storage**: `/Users/chaitanyashahane/Documents/UVA/projects/thunderbolts`
- **Docker Mount**: Mapped to `/app/storage/` in container
- **Structure**:
  ```
  /storage/
  ├── research_paper/
  ├── dataset/
  ├── results/
  ├── embeddings/
  └── uploads/
  ```

### 6. UVA-Specific Resource Scraping

#### UVA Resource Scraper

**Class**: `UVAResourceScraper` (backend/app/services/uva_scraper.py)

**Capabilities**:
- **Target**: https://its.virginia.edu (UVA IT resources)
- **Technology**: BeautifulSoup + Selenium (for dynamic content)
- **Detection**: Triggers on UVA-related keywords
  - uva, virginia, netbadge, onedrive, vpn, campus, its, etc.

**Scraped Information**:
- IT help articles
- Service documentation
- Technical guides
- Support resources

**Integration**:
- Automatically activated by LangGraph workflow
- Results included in answer generation
- UVA-specific citations with URLs

### 7. Authentication & User Management

#### JWT Authentication
- **Algorithm**: HS256
- **Token Expiration**: 43,200 minutes (30 days)
- **Storage**: LocalStorage (frontend)

#### User Model
```python
class User:
    id: int
    username: str (unique)
    email: str (unique, validated)
    hashed_password: str (bcrypt)
    is_admin: bool
    is_active: bool
    created_at: datetime
```

#### Endpoints
- `POST /auth/register` - User registration
- `POST /auth/login` - Login (returns JWT)
- `GET /auth/me` - Get current user info

### 8. Embedding System

#### Local Embedding Generation
- **Model**: `all-MiniLM-L6-v2` (Sentence Transformers)
- **Provider**: HuggingFace
- **Dimension**: 384
- **Benefits**:
  - No API costs
  - Privacy (local processing)
  - Fast inference
  - Consistent quality

#### Configurable via Settings UI
Users can switch between:
- HuggingFace (all-MiniLM-L6-v2)
- OpenAI (text-embedding-3-small)
- Custom models

#### Vector Storage
- **Database**: PostgreSQL with pgvector extension
- **Index**: IVFFlat for fast approximate search
- **Distance Metric**: Cosine similarity

## 📊 Database Schema

### Tables

#### users
```sql
id SERIAL PRIMARY KEY
username VARCHAR UNIQUE NOT NULL
email VARCHAR UNIQUE NOT NULL
hashed_password VARCHAR NOT NULL
is_admin BOOLEAN DEFAULT FALSE
is_active BOOLEAN DEFAULT TRUE
created_at TIMESTAMP DEFAULT NOW()
```

#### documents
```sql
id SERIAL PRIMARY KEY
user_id INTEGER REFERENCES users(id)
filename VARCHAR NOT NULL
file_path VARCHAR NOT NULL
google_drive_id VARCHAR NULL
document_type VARCHAR NOT NULL
upload_date TIMESTAMP DEFAULT NOW()
```

#### embeddings
```sql
id SERIAL PRIMARY KEY
document_id INTEGER REFERENCES documents(id)
chunk_text TEXT NOT NULL
chunk_index INTEGER NOT NULL
page_number INTEGER NULL
embedding VECTOR(384) NOT NULL  -- pgvector
created_at TIMESTAMP DEFAULT NOW()
```

#### queries
```sql
id SERIAL PRIMARY KEY
user_id INTEGER REFERENCES users(id)
question TEXT NOT NULL
answer TEXT NOT NULL
confidence_score FLOAT
sources_used TEXT  -- JSON
reasoning_steps TEXT  -- JSON
iterations_used INTEGER
model_used VARCHAR
created_at TIMESTAMP DEFAULT NOW()
```

#### github_tokens
```sql
id SERIAL PRIMARY KEY
user_id INTEGER REFERENCES users(id) UNIQUE
access_token TEXT NOT NULL
token_type VARCHAR DEFAULT 'bearer'
scope TEXT NULL
created_at TIMESTAMP DEFAULT NOW()
updated_at TIMESTAMP DEFAULT NOW()
```

#### google_drive_tokens (inactive)
```sql
id SERIAL PRIMARY KEY
user_id INTEGER REFERENCES users(id) UNIQUE
access_token TEXT NOT NULL
refresh_token TEXT NOT NULL
token_uri TEXT
expires_at TIMESTAMP
created_at TIMESTAMP DEFAULT NOW()
```

## 🔧 Configuration

### Environment Variables (.env)

#### Database
```env
DATABASE_URL=postgresql://uva_user:uva_password@db:5432/uva_research_assistant
```

#### AI Models
```env
# Anthropic (Primary)
ANTHROPIC_API_KEY=sk-ant-***
ANTHROPIC_MODEL=claude-3-haiku-20240307

# OpenAI (Alternative)
OPENAI_API_KEY=sk-proj-***
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

#### Web Search
```env
TAVILY_API_KEY=tvly-dev-***
```

#### GitHub OAuth
```env
GITHUB_CLIENT_ID=Ov23***
GITHUB_CLIENT_SECRET=0d37***
```

#### Google Drive (Inactive)
```env
GOOGLE_DRIVE_CLIENT_ID=***
GOOGLE_DRIVE_CLIENT_SECRET=***
GOOGLE_DRIVE_ROOT_FOLDER=UVA_Research_Assistant
```

#### Authentication
```env
SECRET_KEY=***
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200
```

#### Application
```env
DEBUG=true
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:5174,http://localhost:3000
```

#### Embeddings
```env
EMBEDDING_PROVIDER=huggingface
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

#### RAG Settings
```env
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
SIMILARITY_THRESHOLD=0.4
MAX_RESULTS=5
```

#### LangGraph
```env
MAX_ITERATIONS=3
ENABLE_DETAILED_REASONING=true
```

#### Storage
```env
LOCAL_STORAGE_PATH=/Users/chaitanyashahane/Documents/UVA/projects/thunderbolts
ENABLE_GOOGLE_DRIVE=false
```

## 🎨 Frontend Features

### Pages

1. **Login/Register**
   - JWT authentication
   - Form validation
   - Error handling

2. **Dashboard**
   - Navigation hub
   - User info display
   - Quick access to features

3. **Upload**
   - Multiple file selection
   - Sequential processing
   - Real-time status updates
   - Progress indicators
   - Error handling per file

4. **Chat/Assistant**
   - Conversational interface
   - Real-time responses
   - Source citations
   - Confidence scores
   - Reasoning steps viewer

5. **Search**
   - Direct document search
   - Similarity-based results
   - Relevance scoring

6. **Settings**
   - **Google Drive Tab**: OAuth connection (inactive)
   - **GitHub Tab**: OAuth connection, test, disconnect
   - **Embedding Settings**: Model selection
   - **System Info**: Configuration overview

### Components

- **GoogleDriveSetup**: OAuth flow UI (inactive)
- **GitHubSetup**: OAuth flow UI, connection management
- **EmbeddingSettings**: Model configuration
- **FileUpload**: Multiple file handling with status tracking

## 🚀 Deployment

### Local Development

#### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.10+ (for backend development)

#### Quick Start
```bash
# Clone repository
cd Team-Thuderbolts

# Start all services
./start.sh

# Or manually
docker-compose up -d

# Access application
# Frontend: http://localhost:5174
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

#### Stop Services
```bash
./stop.sh
# Or
docker-compose down
```

### Production Considerations

1. **Environment**
   - Set `DEBUG=false`
   - Use production database credentials
   - Update `ALLOWED_ORIGINS` to production domains
   - Use strong `SECRET_KEY`

2. **GitHub OAuth**
   - Update callback URL to production domain
   - Create separate production OAuth app

3. **Google Drive** (if activated)
   - Update callback URL
   - Configure OAuth consent screen for production
   - Add production redirect URIs

4. **SSL/TLS**
   - Enable HTTPS
   - Update all URLs to https://
   - Configure SSL certificates

5. **Scaling**
   - Use production WSGI server (Gunicorn)
   - Configure database connection pooling
   - Enable caching (Redis)
   - Load balancing for frontend

## 📈 Performance Optimizations

### Backend
- **Async Processing**: All LangGraph nodes use async/await
- **Connection Pooling**: SQLAlchemy connection pool
- **Vector Indexing**: IVFFlat index on embeddings
- **Batch Processing**: Document chunks processed in batches
- **Caching**: LLM responses could be cached (future enhancement)

### Frontend
- **Code Splitting**: React lazy loading
- **Memoization**: React.memo for expensive components
- **Debouncing**: Search input debouncing
- **Optimistic Updates**: Immediate UI feedback

### Database
- **Indexes**: Primary keys, foreign keys, vector indexes
- **Query Optimization**: Efficient joins, selective loading
- **pgvector**: Approximate nearest neighbor search

## 🔒 Security Features

### Authentication
- JWT token-based authentication
- Bcrypt password hashing
- Token expiration
- Secure token storage

### Authorization
- User-scoped data access
- Admin role separation
- OAuth token isolation

### Data Privacy
- User documents isolated by user_id
- Encrypted OAuth tokens
- No data sharing between users

### API Security
- CORS configuration
- Input validation (Pydantic)
- SQL injection prevention (ORM)
- XSS protection

## 🐛 Error Handling

### Backend
- Try-catch blocks in all async operations
- Graceful degradation (services fail independently)
- Detailed logging (Python logging module)
- HTTP exception handling with proper status codes

### Frontend
- Error boundaries (React)
- User-friendly error messages
- Retry mechanisms
- Loading states

### Workflow
- Individual node error handling
- Workflow continues if non-critical node fails
- Fallback responses when errors occur

## 📝 Logging & Monitoring

### Backend Logging
```python
logger = logging.getLogger(__name__)
logger.info("GitHub MCP initialized")
logger.warning("Web search failed, using cached results")
logger.error("Database connection failed")
```

### Workflow Tracing
- Each node adds reasoning step to state
- Complete workflow trace available
- Timestamps for performance analysis
- Debugging information preserved

### Docker Logs
```bash
# View all logs
docker-compose logs

# Follow backend logs
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail 100 backend
```

## 🎯 Use Cases

### Research Assistance
- **Query**: "Summarize my research paper on machine learning"
- **Workflow**: Local Search → Generate Answer
- **Sources**: Uploaded research paper

### UVA IT Support
- **Query**: "How do I connect to UVA VPN?"
- **Workflow**: UVA Search → Web Search → Generate Answer
- **Sources**: UVA IT resources, web guides

### Code Reference
- **Query**: "List my Python projects on GitHub"
- **Workflow**: GitHub Search → Generate Answer
- **Sources**: User's GitHub repositories

### Comprehensive Research
- **Query**: "What are the latest developments in quantum computing?"
- **Workflow**: Local Search → UVA Search → GitHub Search → Web Search → Generate Answer
- **Sources**: Documents, UVA resources, GitHub repos, web articles

## 🔮 Future Enhancements

### Planned Features
1. **Google Drive Activation**: Complete OAuth flow testing
2. **Multi-modal Support**: Image analysis in documents
3. **Collaborative Features**: Shared workspaces
4. **Advanced Analytics**: Usage statistics, query insights
5. **Custom LLM Integration**: Support for more models
6. **Voice Interface**: Speech-to-text for queries
7. **Export Features**: PDF/Word report generation
8. **Notification System**: Real-time updates
9. **Mobile App**: React Native implementation
10. **API Rate Limiting**: Request throttling

### Optimization Opportunities
1. **Response Caching**: Redis for frequent queries
2. **Streaming Responses**: Real-time answer generation
3. **Parallel Processing**: Concurrent node execution in LangGraph
4. **Smart Prefetching**: Predictive resource loading
5. **Compression**: Response payload optimization

## 📚 Documentation

### Available Guides
- **README.md**: Quick start guide
- **SETUP_GUIDE.md**: Detailed installation instructions
- **GITHUB_OAUTH_SETUP.md**: GitHub integration setup
- **QUICKSTART.md**: Getting started tutorial
- **FEATURES.md**: Feature overview
- **PROJECT_DETAILS.md**: This document

### API Documentation
- **Interactive Docs**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc (Alternative API docs)

## 🤝 Contributing

### Development Workflow
1. Fork repository
2. Create feature branch
3. Make changes
4. Test locally
5. Submit pull request

### Code Style
- **Python**: PEP 8, type hints
- **TypeScript**: ESLint + Prettier
- **Commits**: Conventional commits

## 📞 Support

### Resources
- **GitHub Issues**: Bug reports and feature requests
- **Documentation**: Comprehensive guides
- **API Docs**: Interactive API explorer

## 📄 License

Proprietary - University of Virginia Research Project

## 👥 Team

**Team Thunderbolts**
- Chaitanya Shahane (@ChaitanyaRS06)

---

**Version**: 1.0.0
**Last Updated**: November 2025
**Powered by**: Claude 3.5 Sonnet, LangGraph, FastAPI, React
