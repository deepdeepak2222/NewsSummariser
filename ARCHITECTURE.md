# News Summarizer - End-to-End Architecture

## 🏗️ System Overview

The News Summarizer is a full-stack web application that fetches news articles from Google News RSS feeds, summarizes them using AI models (OpenAI GPT or open-source models via Ollama), and presents them in a user-friendly interface with multi-language support (Hindi/English).

---

## 📐 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Browser                            │
│                    https://news.deestore.in                     │
└───────────────────────────┬───────────────────────────────────┘
                             │ HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Cloudflare Tunnel                            │
│         (Routes domain → localhost:8501)                         │
└───────────────────────────┬───────────────────────────────────┘
                             │ HTTP
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Kubernetes Port Forward                             │
│         (Routes localhost:8501 → Pod:8501)                       │
└───────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Kubernetes Pod (Docker Container)                   │
│  ┌─────────────────────────┐  ┌──────────────────────────┐   │
│  │   Streamlit Frontend     │  │   FastAPI Backend         │   │
│  │   (Port 8501)            │  │   (Port 8000)             │   │
│  │                          │  │                          │   │
│  │  - UI Components         │  │  - /summarize endpoint   │   │
│  │  - User Input            │  │  - /articles endpoint     │   │
│  │  - Display Results       │◄─┤  - /health endpoint       │   │
│  └─────────────────────────┘  └───────────┬──────────────┘   │
└─────────────────────────────────────────────┼───────────────────┘
                                             │
                                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Application Logic Layer                             │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  news_summariser/summarise.py                             │ │
│  │  - Orchestrates news fetching & summarization             │ │
│  └───────────────────┬──────────────────────────────────────┘ │
│                      │                                          │
│  ┌───────────────────▼──────────────────────────────────────┐ │
│  │  news_summariser/news_fetcher.py                          │ │
│  │  - Fetches articles from Google News RSS                  │ │
│  │  - Scrapes article content                               │ │
│  │  - Cleans HTML content                                   │ │
│  └───────────────────┬──────────────────────────────────────┘ │
│                      │                                          │
│  ┌───────────────────▼──────────────────────────────────────┐ │
│  │  ai/query_model_unified.py                                │ │
│  │  - Unified interface for OpenAI and Ollama                │ │
│  │  - Auto-detects provider from env vars                    │ │
│  │  - Automatic fallback to OpenAI if Ollama fails           │ │
│  └───────────────────┬──────────────────────────────────────┘ │
│                      │                                          │
│  ┌───────────────────▼──────────────────────────────────────┐ │
│  │  ai/query_model.py (OpenAI)                               │ │
│  │  ai/query_model_ollama.py (Ollama)                        │ │
│  └───────────────────┬──────────────────────────────────────┘ │
└───────────────────────┼──────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    External Services                             │
│  ┌──────────────────────┐  ┌──────────────────────────────┐  │
│  │   Google News RSS     │  │      AI Providers             │  │
│  │   (news.google.com)   │  │  • OpenAI API (paid)          │  │
│  └──────────────────────┘  │  • Ollama (free, local)        │  │
│                            │    - Mistral 7B (recommended)   │  │
│                            │    - Llama 3.1 8B              │  │
│                            │    - Qwen 2.5 7B               │  │
│                            └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 End-to-End User Flow

### Step 1: User Access
1. User opens browser and navigates to `https://news.deestore.in`
2. **Cloudflare Tunnel** receives the HTTPS request
3. Tunnel routes to `localhost:8501` (where port-forwarding is active)
4. **Kubernetes Port-Forward** routes to the pod's port 8501
5. **Streamlit** serves the UI

### Step 2: User Input
1. User enters:
   - **Query**: "gaya" (or any news topic)
   - **Location**: "Bihar" (default)
   - **Max Articles**: 5 (slider)
   - **Language**: Hindi/English
2. User clicks **"Get Summary"** button

