"""
FastAPI server for News Summarizer
"""
import sys
import hashlib
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
from cachetools import TTLCache

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import cache configuration
try:
    from cache_config import CACHE_TTL_SECONDS, CACHE_ENABLED, MAX_CACHE_SIZE
except ImportError:
    # Fallback defaults if cache_config not found
    CACHE_TTL_SECONDS = 1800  # 30 minutes
    CACHE_ENABLED = True
    MAX_CACHE_SIZE = 100

# Import summarise module dynamically
import importlib.util
summarise_path = project_root / "news_summariser" / "summarise.py"
summarise_spec = importlib.util.spec_from_file_location("summarise", summarise_path)
summarise_module = importlib.util.module_from_spec(summarise_spec)
summarise_spec.loader.exec_module(summarise_module)
get_news = summarise_module.get_news

# Import news_fetcher module dynamically  
news_fetcher_path = project_root / "news_summariser" / "news_fetcher.py"
news_fetcher_spec = importlib.util.spec_from_file_location("news_fetcher", news_fetcher_path)
news_fetcher_module = importlib.util.module_from_spec(news_fetcher_spec)
news_fetcher_spec.loader.exec_module(news_fetcher_module)
fetch_news_articles = news_fetcher_module.fetch_news_articles

# Initialize cache
cache = TTLCache(maxsize=MAX_CACHE_SIZE, ttl=CACHE_TTL_SECONDS) if CACHE_ENABLED else None

app = FastAPI(
    title="News Summarizer API",
    description="API for fetching and summarizing news articles",
    version="1.0.0"
)

# Enable CORS for React frontend
# In production, replace "*" with specific frontend URL(s)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your React frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class NewsRequest(BaseModel):
    query: str
    location: Optional[str] = ""  # Any Indian state or location
    max_articles: Optional[int] = 10
    language: Optional[str] = "Hindi"
    when: Optional[str] = "1d"  # Time filter: "1d" (last 24h), "7d" (last week), None (all time)


class NewsResponse(BaseModel):
    summary: str
    articles_found: int
    query: str
    language: Optional[str] = "Hindi"
    articles: Optional[List[Dict]] = []


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "News Summarizer API is running", "status": "ok"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/cache/stats")
async def cache_stats():
    """
    Get cache statistics
    
    Returns:
        Cache statistics including size, TTL, and enabled status
    """
    if not CACHE_ENABLED or cache is None:
        return {
            "cache_enabled": False,
            "message": "Cache is disabled"
        }
    
    return {
        "cache_enabled": True,
        "cache_size": len(cache),
        "max_size": MAX_CACHE_SIZE,
        "ttl_seconds": CACHE_TTL_SECONDS,
        "ttl_minutes": CACHE_TTL_SECONDS / 60,
        "cache_keys": list(cache.keys())[:10]  # Show first 10 keys for debugging
    }


@app.post("/cache/clear")
async def clear_cache():
    """
    Clear the cache
    
    Returns:
        Success message
    """
    if CACHE_ENABLED and cache is not None:
        cache.clear()
        return {"message": "Cache cleared successfully", "cache_enabled": True}
    return {"message": "Cache is disabled", "cache_enabled": False}


def generate_cache_key(query: str, location: str, max_articles: int, language: str, when: str = "1d") -> str:
    """
    Generate a cache key from request parameters
    
    Args:
        query: Search query
        location: Location
        max_articles: Maximum articles
        language: Language preference
        when: Time filter (1d, 7d, all)
    
    Returns:
        Cache key string
    """
    cache_data = {
        "query": query.strip().lower(),
        "location": location.strip().lower() if location else "",
        "max_articles": max_articles,
        "language": language.strip(),
        "when": when.strip() if when else "1d"
    }
    cache_string = json.dumps(cache_data, sort_keys=True)
    return hashlib.md5(cache_string.encode()).hexdigest()


@app.post("/summarize", response_model=NewsResponse)
async def summarize_news(request: NewsRequest):
    """
    Fetch and summarize news articles (with caching)
    
    Args:
        request: NewsRequest with query, location, and max_articles
    
    Returns:
        NewsResponse with summary and metadata
    """
    try:
        # Build search query: if location provided, combine with query; otherwise use query only
        if request.location and request.location.strip():
            search_query = f"{request.location.strip()} {request.query}".strip()
        else:
            search_query = request.query.strip()
        
        # Generate cache key (include when parameter)
        cache_key = generate_cache_key(
            request.query,
            request.location,
            request.max_articles,
            request.language,
            request.when or "1d"
        )
        
        # Check cache if enabled
        if CACHE_ENABLED and cache is not None:
            if cache_key in cache:
                cached_response = cache[cache_key]
                return NewsResponse(**cached_response)
        
        # Fetch articles first to check if any were found
        # Use when parameter to get latest news (default: last 24 hours)
        articles = fetch_news_articles(search_query, max_articles=request.max_articles, when=request.when)
        
        if not articles:
            # Use language-appropriate error message
            error_message = "Sorry, no news articles found. Please try again later." if request.language == "English" else "क्षमा करें, मुझे कोई समाचार लेख नहीं मिला। कृपया बाद में पुनः प्रयास करें।"
            response = NewsResponse(
                summary=error_message,
                articles_found=0,
                query=search_query,
                language=request.language,
                articles=[]
            )
            # Cache empty response too
            if CACHE_ENABLED and cache is not None:
                cache[cache_key] = response.dict()
            return response
        
        # Get summary - pass max_articles, language, and when parameter
        summary = get_news(request.query, request.location, max_articles=request.max_articles, language=request.language, when=request.when or "1d")
        
        response = NewsResponse(
            summary=summary,
            articles_found=len(articles),
            query=search_query,
            language=request.language,
            articles=articles
        )
        
        # Store in cache if enabled
        if CACHE_ENABLED and cache is not None:
            cache[cache_key] = response.dict()
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@app.get("/articles")
async def get_articles(query: str, location: str = "", max_articles: int = 10):
    """
    Fetch news articles without summarization
    
    Args:
        query: Search query
        location: Location to search (any Indian state or location)
        max_articles: Maximum number of articles to fetch
    
    Returns:
        List of articles
    """
    try:
        # Build search query: if location provided, combine with query; otherwise use query only
        if location and location.strip():
            search_query = f"{location.strip()} {query}".strip()
        else:
            search_query = query.strip()
        articles = fetch_news_articles(search_query, max_articles=max_articles)
        return {
            "articles": articles,
            "count": len(articles),
            "query": search_query
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching articles: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

