"""
Multi-RSS Feed Fetcher
Fetches news articles from multiple RSS sources in parallel
"""
import feedparser
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from news_summariser.rss_sources import get_rss_sources_for_query, build_rss_url, RSSSource
    from news_summariser.news_fetcher import clean_html_text
except ImportError:
    from .rss_sources import get_rss_sources_for_query, build_rss_url, RSSSource
    from .news_fetcher import clean_html_text


def filter_articles_by_query(articles: List[Dict[str, str]], query: str) -> List[Dict[str, str]]:
    """
    Filter articles by query keywords (for sources that don't support query in RSS)
    
    Args:
        articles: List of article dictionaries
        query: Search query with keywords
    
    Returns:
        Filtered list of articles matching the query
    """
    if not query:
        return articles
    
    # Extract keywords from query
    query_lower = query.lower()
    keywords = [kw.strip() for kw in query_lower.split() if len(kw.strip()) > 2]
    
    if not keywords:
        return articles
    
    filtered = []
    for article in articles:
        title = article.get('title', '').lower()
        summary = article.get('summary', '').lower()
        
        # Check if any keyword appears in title or summary
        matches = sum(1 for keyword in keywords if keyword in title or keyword in summary)
        
        # Include if at least one keyword matches
        if matches > 0:
            filtered.append(article)
    
    return filtered