### Step 3: Frontend Processing (`app.py`)
1. Streamlit captures user input
2. Makes HTTP POST request to FastAPI backend:
   ```python
   POST http://localhost:8000/summarize
   {
     "query": "gaya",
     "location": "Bihar",
     "max_articles": 5,
     "language": "Hindi"
   }
   ```
3. Shows loading spinner while waiting

### Step 4: Backend Processing (`api.py`)
1. FastAPI receives request at `/summarize` endpoint
2. Calls `fetch_news_articles()` to get articles first
3. If articles found, calls `get_news()` for summarization
4. Returns response with summary and article list

### Step 5: News Fetching (`news_fetcher.py`)
1. **Builds RSS URL**:
   ```
   https://news.google.com/rss/search?q=Bihar+gaya&hl=en-IN&gl=IN&ceid=IN:en
   ```
2. **Parses RSS feed** using `feedparser` library
3. **Extracts articles** (up to `max_articles`):
   - Title
   - Link (URL)
   - Summary/Description
4. **Cleans HTML** from titles and summaries using BeautifulSoup
5. Returns list of article dictionaries

### Step 6: Summarization (`summarise.py`)
1. **Formats articles** for AI processing:
   ```
   --- Article 1 ---
   Title: [article title]
   Summary: [article summary]
   
   --- Article 2 ---
   ...
   ```
2. **Selects system prompt** based on language:
   - Hindi: `SUMMARISE_NEWS_IN_BIHAR_STATE_IN_HINDI_LANGUAGE_SYSTEM_PROMPT`
   - English: `SUMMARISE_NEWS_IN_ENGLISH_LANGUAGE_SYSTEM_PROMPT`
3. **Creates user prompt** with formatted articles
4. **Calls OpenAI API** via `query_model()`

### Step 7: AI Processing (`ai/query_model_unified.py`)
1. **Determines provider** from `AI_PROVIDER` env var (default: 'openai')
2. **Routes to appropriate provider**:

   **If OpenAI:**
   - Loads API key from `.env` or Kubernetes Secret
   - Initializes OpenAI client
   - Sends request to `api.openai.com`
   - Models: `gpt-4o`, `gpt-4o-mini`

   **If Ollama:**
   - Connects to Ollama API (default: `http://localhost:11434` or `http://ollama-service:11434` in K8s)
   - Sends request to local/self-hosted Ollama instance
   - Models: `mistral:7b`, `llama3.1:8b`, `qwen2.5:7b`
   - Falls back to OpenAI if Ollama fails

3. **Returns** AI-generated summary in requested language

### Step 8: Response Back to Frontend
1. FastAPI returns JSON response:
   ```json
   {
     "summary": "[AI-generated summary in Hindi/English]",
     "articles_found": 5,
     "query": "Bihar gaya",
     "articles": [
       {
         "title": "...",
         "link": "...",
         "summary": "..."
       },
       ...
     ]
   }
   ```
2. Streamlit receives response
3. **Stores in session state** (persists across reruns)

### Step 9: Display Results (`app.py`)
1. **Shows summary** in a styled box
2. **Displays metadata**:
   - Number of articles found
   - Search query used
3. **Lists individual articles** with expandable sections
4. **For Hindi language**:
   - Translates article titles using AI
   - Translates article summaries using AI
   - Caches translations in session state
5. **For each article**:
   - Shows translated title and summary
   - Provides "Read Full Article (Translated)" button
   - Provides link to original article

### Step 10: Full Article Translation (Optional)
1. User clicks **"Read Full Article (Translated)"**
2. Streamlit fetches full article content:
   - Calls `get_article_content()` from `news_fetcher.py`
   - Scrapes article HTML using BeautifulSoup
   - Extracts main content
3. **Translates full article** using OpenAI:
   - Sends article content to AI
   - Gets Hindi/English translation
4. **Displays translated article** in expandable section

---

## 🧩 Component Details

### 1. **Streamlit Frontend** (`app.py`)
- **Purpose**: User interface
- **Port**: 8501
- **Features**:
  - Sidebar with settings (location, max articles, language)
  - Main query input area
  - Results display with expandable articles
  - Session state management (persists data across reruns)
  - Dynamic UI text based on language selection
  - Article translation on-demand

