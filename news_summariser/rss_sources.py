"""
RSS Feed Sources Configuration
Defines all RSS feed sources and their configurations
"""
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class RSSSource:
    """Configuration for an RSS feed source"""
    name: str
    url_template: str
    enabled: bool = True
    priority: int = 1  # Lower number = higher priority
    timeout: int = 10  # Request timeout in seconds
    max_articles: Optional[int] = None  # None = no limit
    language: Optional[str] = None  # None = use query language
    region: Optional[str] = None  # None = use query region


# RSS Feed Sources Configuration
RSS_SOURCES: List[RSSSource] = [
    # Google News RSS (Current - keep it)
    RSSSource(
        name="Google News",
        url_template="https://news.google.com/rss/search?q={query}&hl={lang}&gl={region}&ceid={region}:{lang}",
        enabled=True,
        priority=1,
        timeout=10,
    ),
    
    # BBC News RSS (World News feed - doesn't support query parameter)
    RSSSource(
        name="BBC News",
        url_template="http://feeds.bbci.co.uk/news/world/rss.xml",
        enabled=True,
        priority=2,
        timeout=10,
        max_articles=20,  # Limit BBC articles since we can't filter by query
    ),
    
    # Reuters RSS (World News feed - doesn't support query parameter)
    # Temporarily disabled due to connectivity issues
    RSSSource(
        name="Reuters",
        url_template="http://feeds.reuters.com/reuters/worldNews",
        enabled=False,  # Disabled until we find a working RSS URL
        priority=2,
        timeout=10,
        max_articles=20,  # Limit Reuters articles since we can't filter by query
    ),
    
    # NDTV RSS (India-specific - Top Stories feed)
    RSSSource(
        name="NDTV",
        url_template="https://feeds.feedburner.com/ndtvnews-top-stories",
        enabled=True,
        priority=3,
        timeout=10,
        max_articles=15,
    ),
]


def get_rss_sources_for_query(query: str, language: str = "en", region: str = "IN") -> List[RSSSource]:
    """
    Get enabled RSS sources configured for a specific query
    
    Args:
        query: Search query
        language: Language code (en, hi, etc.)
        region: Region code (IN, US, etc.)
    
    Returns:
        List of enabled RSS sources
    """
    enabled_sources = [source for source in RSS_SOURCES if source.enabled]
    
    # Sort by priority (lower number = higher priority)
    enabled_sources.sort(key=lambda x: x.priority)
    
    return enabled_sources


def build_rss_url(source: RSSSource, query: str, language: str = "en", region: str = "IN") -> str:
    """
    Build RSS URL from source template and query parameters
    
    Args:
        source: RSS source configuration
        query: Search query
        language: Language code
        region: Region code
    
    Returns:
        Complete RSS URL
    """
    # Handle different URL templates
    if "google.com" in source.url_template:
        # Google News - use query parameter
        from urllib.parse import quote_plus
        encoded_query = quote_plus(query)
        return source.url_template.format(
            query=encoded_query,
            lang=language,
            region=region
        )
    else:
        # For sources that don't support query parameters (BBC, Reuters, NDTV)
        # Return the URL as-is (they're fixed feeds)
        return source.url_template

