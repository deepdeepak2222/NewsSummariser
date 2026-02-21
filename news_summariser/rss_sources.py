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
    
    # Live Hindustan RSS Feeds (India-specific regional news)
    # National feed (always included)
    RSSSource(
        name="Live Hindustan (National)",
        url_template="https://api.livehindustan.com/feeds/rss/national/rssfeed.xml",
        enabled=True,
        priority=4,
        timeout=10,
        max_articles=20,
        language="hi",  # Hindi/English mix
        region="IN",
    ),

    # Major state feeds (used when user's location matches)
    RSSSource(
        name="Live Hindustan (Bihar)",
        url_template="https://api.livehindustan.com/feeds/rss/bihar/rssfeed.xml",
        enabled=True,
        priority=4,
        timeout=10,
        max_articles=30,
        language="hi",
        region="IN",
    ),

    RSSSource(
        name="Live Hindustan (Jharkhand)",
        url_template="https://api.livehindustan.com/feeds/rss/jharkhand/rssfeed.xml",
        enabled=True,
        priority=4,
        timeout=10,
        max_articles=30,
        language="hi",
        region="IN",
    ),

    RSSSource(
        name="Live Hindustan (Uttar Pradesh)",
        url_template="https://api.livehindustan.com/feeds/rss/uttar-pradesh/rssfeed.xml",
        enabled=True,
        priority=4,
        timeout=10,
        max_articles=30,
        language="hi",
        region="IN",
    ),
    
    # Regional feeds (will be dynamically selected based on query location)
    RSSSource(
        name="Live Hindustan (Gujarat)",
        url_template="https://api.livehindustan.com/feeds/rss/gujarat/rssfeed.xml",
        enabled=True,
        priority=4,
        timeout=10,
        max_articles=15,
        language="hi",
        region="IN",
    ),
    
    RSSSource(
        name="Live Hindustan (Punjab)",
        url_template="https://api.livehindustan.com/feeds/rss/punjab/rssfeed.xml",
        enabled=True,
        priority=4,
        timeout=10,
        max_articles=15,
        language="hi",
        region="IN",
    ),
    
    RSSSource(
        name="Live Hindustan (West Bengal)",
        url_template="https://api.livehindustan.com/feeds/rss/west-bengal/rssfeed.xml",
        enabled=True,
        priority=4,
        timeout=10,
        max_articles=15,
        language="hi",
        region="IN",
    ),
    
    RSSSource(
        name="Live Hindustan (Odisha)",
        url_template="https://api.livehindustan.com/feeds/rss/odisha/rssfeed.xml",
        enabled=True,
        priority=4,
        timeout=10,
        max_articles=15,
        language="hi",
        region="IN",
    ),
]


def get_rss_sources_for_query(
    topic: str,
    location: Optional[str] = None,
    language: str = "en",
    region: str = "IN"
) -> List[RSSSource]:
    """
    Get enabled RSS sources configured for a specific query and location.
    Strategy:
    - Always include Google News (query-based).
    - If location is provided, prefer regional/state sources for that location.
    - If location is NOT provided, include broader sources (BBC/NDTV/etc).
    
    Args:
        topic: Search topic query (e.g., "jobs", "election")
        location: Optional location (e.g., "Bihar", "Jehanabad", "Mumbai")
        language: Language code (en, hi, etc.)
        region: Region code (IN, US, etc.)
    
    Returns:
        List of enabled RSS sources based on the selection strategy
    """
    enabled_sources = [source for source in RSS_SOURCES if source.enabled]

    # Always include Google News (query-based)
    google_source = next((s for s in enabled_sources if s.name == "Google News"), None)
    if google_source is None:
        return []

    if location and location.strip():
        location_lower = location.lower()

        # Location keyword -> Live Hindustan regional/state feed name
        location_mapping = {
            # States
            "bihar": "Live Hindustan (Bihar)",
            "jharkhand": "Live Hindustan (Jharkhand)",
            "uttar pradesh": "Live Hindustan (Uttar Pradesh)",
            "up": "Live Hindustan (Uttar Pradesh)",

            # Already present regions
            "gujarat": "Live Hindustan (Gujarat)",
            "punjab": "Live Hindustan (Punjab)",
            "west bengal": "Live Hindustan (West Bengal)",
            "bengal": "Live Hindustan (West Bengal)",
            "odisha": "Live Hindustan (Odisha)",
            "orissa": "Live Hindustan (Odisha)",
        }

        matched_feeds: List[RSSSource] = []
        for keyword, feed_name in location_mapping.items():
            if keyword in location_lower:
                feed = next((s for s in enabled_sources if s.name == feed_name), None)
                if feed:
                    matched_feeds.append(feed)

        # If we have a location, prioritize location-first sources:
        # Google News + matched Live Hindustan regional/state feeds.
        selected = [google_source] + matched_feeds

        # If no regional/state feed matched, keep Live Hindustan National as a shallow fallback.
        if not matched_feeds:
            national = next((s for s in enabled_sources if s.name == "Live Hindustan (National)"), None)
            if national:
                selected.append(national)

        # Remove duplicates while preserving order
        seen = set()
        deduped = []
        for s in selected:
            if s.name not in seen:
                deduped.append(s)
                seen.add(s.name)

        deduped.sort(key=lambda x: x.priority)
        return deduped

    # No location: include broader sources
    selected = enabled_sources
    selected.sort(key=lambda x: x.priority)
    return selected


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