### 2. **FastAPI Backend** (`api.py`)
- **Purpose**: REST API server
- **Port**: 8000
- **Endpoints**:
  - `GET /health` - Health check
  - `POST /summarize` - Main summarization endpoint
  - `GET /articles` - Fetch articles without summarization
- **Features**:
  - CORS enabled for Streamlit
  - Error handling
  - Pydantic models for request/response validation

### 3. **News Fetcher** (`news_summariser/news_fetcher.py`)
- **Purpose**: Fetch news from Google News RSS
- **Functions**:
  - `fetch_news_articles()` - Fetches articles from RSS feed
  - `get_article_content()` - Scrapes full article content
  - `clean_html_text()` - Removes HTML tags
  - `format_articles_for_summarization()` - Formats articles for AI

### 4. **Summarization Logic** (`news_summariser/summarise.py`)
- **Purpose**: Orchestrates news fetching and AI summarization
- **Function**: `get_news(user_prompt, location, max_articles, language)`
- **Process**:
  1. Builds search query from user input
  2. Fetches articles
  3. Formats articles for AI
  4. Selects appropriate system prompt
  5. Calls AI model
  6. Returns summary

### 5. **AI Integration** (`ai/query_model_unified.py`)
- **Purpose**: Unified interface for AI models (OpenAI or Ollama)
- **Function**: `query_model(user_prompt, system_prompt, model, provider)`
- **Providers**:
  - **OpenAI**: `gpt-4o`, `gpt-4o-mini` (paid, cloud-based)
  - **Ollama**: `mistral:7b`, `llama3.1:8b`, `qwen2.5:7b` (free, self-hosted)
- **Features**:
  - Auto-detects provider from `AI_PROVIDER` env var
  - Automatic fallback to OpenAI if Ollama fails
  - Supports both local and Kubernetes deployments

### 6. **Constants** (`news_summariser/constants.py`)
- **Purpose**: System prompts for AI
- **Functions**:
  - `get_system_prompt(language)` - Returns prompt based on language

---

## 🚀 Deployment Architecture

### Container Setup (`Dockerfile`)
1. **Base Image**: `python:3.9-slim`
2. **Install Dependencies**: From `requirements.txt`
3. **Copy Code**: Application files
4. **Start Script**: `start.sh` runs both services

### Startup Script (`start.sh`)
```bash
# Start FastAPI in background
python api.py &

# Start Streamlit (foreground)
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
```

### Kubernetes Deployment

#### Option 1: Minikube (Local Development)
1. **Deployment**: Runs 2 replicas of the container
2. **Service**: NodePort (minikube)
3. **Secrets**: Stores OpenAI API key (for fallback)
4. **ConfigMap**: Application configuration
5. **Ollama Deployment** (optional): Separate pod running Ollama with Mistral 7B
   - Resources: 3-4GB RAM, 1-2 CPU cores (limited by Docker Desktop)
   - Service: `ollama-service:11434` (internal)
   - Model: Pre-loaded Mistral 7B (~4GB)

#### Option 2: Oracle Cloud Infrastructure (OCI) - Production (Free Tier)
1. **VM**: ARM-based VM (Ampere A1) with 24GB RAM, 4 OCPUs (free forever)
2. **Kubernetes**: k3s (lightweight Kubernetes)
3. **Deployment**: Runs 2 replicas of the container
4. **Service**: LoadBalancer (OCI provides public IP)
5. **Secrets**: Stores OpenAI API key (for fallback)
6. **ConfigMap**: Application configuration
7. **Ollama Deployment**: Separate pod running Ollama with Mistral 7B
   - Resources: 6-8GB RAM, 2-4 CPU cores (plenty available on OCI)
   - Service: `ollama-service:11434` (internal)
   - Model: Pre-loaded Mistral 7B (~4GB)
   - **Cost**: $0/month (free forever)

### Network Flow

