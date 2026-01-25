"""
Fetch news articles from Google News RSS feeds
"""
import feedparser
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from typing import List, Dict


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


def fetch_news_articles(query: str, max_articles: int = 10) -> List[Dict[str, str]]:
    """
    Fetch news articles from Google News RSS feed
    
    Args:
        query: Search query (e.g., "Bihar Jehanabad")
        max_articles: Maximum number of articles to fetch
    
    Returns:
        List of dictionaries with 'title', 'link', and 'summary' keys
    """
    # URL encode the query
    encoded_query = quote_plus(query)
    # Google News RSS feed URL
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
    
    try:
        # Parse RSS feed
        feed = feedparser.parse(rss_url)
        
        articles = []
        for entry in feed.entries[:max_articles]:
            # Clean HTML from summary
            raw_summary = entry.get('summary', entry.get('description', ''))
            clean_summary = clean_html_text(raw_summary)
            
            article = {
                'title': clean_html_text(entry.get('title', '')),  # Also clean title
                'link': entry.get('link', ''),
                'summary': clean_summary
            }
            articles.append(article)
        
        return articles
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

