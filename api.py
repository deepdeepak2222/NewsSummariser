"""
FastAPI server for News Summarizer
"""
import sys
import hashlib
import json
from pathlib import Path
from datetime import timedelta
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional, List, Dict
from fastapi import Depends, HTTPException, status
from cachetools import TTLCache
from sqlalchemy.orm import Session

# Database imports
from database import get_db, init_db
from models import User
from schemas import UserRegister, UserLogin, Token, UserResponse, UserPreferenceResponse
from auth import verify_password, create_access_token, get_current_active_user, get_current_user_optional, ACCESS_TOKEN_EXPIRE_MINUTES
from crud import (
    get_user_by_username_or_email,
    get_user_by_username,
    create_user,
    update_user_last_login,
    get_user_preferences,
    create_user_preferences
)

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

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    try:
        init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️  Database initialization warning: {e}")
        # Don't fail startup if DB not available (for development)

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
    max_articles: Optional[int] = None  # None = unlimited (fetch all in time range), set to limit
    language: Optional[str] = "Hindi"
    when: Optional[str] = "1d"  # Time filter: "1d" (last 24h), "7d" (last week), "all" (all time)


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


# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.post("/api/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user
    
    Args:
        user_data: User registration data (phone, username, password, optional email)
        db: Database session
    
    Returns:
        Created user object
    
    Raises:
        HTTPException: If phone, email, or username already exists
    """
    # Normalize phone number (remove spaces, dashes, etc.)
    from schemas import validate_phone
    try:
        normalized_phone = validate_phone(user_data.phone)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Check if phone already exists
    from crud import get_user_by_phone
    if get_user_by_phone(db, normalized_phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered"
        )
    
    # Check if email already exists (if provided)
    if user_data.email and get_user_by_username_or_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    if get_user_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create user
    from schemas import UserCreate
    user_create = UserCreate(
        phone=normalized_phone,
        email=user_data.email,
        username=user_data.username,
        password=user_data.password,
        full_name=user_data.full_name
    )
    
    user = create_user(db, user_create)
    return user


@app.post("/api/auth/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login user and get access token
    
    Args:
        form_data: OAuth2 form data (username, password)
        db: Database session
    
    Returns:
        JWT access token
    
    Raises:
        HTTPException: If credentials are invalid
    """
    # Get user by username or email
    user = get_user_by_username_or_email(db, form_data.username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},  # JWT sub claim must be a string
        expires_delta=access_token_expires
    )
    
    # Update last login
    update_user_last_login(db, user.id)
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user information
    
    Args:
        current_user: Current authenticated user (from token)
    
    Returns:
        User object
    """
    return current_user


@app.get("/api/auth/preferences", response_model=UserPreferenceResponse)
async def get_user_preferences_endpoint(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user preferences
    
    Args:
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        User preferences
    """
    preferences = get_user_preferences(db, current_user.id)
    if not preferences:
        preferences = create_user_preferences(db, current_user.id)
    return preferences


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


def generate_cache_key(query: str, location: str, max_articles: Optional[int], language: str, when: str = "1d") -> str:
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
        # Location and topic are treated separately for location-first ranking.
        # Keep a combined string for display/compatibility only.
        topic = (request.query or "").strip()
        location = (request.location or "").strip()
        search_query = f"{location} {topic}".strip() if location else topic
        
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
        # Respect time filter strictly; rank by location-first relevance when location is provided.
        articles = fetch_news_articles(topic, location=location, max_articles=request.max_articles, when=request.when)
        
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
        
        # Get summary - pass max_articles (None = all articles), language, and when parameter
        # For summarization, we use all fetched articles (already filtered by time if when is set)
        summary = get_news(topic, location=location, max_articles=None, language=request.language, when=request.when or "1d")
        
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
        topic = (query or "").strip()
        loc = (location or "").strip()
        search_query = f"{loc} {topic}".strip() if loc else topic
        articles = fetch_news_articles(topic, location=loc, max_articles=max_articles)
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

