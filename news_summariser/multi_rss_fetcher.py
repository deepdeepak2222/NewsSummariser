"""
Multi-RSS Feed Fetcher
Fetches news articles from multiple RSS sources in parallel
"""
import feedparser
import requests
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from news_summariser.rss_sources import get_rss_sources_for_query, build_rss_url, RSSSource
    from news_summariser.news_fetcher import clean_html_text
except ImportError:
    from .rss_sources import get_rss_sources_for_query, build_rss_url, RSSSource
    from .news_fetcher import clean_html_text


_TOKEN_RE = re.compile(r"[A-Za-z0-9\u0900-\u097F]+")


# Minimal bilingual aliases for India-first location matching.
# (We can expand this list over time.)
_ALIASES: Dict[str, List[str]] = {
    "bihar": ["bihar", "बिहार"],
    "jehanabad": ["jehanabad", "जहानाबाद"],
    "jharkhand": ["jharkhand", "झारखंड"],
    "uttar pradesh": ["uttar pradesh", "up", "उत्तर प्रदेश", "यूपी"],
    "gujarat": ["gujarat", "गुजरात"],
    "punjab": ["punjab", "पंजाब"],
    "west bengal": ["west bengal", "bengal", "पश्चिम बंगाल", "बंगाल"],
    "odisha": ["odisha", "orissa", "ओडिशा", "उड़ीसा", "ओड़िशा"],
    "delhi": ["delhi", "दिल्ली"],
    "mumbai": ["mumbai", "मुंबई"],
    "kolkata": ["kolkata", "कोलकाता"],
    "chennai": ["chennai", "चेन्नई"],
    "hyderabad": ["hyderabad", "हैदराबाद"],
    "bengaluru": ["bengaluru", "bangalore", "बेंगलुरु", "बैंगलोर"],
    "patna": ["patna", "पटना"],
}


def _tokenize(text: str) -> List[str]:
    if not text:
        return []
    return [t.strip().lower() for t in _TOKEN_RE.findall(text) if t.strip()]


def _expand_terms(tokens: List[str]) -> List[str]:
    """
    Expand tokens using alias mapping.
    Keeps duplicates out, preserves insertion order.
    """
    seen = set()
    out: List[str] = []
    for t in tokens:
        if t and t not in seen:
            out.append(t)
            seen.add(t)
        # Add alias expansions if present
        for key, aliases in _ALIASES.items():
            if t == key or t in aliases:
                for a in aliases:
                    a_norm = a.lower()
                    if a_norm and a_norm not in seen:
                        out.append(a_norm)
                        seen.add(a_norm)
    return out


def _build_google_query(topic: str, location: Optional[str]) -> str:
    """
    Build a Google News RSS search query that strongly boosts location.
    Example: ("jehanabad" OR "जहानाबाद") (bihar OR बिहार) <topic terms>
    """
    topic_tokens = _expand_terms([t for t in _tokenize(topic) if len(t) > 2])
    loc_tokens = _expand_terms([t for t in _tokenize(location or "") if len(t) > 2])

    def or_group(tokens: List[str]) -> str:
        if not tokens:
            return ""
        uniq = []
        seen = set()
        for t in tokens:
            if t not in seen:
                uniq.append(t)
                seen.add(t)
        if len(uniq) == 1:
            return f"\"{uniq[0]}\""
        return "(" + " OR ".join([f"\"{t}\"" for t in uniq]) + ")"

    # If location is provided, make it mandatory via grouping.
    loc_group = or_group(loc_tokens)
    topic_group = " ".join([f"\"{t}\"" for t in topic_tokens]) if topic_tokens else ""

    if loc_group and topic_group:
        return f"{loc_group} {topic_group}"
    if loc_group:
        return loc_group
    return topic_group or topic.strip()


def _parse_published_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
        # normalize to UTC naive for comparisons
        if dt.tzinfo:
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except Exception:
        return None


def _count_term_hits(text: str, terms: List[str]) -> int:
    if not text or not terms:
        return 0
    text_l = text.lower()
    return sum(1 for t in terms if t and t in text_l)


def _score_article(article: Dict[str, str], location_terms: List[str], topic_terms: List[str]) -> Dict[str, float]:
    """
    Location-first scoring.
    """
    title = article.get("title", "") or ""
    summary = article.get("summary", "") or ""
    link = article.get("link", "") or ""

    # Location match (highest weight)
    loc_title_hits = _count_term_hits(title, location_terms)
    loc_summary_hits = _count_term_hits(summary, location_terms)
    loc_link_hits = _count_term_hits(link, location_terms)
    location_score = (loc_title_hits * 10.0) + (loc_summary_hits * 6.0) + (loc_link_hits * 4.0)

    # Topic match (lower weight than location)
    topic_title_hits = _count_term_hits(title, topic_terms)
    topic_summary_hits = _count_term_hits(summary, topic_terms)
    topic_score = (topic_title_hits * 3.0) + (topic_summary_hits * 1.0)

    # Freshness proxy (used in tie-breakers)
    published_dt = _parse_published_iso(article.get("published"))
    freshness_score = 0.0
    if published_dt:
        hours = max(0.0, (datetime.utcnow() - published_dt).total_seconds() / 3600.0)
        # More recent => higher score (capped)
        freshness_score = max(0.0, 10.0 - min(10.0, hours / 12.0))

    return {
        "location_score": location_score,
        "topic_score": topic_score,
        "freshness_score": freshness_score,
    }


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
        
        print(f"✅ {source.name}: Fetched {len(articles)} articles")
        return articles
        
    except Exception as e:
        print(f"❌ {source.name}: Error fetching RSS feed - {str(e)}")
        return []


