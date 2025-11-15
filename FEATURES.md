# Features Documentation

Complete list of features in the UVA AI Research Assistant, updated as new features are added.

## Current Features (v1.0)

### 1. Authentication & User Management

**Features:**
- User registration with email and password
- Secure JWT-based authentication
- User profile management
- Role-based access control (admin/user)

**Technical Details:**
- JWT tokens with configurable expiration
- bcrypt password hashing
- Session management

---

### 2. Multi-LLM Support

**Supported Models:**
- **OpenAI GPT-4** (`gpt-4o`)
  - Best for: General-purpose queries, creative writing
  - Strengths: Broad knowledge, conversational
- **Anthropic Claude 3.5 Sonnet** (`claude-3-5-sonnet-20241022`)
  - Best for: Complex reasoning, analytical tasks
  - Strengths: Long context, detailed analysis

**Features:**
- Seamless model switching from UI
- Model-specific optimizations
- Unified API interface

---

### 3. Document Management

#### Upload System
- **Supported Format**: PDF files
- **Categorization**:
  - Dataset: Research data files
  - Research Paper: Published papers, articles
  - Results: Experimental results
  - Other: Miscellaneous documents

#### Processing Pipeline
1. **Upload**: File uploaded to server
2. **OneDrive Sync**: Automatic sync to UVA OneDrive (if configured)
3. **Text Extraction**: PyPDF extracts text from PDF
4. **Chunking**: Text split into semantic chunks (1000 chars, 200 overlap)
5. **Embedding**: OpenAI embeddings generated for each chunk
6. **Indexing**: Stored in pgvector for semantic search

#### Status Tracking
- `uploaded`: File received
- `processed`: Text extracted and chunked
- `embedded`: Ready for search
- `failed`: Error occurred

---

### 4. OneDrive MCP Server

**Model Context Protocol (MCP) Server for OneDrive**

#### Features:
- Automatic file upload to UVA OneDrive
- Organized folder structure by document type
- Background sync (non-blocking)
- Microsoft Graph API integration

#### Tools Provided:
- `upload_to_onedrive`: Upload files
- `list_onedrive_files`: List files in folders
- `download_from_onedrive`: Download files

#### Configuration:
Requires Microsoft Graph API credentials:
- Client ID
- Client Secret
- Tenant ID

---

### 5. Multi-Agent RAG System (LangGraph)

**7 Specialized Agents:**

#### 1. Analyzer Agent
- **Role**: Analyzes question complexity
- **Output**: Complexity score, required sources
- **Use**: Plans the search strategy

#### 2. Local Search Agent
- **Role**: Searches uploaded documents
- **Technology**: pgvector cosine similarity
- **Output**: Top 5 relevant document chunks

#### 3. UVA Resource Agent
- **Role**: Searches UVA IT resources
- **Trigger**: Keywords like "UVA", "OneDrive", "VPN"
- **Output**: Relevant UVA guides and policies

#### 4. Evaluator Agent (Local)
- **Role**: Assesses if local results are sufficient
- **Criteria**: Result count, similarity scores
- **Decision**: Proceed to web search or generate answer

#### 5. Web Search Agent
- **Role**: Performs live internet search
- **Technology**: Tavily API
- **Output**: Up to 5 web results with content

#### 6. Generator Agent
- **Role**: Creates answer from all context
- **Input**: Local docs + UVA resources + Web results
- **Output**: Comprehensive answer with citations

#### 7. Evaluator Agent (Answer)
- **Role**: Assesses answer quality
- **Metrics**: Completeness, accuracy, clarity
- **Output**: Confidence score (0-1)

**Workflow:**
```
Question → Analyzer → Local Search → UVA Search →
Evaluate → [Web Search?] → Generate → Evaluate → Synthesize
```

---

### 6. Semantic Search

**Technology:**
- PostgreSQL with pgvector extension
- Cosine similarity search
- OpenAI text-embedding-3-small (1536 dimensions)

**Features:**
- Sub-second search on 1000+ chunks
- Configurable similarity threshold (default: 0.4)
- Ranked results with scores
- Page number tracking

**Query Types Supported:**
- Factual questions
- Conceptual queries
- Similarity-based retrieval

---

### 7. Web Search Integration (Tavily)

