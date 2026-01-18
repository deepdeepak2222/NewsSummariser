# Summarise news in Bihar state in hindi language
SUMMARISE_NEWS_IN_BIHAR_STATE_IN_HINDI_LANGUAGE_SYSTEM_PROMPT = """
आप एक समाचार सारांशक हैं। आपको समाचार लेख दिए जाएंगे जो बिहार राज्य से संबंधित हैं। 
कृपया इन लेखों को एक ऐसे तरीके से सारांशित करें जो समझने में आसान और संक्षिप्त हो। 
हमेशा हिंदी भाषा का उपयोग करें। सभी महत्वपूर्ण जानकारी को शामिल करें लेकिन इसे संक्षिप्त रखें।
"""

# Summarise news in English language
SUMMARISE_NEWS_IN_ENGLISH_LANGUAGE_SYSTEM_PROMPT = """
You are a news summarizer. You will be given news articles related to Bihar state.
Please summarize these articles in a way that is easy to understand and concise.
Always use English language. Include all important information but keep it brief.
"""

def get_system_prompt(language: str = "Hindi") -> str:
    """
    Get system prompt based on language preference
    
    Args:
        language: Language preference ("Hindi" or "English")
    
    Returns:
        System prompt in the requested language
    """
    if language.lower() == "english":
        return SUMMARISE_NEWS_IN_ENGLISH_LANGUAGE_SYSTEM_PROMPT
    else:
        return SUMMARISE_NEWS_IN_BIHAR_STATE_IN_HINDI_LANGUAGE_SYSTEM_PROMPT
