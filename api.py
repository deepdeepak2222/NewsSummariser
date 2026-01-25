"""
FastAPI server for News Summarizer
"""
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

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

app = FastAPI(
    title="News Summarizer API",
    description="API for fetching and summarizing news articles",
    version="1.0.0"
)

# Enable CORS for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Streamlit URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class NewsRequest(BaseModel):
    query: str
    location: Optional[str] = ""  # Any Indian state or location
    max_articles: Optional[int] = 10
    language: Optional[str] = "Hindi"


class NewsResponse(BaseModel):
    summary: str
    articles_found: int
    query: str
    articles: Optional[List[Dict]] = []


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "News Summarizer API is running", "status": "ok"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/summarize", response_model=NewsResponse)
async def summarize_news(request: NewsRequest):
    """
    Fetch and summarize news articles
    
    Args:
        request: NewsRequest with query, location, and max_articles
    
    Returns:
        NewsResponse with summary and metadata
    """
    try:
        # Fetch articles first to check if any were found
        # Build search query: if location provided, combine with query; otherwise use query only
        if request.location and request.location.strip():
            search_query = f"{request.location.strip()} {request.query}".strip()
        else:
            search_query = request.query.strip()
        articles = fetch_news_articles(search_query, max_articles=request.max_articles)
        
        if not articles:
            return NewsResponse(
                summary="क्षमा करें, मुझे कोई समाचार लेख नहीं मिला। कृपया बाद में पुनः प्रयास करें।",
                articles_found=0,
                query=search_query,
                articles=[]
            )
        
        # Get summary - pass max_articles and language to ensure all fetched articles are summarized
        summary = get_news(request.query, request.location, max_articles=request.max_articles, language=request.language)
        
        return NewsResponse(
            summary=summary,
            articles_found=len(articles),
            query=search_query,
            articles=articles
        )
    
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