**Features:**
- Real-time web search
- AI-generated summaries
- Source attribution
- Relevance scoring

**Search Modes:**
- `basic`: Quick search
- `advanced`: Deep search with more sources

**Use Cases:**
- Current events
- Information not in documents
- Fact-checking
- Supplementary information

---

### 8. UVA Resource Scraper

**Indexed Resources:**
- UVA IT guides
- OneDrive documentation
- VPN setup instructions
- NetBadge authentication guides
- Security policies

**Features:**
- Web scraping with BeautifulSoup
- Semantic indexing
- Relevance scoring
- Auto-updating (admin only)

**Resource Types:**
- `onedrive_guide`
- `vpn_guide`
- `security_policy`
- `authentication_guide`
- `it_guide`

---

### 9. User Interface

#### Design Principles:
- **Simplicity**: Clear navigation, minimal clutter
- **Visual Feedback**: Loading states, progress indicators
- **Accessibility**: High contrast, readable fonts
- **UVA Branding**: Orange and blue color scheme

#### Pages:

**Login/Register**
- Simple authentication
- Error handling
- Account creation

**Dashboard**
- Sidebar navigation
- User profile display
- Quick access to all features

**Upload Page**
- Document type selection
- Drag-and-drop upload
- Progress tracking
- Success/error messages

**Documents Page**
- List all documents
- Status indicators
- File size display
- Delete functionality

**Assistant Page (Main Chat)**
- Message history
- Model selection
- Source citations
- Confidence scores
- Reasoning steps (optional)
- Real-time typing indicator

**UVA Resources Page**
- Resource type filters
- Search interface
- Relevance scores
- Direct links to UVA sites

---

### 10. Answer Quality Features

**Source Citations:**
- Document name and page number
- Web URLs
- UVA resource links
- Relevance scores

**Confidence Scoring:**
- 0-1 scale
- Based on:
  - Source quality
  - Result count
  - Similarity scores
  - Answer completeness

**Reasoning Transparency:**
- Step-by-step workflow
- Agent actions
- Decision points
- Timestamps

---

### 11. Security Features

**Authentication:**
- JWT with expiration
- bcrypt password hashing
- Secure token storage

**Authorization:**
- User isolation (only see own documents)
- Admin-only endpoints
- Role-based access

**Data Protection:**
- CORS configuration
- Input validation
- SQL injection prevention (SQLAlchemy ORM)
- Environment variable protection

---

### 12. Performance Optimizations

**Database:**
- pgvector indexing
- Connection pooling
- Batch processing

**API:**
- Async/await support
- Concurrent requests
- Caching strategies

**Frontend:**
- Code splitting
- Lazy loading
- Optimized builds

---

## Planned Features (Roadmap)

### Short Term (Next Release)

- [ ] **GitHub Integration**
  - MCP server for GitHub
  - Code repository search
  - Issue/PR integration

- [ ] **Multi-file Upload**
  - Bulk upload
  - Folder upload
  - Progress tracking

- [ ] **Export Features**
  - Export chat history
  - Download answers as PDF
  - Citation export

### Medium Term

- [ ] **Advanced Analytics**
  - Usage statistics
  - Popular queries
  - Document engagement

- [ ] **Collaboration**
  - Share documents with other users
  - Team workspaces
  - Collaborative annotations

- [ ] **Voice Interface**
  - Voice input for questions
  - Text-to-speech answers
  - Accessibility features

### Long Term

- [ ] **Mobile App**
  - iOS and Android
  - Native features
  - Offline mode

- [ ] **Custom Model Fine-tuning**
  - Train on user's documents
  - Domain-specific models
  - Improved accuracy

- [ ] **Advanced Visualizations**
  - Document relationship graphs
  - Citation networks
  - Topic modeling

- [ ] **Integration Ecosystem**
  - Slack integration
  - Microsoft Teams
  - Zotero/Mendeley
  - ORCID

---

## Feature Requests

To request a new feature:
1. Check if it's already in the roadmap
2. Open an issue on GitHub
3. Describe the use case
4. Explain the benefit

## Feature Updates

This document is updated with each release. Check the version number at the top to ensure you're viewing the latest features.

Last Updated: 2025-01-15
Version: 1.0.0