def fetch_news_from_multiple_sources(
    topic: str,
    location: Optional[str] = None,
    max_articles: Optional[int] = None,
    when: Optional[str] = None,
    language: str = "en",
    region: str = "IN",
    strict_location: Optional[bool] = None,
) -> List[Dict[str, str]]:
    """
    Fetch news articles from multiple RSS sources in parallel
    
    Args:
        topic: Search topic query
        location: Optional user-provided location (city/state/district)
        max_articles: Maximum number of articles to return. 
                     If None and when filter is set, returns all articles in time range.
                     If None and no when filter, returns all articles.
                     If set, limits to that number.
        when: Time filter - "1d" (last 24h), "7d" (last week), "all" (all time), None (all time)
        language: Language code
        region: Region code
        strict_location: If True and location is provided, only keep articles that match the location.
    
    Returns:
        List of article dictionaries, sorted by relevance (location-first) and date
    """
    if strict_location is None:
        strict_location = bool(location and location.strip())

    google_query = _build_google_query(topic, location)

    # Get enabled RSS sources (location-aware selection)
    sources = get_rss_sources_for_query(topic=topic, location=location, language=language, region=region)
    
    if not sources:
        print("⚠️  No RSS sources enabled")
        return []
    
    print(
        f"📡 Fetching from {len(sources)} RSS sources: {', '.join([s.name for s in sources])} "
        f"(topic='{topic}', location='{location or ''}', strict_location={strict_location}, when='{when}')"
    )
    
    # Fetch from all sources in parallel using ThreadPoolExecutor
    all_articles = []
    
    with ThreadPoolExecutor(max_workers=len(sources)) as executor:
        # Submit all fetch tasks
        future_to_source = {
            executor.submit(fetch_single_rss_feed, source, google_query, language, region): source
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

    # Build terms for relevance scoring
    location_terms = _expand_terms([t for t in _tokenize(location or "") if len(t) > 2])
    topic_terms_raw = _expand_terms([t for t in _tokenize(topic or "") if len(t) > 2])
    # Remove location terms from topic terms (avoid double counting)
    topic_terms = [t for t in topic_terms_raw if t not in set(location_terms)]

    scored: List[Tuple[Dict[str, str], Dict[str, float]]] = []
    for a in filtered_articles:
        scores = _score_article(a, location_terms=location_terms, topic_terms=topic_terms)
        a["relevance"] = scores
        scored.append((a, scores))

    # Strict location filtering (location-first product behavior)
    if strict_location and location_terms:
        scored = [(a, s) for (a, s) in scored if s["location_score"] > 0.0]
        print(f"📊 After strict location filter: {len(scored)} articles")

    # If topic is provided, drop items with zero topic match.
    # This prevents returning generic "Bihar news" for a specific query like "Jehanabad".
    if topic_terms:
        scored = [(a, s) for (a, s) in scored if s["topic_score"] > 0.0]
        print(f"📊 After topic relevance filter: {len(scored)} articles")

    # Sort by: location_score desc, published desc, topic_score desc
    def sort_key(item: Tuple[Dict[str, str], Dict[str, float]]):
        a, s = item
        published_dt = _parse_published_iso(a.get("published"))
        published_ts = published_dt.timestamp() if published_dt else 0.0
        return (s["location_score"], published_ts, s["topic_score"], s["freshness_score"])

    scored.sort(key=sort_key, reverse=True)
    sorted_articles = [a for (a, _) in scored]
    
    # Limit to max_articles only if explicitly set
    # If max_articles is None, return all articles (filtered by time if when is set)
    if max_articles is not None:
        print(f"📊 Limiting to {max_articles} articles")
        return sorted_articles[:max_articles]
    else:
        print(f"📊 Returning all articles (no limit)")
        return sorted_articles


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
    
    # Use UTC-naive timestamps for consistent comparisons
    now = datetime.utcnow()
    if when == '1d':
        cutoff = now - timedelta(days=1)
    elif when == '7d':
        cutoff = now - timedelta(days=7)
    else:
        return articles
    
    filtered = []
    articles_without_dates = []
    articles_with_failed_dates = []
    
    for article in articles:
        if article.get('published'):
            try:
                pub_date = _parse_published_iso(article['published'])
                if pub_date is None:
                    articles_with_failed_dates.append(article)
                elif pub_date >= cutoff:
                    filtered.append(article)
            except Exception as e:
                # If date parsing fails, include the article (might be recent)
                articles_with_failed_dates.append(article)
        else:
            # Articles without dates - include them (might be recent)
            articles_without_dates.append(article)
    
    # Add articles without dates and failed date parsing at the end (they might be recent)
    filtered.extend(articles_without_dates)
    filtered.extend(articles_with_failed_dates)
    
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

