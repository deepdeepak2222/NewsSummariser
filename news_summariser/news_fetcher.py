"""
Fetch news articles from Google News RSS feeds
"""
import feedparser
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from typing import List, Dict, Optional
from datetime import datetime, timedelta


def clean_html_text(html_text: str) -> str:
    """
    Clean HTML tags from text and extract plain text
    
    Args:
        html_text: Text containing HTML tags
    
    Returns:
        Cleaned plain text
    """
    if not html_text:
        return ""
    
    # Use BeautifulSoup to parse and extract text
    soup = BeautifulSoup(html_text, 'html.parser')
    # Get text and clean up extra whitespace
    text = soup.get_text(separator=' ', strip=True)
    # Remove extra spaces
    text = ' '.join(text.split())
    return text


def fetch_news_articles(
    topic: str,
    location: str = "",
    max_articles: Optional[int] = None,
    when: Optional[str] = None,
    use_multi_source: bool = True
) -> List[Dict[str, str]]:
    """
    Fetch news articles from RSS feeds (single or multiple sources)
    
    Args:
        topic: Topic query (e.g., "jobs", "elections", "Jehanabad")
        location: Optional location (e.g., "Bihar", "Mumbai")
        max_articles: Maximum number of articles to fetch
        when: Time filter - "1d" (last 24 hours), "7d" (last week), None (all time)
        use_multi_source: If True, fetch from multiple RSS sources; if False, use only Google News
    
    Returns:
        List of dictionaries with 'title', 'link', 'summary', 'published', and 'source' keys
    """
    # Use multi-source fetcher if enabled
    if use_multi_source:
        try:
            # Try absolute import first
            try:
                from news_summariser.multi_rss_fetcher import fetch_news_from_multiple_sources
            except ImportError:
                # Fallback to relative import
                from .multi_rss_fetcher import fetch_news_from_multiple_sources
            
            # Determine language and region from query context
            # For now, default to English/India, but can be enhanced
            language = "en"
            region = "IN"
            return fetch_news_from_multiple_sources(
                topic=topic,
                location=location,
                max_articles=max_articles,
                when=when,
                language=language,
                region=region
            )
        except ImportError as e:
            print(f"⚠️  Multi-RSS fetcher not available (ImportError: {e}), falling back to Google News only")
        except Exception as e:
            print(f"⚠️  Error in multi-RSS fetcher: {type(e).__name__}: {e}, falling back to Google News only")
            import traceback
            traceback.print_exc()
    
    # Fallback to single-source Google News RSS
    # URL encode the base query
    search_query = f"{location.strip()} {topic.strip()}".strip()
    encoded_query = quote_plus(search_query)
    
    # Build RSS URL - Google News RSS doesn't support when: parameter in query
    # Instead, we'll fetch all results and filter/sort by date
    # The RSS feed is already sorted by relevance/date by Google
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
    
    try:
        # Parse RSS feed
        feed = feedparser.parse(rss_url)
        
        # Debug: Log feed info
        print(f"RSS Feed URL: {rss_url}")
        print(f"Feed entries found: {len(feed.entries)}")
        if len(feed.entries) == 0:
            print(f"Feed status: {feed.get('status', 'unknown')}")
            print(f"Feed bozo: {feed.get('bozo', False)}")
            if feed.get('bozo_exception'):
                print(f"Feed error: {feed.bozo_exception}")
        
        articles = []
        entries = feed.entries if max_articles is None else feed.entries[:max_articles]
        for entry in entries:
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
                    pass
            
            article = {
                'title': clean_html_text(entry.get('title', '')),
                'link': entry.get('link', ''),
                'summary': clean_summary,
                'published': published_time.isoformat() if published_time else None,
                'published_formatted': published_time.strftime('%Y-%m-%d %H:%M') if published_time else None,
                'source': 'Google News'  # Add source name for consistency
            }
            articles.append(article)
        
        # Sort by published date (newest first) if dates are available
        articles_with_dates = [a for a in articles if a['published']]
        articles_without_dates = [a for a in articles if not a['published']]
        
        # Sort articles with dates by newest first
        articles_with_dates.sort(key=lambda x: x['published'], reverse=True)
        
        # Combine: articles with dates first (sorted), then articles without dates
        sorted_articles = articles_with_dates + articles_without_dates
        
        # Filter by time range if specified
        if when and when != 'all' and articles_with_dates:
            now = datetime.now()
            if when == '1d':
                cutoff = now - timedelta(days=1)
            elif when == '7d':
                cutoff = now - timedelta(days=7)
            else:
                cutoff = None
            
            if cutoff:
                # Filter articles to only include those within time range
                filtered_articles = []
                for article in sorted_articles:
                    if article['published']:
                        try:
                            pub_date = datetime.fromisoformat(article['published'])
                            if pub_date >= cutoff:
                                filtered_articles.append(article)
                        except:
                            # If date parsing fails, include the article
                            filtered_articles.append(article)
                    else:
                        # Articles without dates - include them but prioritize dated ones
                        pass
                
                # Add articles without dates at the end if we have space
                if max_articles is not None:
                    remaining_slots = max_articles - len(filtered_articles)
                    if remaining_slots > 0:
                        filtered_articles.extend(articles_without_dates[:remaining_slots])
                else:
                    # If max_articles is None, include all articles without dates
                    filtered_articles.extend(articles_without_dates)
                
                sorted_articles = filtered_articles
        
        # Limit to max_articles only if explicitly set
        if max_articles is not None:
            return sorted_articles[:max_articles]
        else:
            return sorted_articles
        
    except Exception as e:
        print(f"Error fetching news: {e}")
        return []


def get_article_content(url: str) -> str:
    """
    Fetch full content of a news article from its URL
    
    Args:
        url: URL of the news article
    
    Returns:
        Full text content of the article
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try to extract article text (common patterns)
        article_text = ""
        
        # Try different common article selectors
        for selector in ['article', '.article-body', '.post-content', 'main', '.content']:
            elements = soup.select(selector)
            if elements:
                article_text = ' '.join([elem.get_text(strip=True) for elem in elements])
                break
        
        # If no specific article tag found, get all paragraphs
        if not article_text:
            paragraphs = soup.find_all('p')
            article_text = ' '.join([p.get_text(strip=True) for p in paragraphs])
        
        return article_text[:5000]  # Limit to 5000 characters
    except Exception as e:
        print(f"Error fetching article content: {e}")
        return ""


def format_articles_for_summarization(articles: List[Dict[str, str]]) -> str:
    """
    Format articles into a single text string for summarization
    
    Args:
        articles: List of article dictionaries
    
    Returns:
        Formatted string with all article content
    """
    formatted_text = ""
    for i, article in enumerate(articles, 1):
        formatted_text += f"\n--- Article {i} ---\n"
        formatted_text += f"Title: {article['title']}\n"
        formatted_text += f"Summary: {article['summary']}\n"
        if article.get('content'):
            formatted_text += f"Content: {article['content']}\n"
        formatted_text += "\n"
    
    return formatted_text