#### Minikube (Local):
1. **Domain** (`news.deestore.in`) → Cloudflare DNS
2. **Cloudflare Tunnel** → Routes to `localhost:8501`
3. **Port Forward** → Routes to Kubernetes pod
4. **Pod** → Streamlit on port 8501

#### OCI (Cloud):
1. **Domain** (`news.deestore.in`) → Cloudflare DNS (or direct OCI LoadBalancer IP)
2. **OCI LoadBalancer** → Routes to Kubernetes Service
3. **Service** → Routes to Pod
4. **Pod** → Streamlit on port 8501

---

## 🔐 Security & Configuration

### Environment Variables
- `OPENAI_API_KEY` - Stored in Kubernetes Secret (for fallback)
- `AI_PROVIDER` - `'openai'` or `'ollama'` (default: 'openai')
- `OLLAMA_BASE_URL` - Ollama API URL (default: `http://localhost:11434` or `http://ollama-service:11434` in K8s)
- `OLLAMA_DEFAULT_MODEL` - Model to use (default: `'mistral:7b'`)
- Loaded from `.env` file (local) or ConfigMap/Secret (Kubernetes)

### API Key Management
- **Local**: `.env` file (gitignored)
- **Kubernetes**: Secret `newssummariser-secrets`
- **Injected**: Via `envFrom` in deployment

---

## 📊 Data Flow Summary

```
User Input → Streamlit → FastAPI → News Fetcher → Google News RSS
                                                      ↓
User Sees ← Streamlit ← FastAPI ← Summarizer ← AI Provider
                                                    ↓
                                          ┌─────────┴─────────┐
                                          │                   │
                                    OpenAI API          Ollama (Mistral 7B)
                                    (api.openai.com)    (local/K8s)
```

## 🤖 AI Provider Options

### Option 1: OpenAI (Current Default)
- **Cost**: ~$0.01-0.03 per summary
- **Quality**: ⭐⭐⭐⭐⭐ (95%)
- **Speed**: ⭐⭐⭐⭐⭐ (2-3 seconds)
- **Setup**: API key only

### Option 2: Ollama + Mistral 7B (Recommended for Cost Savings)
- **Cost**: $0 (free, self-hosted)
- **Quality**: ⭐⭐⭐⭐ (88-92% of GPT-4o)
- **Speed**: ⭐⭐⭐⭐ (3-5 seconds CPU, 0.5-1s GPU)
- **Setup**: Requires Ollama installation + 6-8GB RAM
- **Best for**: Hindi summarization, cost savings

### Switching Providers:
Set `AI_PROVIDER=ollama` in `.env` or Kubernetes ConfigMap to use Ollama instead of OpenAI.

---

## 🎯 Key Features

1. **Multi-language Support**: Hindi and English
2. **Real-time Translation**: Article titles and summaries translated on-demand
3. **Article Expansion**: Click to see full translated articles
4. **Session Persistence**: Results persist across page interactions
5. **Error Handling**: Graceful fallbacks if articles not found
6. **HTML Cleaning**: Removes HTML tags from RSS feed content
7. **Caching**: Translations cached in session state

---

## 🔧 Technologies Used

- **Frontend**: Streamlit
- **Backend**: FastAPI
- **AI Providers**:
  - OpenAI GPT-4o / GPT-4o-mini (paid, cloud)
  - Ollama + Mistral 7B / Llama 3.1 8B / Qwen 2.5 7B (free, self-hosted)
- **News Source**: Google News RSS
- **Web Scraping**: BeautifulSoup
- **Containerization**: Docker
- **Orchestration**: Kubernetes (minikube for local, k3s for OCI)
- **Cloud Providers**: 
  - Oracle Cloud Infrastructure (OCI) - Free tier (24GB RAM, 4 OCPUs)
  - Minikube (local development)
- **Tunneling**: Cloudflare Tunnel (for minikube)
- **Domain**: GoDaddy + Cloudflare DNS

---

This architecture provides a scalable, containerized solution for news summarization with multi-language support and a user-friendly interface.

