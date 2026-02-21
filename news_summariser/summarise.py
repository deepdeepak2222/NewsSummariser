# Summarise news for any Indian state/location in Hindi or English
import sys
import importlib.util
from pathlib import Path

# Add project root to Python path (must be done before imports)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai.constants import MODEL_GPT_4O
# Use unified query_model that supports both OpenAI and Ollama
try:
    from ai.query_model_unified import query_model
except ImportError:
    # Fallback to OpenAI-only if unified not available
    from ai.query_model import query_model

# Import constants from the same directory (since we can't use relative imports when running directly)
constants_path = Path(__file__).parent / "constants.py"
spec = importlib.util.spec_from_file_location("news_summariser_constants", constants_path)
constants_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(constants_module)
SUMMARISE_NEWS_IN_BIHAR_STATE_IN_HINDI_LANGUAGE_SYSTEM_PROMPT = constants_module.SUMMARISE_NEWS_IN_BIHAR_STATE_IN_HINDI_LANGUAGE_SYSTEM_PROMPT

# Import news fetcher
news_fetcher_path = Path(__file__).parent / "news_fetcher.py"
news_fetcher_spec = importlib.util.spec_from_file_location("news_fetcher", news_fetcher_path)
news_fetcher_module = importlib.util.module_from_spec(news_fetcher_spec)
news_fetcher_spec.loader.exec_module(news_fetcher_module)

def get_news(user_prompt, location="", max_articles=None, language="Hindi", when="1d"):
    """
    Fetch news articles and summarize them
    
    Args:
        user_prompt: User's query about what news they want
        location: Location to search for news (any Indian state or location, default: empty)
        max_articles: Maximum number of articles to fetch. None = fetch all articles (filtered by time if when is set)
        language: Language preference - "Hindi" or "English" (default: "Hindi")
        when: Time filter - "1d" (last 24h), "7d" (last week), "all" (all time)
    
    Returns:
        Summarized news in the requested language
    """
    # Extract keywords from user prompt - remove common words and create search query
    keywords = user_prompt.replace("Get me", "").replace("the latest news", "").replace("of", "").replace("in", "").strip()
    
    # Topic and location are treated separately for location-first ranking
    topic = (keywords or user_prompt or "").strip()
    loc = (location or "").strip()
    
    # Fetch news articles with time filter
    # If max_articles is None, fetch all articles in the time range
    print(
        f"Fetching news articles (topic='{topic}', location='{loc}', when='{when}', "
        f"max_articles={'unlimited' if max_articles is None else max_articles})..."
    )
    articles = news_fetcher_module.fetch_news_articles(topic, location=loc, max_articles=max_articles, when=when)
    
    # Get system prompt based on language
    get_system_prompt = constants_module.get_system_prompt
    system_prompt = get_system_prompt(language)
    
    if not articles:
        if language.lower() == "english":
            return "Sorry, I couldn't find any news articles. Please try again later."
        else:
            return "क्षमा करें, मुझे कोई समाचार लेख नहीं मिला। कृपया बाद में पुनः प्रयास करें।"
    
    # Format articles for summarization
    articles_text = news_fetcher_module.format_articles_for_summarization(articles)
    
    # Create prompt with articles based on language
    if language.lower() == "english":
        prompt_with_articles = f"""Please read the following {len(articles)} news articles and provide a comprehensive summary in English. Make sure to cover information from ALL {len(articles)} articles:

{articles_text}

Please provide a brief and easy-to-understand summary in English that covers key points from all {len(articles)} articles. Use numbered points (1, 2, 3...) to organize the summary clearly."""
    else:
        prompt_with_articles = f"""निम्नलिखित {len(articles)} समाचार लेखों को पढ़ें और उनका व्यापक सारांश हिंदी में प्रदान करें। सुनिश्चित करें कि सभी {len(articles)} लेखों की जानकारी शामिल हो:

{articles_text}

कृपया सभी {len(articles)} लेखों के मुख्य बिंदुओं को कवर करते हुए हिंदी में एक संक्षिप्त और आसानी से समझने योग्य सारांश प्रदान करें। सारांश को स्पष्ट रूप से व्यवस्थित करने के लिए क्रमांकित बिंदुओं (1, 2, 3...) का उपयोग करें।"""
    
    # Summarize using AI
    summary = query_model(prompt_with_articles, system_prompt, model=MODEL_GPT_4O)
    
    return summary


if __name__ == "__main__":
    print(get_news("Get me the latest news of elections", location="Maharashtra"))
    