def fetch_single_rss_feed(source: RSSSource, query: str, language: str = "en", region: str = "IN") -> List[Dict[str, str]]:
    """
    Fetch articles from a single RSS feed
    
    Args:
        source: RSS source configuration
        query: Search query
        language: Language code
        region: Region code
    
    Returns:
        List of article dictionaries with 'title', 'link', 'summary', 'published', 'source' keys
    """
    try:
        # Build RSS URL
        rss_url = build_rss_url(source, query, language, region)
        
        # Fetch RSS feed
        response = requests.get(rss_url, timeout=source.timeout, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        # Parse RSS feed
        feed = feedparser.parse(response.content)
        
        articles = []
        max_articles = source.max_articles or len(feed.entries)
        
        for entry in feed.entries[:max_articles]:
            # Clean HTML from summary
            raw_summary = entry.get('summary', entry.get('description', ''))
            clean_summary = clean_html_text(raw_summary)
            
            # Extract published date
            published_time = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                try:
                    published_time = datetime(*entry.published_parsed[:6])
                except:
                    pass
            
            # Also try published field
            if not published_time and hasattr(entry, 'published'):
                try:
                    published_time = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %Z')
                except:
                    try:
                        published_time = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %z')
                    except:
                        pass
            
            article = {
                'title': clean_html_text(entry.get('title', '')),
                'link': entry.get('link', ''),
                'summary': clean_summary,
                'published': published_time.isoformat() if published_time else None,
                'published_formatted': published_time.strftime('%Y-%m-%d %H:%M') if published_time else None,
                'source': source.name  # Add source name
            }
            articles.append(article)
        
        # For sources that don't support query parameters, filter by query keywords
        if "google.com" not in source.url_template.lower():
            articles = filter_articles_by_query(articles, query)
        
        print(f"✅ {source.name}: Fetched {len(articles)} articles")
        return articles
        
    except Exception as e:
        print(f"❌ {source.name}: Error fetching RSS feed - {str(e)}")
        return []


def fetch_news_from_multiple_sources(
    query: str,
    max_articles: int = 10,
    when: Optional[str] = None,
    language: str = "en",
    region: str = "IN"
) -> List[Dict[str, str]]:
    """
    Fetch news articles from multiple RSS sources in parallel
    
    Args:
        query: Search query
        max_articles: Maximum number of articles to return
        when: Time filter - "1d" (last 24h), "7d" (last week), None (all time)
        language: Language code
        region: Region code
    
    Returns:
        List of article dictionaries, sorted by date (newest first)
    """
    # Get enabled RSS sources
    sources = get_rss_sources_for_query(query, language, region)
    
    if not sources:
        print("⚠️  No RSS sources enabled")
        return []
    
    print(f"📡 Fetching from {len(sources)} RSS sources: {', '.join([s.name for s in sources])}")
    
    # Fetch from all sources in parallel using ThreadPoolExecutor
    all_articles = []
    
    with ThreadPoolExecutor(max_workers=len(sources)) as executor:
        # Submit all fetch tasks
        future_to_source = {
            executor.submit(fetch_single_rss_feed, source, query, language, region): source
            for source in sources
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_source):
            source = future_to_source[future]
            try:
                articles = future.result()
                all_articles.extend(articles)
            except Exception as e:
                print(f"❌ {source.name}: Exception - {str(e)}")
    
    print(f"📊 Total articles fetched: {len(all_articles)}")
    
    # Deduplicate articles
    deduplicated_articles = deduplicate_articles(all_articles)
    print(f"📊 After deduplication: {len(deduplicated_articles)} articles")
    
    # Filter by time range if specified
    if when and when != 'all':
        filtered_articles = filter_articles_by_date(deduplicated_articles, when)
        print(f"📊 After time filter ({when}): {len(filtered_articles)} articles")
    else:
        filtered_articles = deduplicated_articles
    
    # Sort by published date (newest first)
    sorted_articles = sort_articles_by_date(filtered_articles)
    
    # Limit to max_articles
    return sorted_articles[:max_articles]


def deduplicate_articles(articles: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Remove duplicate articles based on title similarity and URL
    
    Args:
        articles: List of article dictionaries
    
    Returns:
        Deduplicated list of articles
    """
    seen_urls = set()
    seen_titles = set()
    deduplicated = []
    
    for article in articles:
        url = article.get('link', '').lower().strip()
        title = article.get('title', '').lower().strip()
        
        # Skip if URL already seen
        if url and url in seen_urls:
            continue
        
        # Skip if very similar title already seen
        title_normalized = title[:50]  # Use first 50 chars for comparison
        if title_normalized in seen_titles:
            continue
        
        # Add to seen sets
        if url:
            seen_urls.add(url)
        if title_normalized:
            seen_titles.add(title_normalized)
        
        deduplicated.append(article)
    
    return deduplicated


def filter_articles_by_date(articles: List[Dict[str, str]], when: str) -> List[Dict[str, str]]:
    """
    Filter articles by publication date
    
    Args:
        articles: List of article dictionaries
        when: Time filter - "1d" (last 24h), "7d" (last week)
    
    Returns:
        Filtered list of articles
    """
    if when == 'all':
        return articles
    
    now = datetime.now()
    if when == '1d':
        cutoff = now - timedelta(days=1)
    elif when == '7d':
        cutoff = now - timedelta(days=7)
    else:
        return articles
    
    filtered = []
    articles_without_dates = []
    
    for article in articles:
        if article.get('published'):
            try:
                pub_date = datetime.fromisoformat(article['published'])
                if pub_date >= cutoff:
                    filtered.append(article)
            except:
                # If date parsing fails, include the article
                filtered.append(article)
        else:
            # Articles without dates - add them separately
            articles_without_dates.append(article)
    
    # Add articles without dates at the end (they might be recent)
    filtered.extend(articles_without_dates)
    
    return filtered


def sort_articles_by_date(articles: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Sort articles by publication date (newest first)
    
    Args:
        articles: List of article dictionaries
    
    Returns:
        Sorted list of articles
    """
    articles_with_dates = []
    articles_without_dates = []
    
    for article in articles:
        if article.get('published'):
            articles_with_dates.append(article)
        else:
            articles_without_dates.append(article)
    
    # Sort articles with dates by newest first
    articles_with_dates.sort(
        key=lambda x: datetime.fromisoformat(x['published']) if x.get('published') else datetime.min,
        reverse=True
    )
    
    # Combine: articles with dates first (sorted), then articles without dates
    return articles_with_dates + articles_without_dates

