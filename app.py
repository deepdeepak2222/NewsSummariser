"""
Streamlit UI for News Summarizer
"""
import streamlit as st
import requests
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# API endpoint
API_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="News Summarizer",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .summary-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        margin-top: 1rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        font-weight: bold;
        padding: 0.5rem 1rem;
        border-radius: 5px;
    }
    .article-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #fafafa;
    }
    .article-title {
        font-size: 1.1rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">📰 News Summarizer</h1>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    location = st.text_input("Location", value="", placeholder="e.g., Bihar, Maharashtra, Karnataka...", help="Enter any Indian state or location for news search")
    max_articles = st.slider("Max Articles", min_value=1, max_value=10, value=10, help="Maximum number of articles to fetch")
    language = st.selectbox("Language", options=["Hindi", "English"], index=0, help="Select your preferred language for summaries")
    
    st.markdown("---")
    st.markdown("### 📝 Instructions")
    st.markdown("""
    1. Enter your news query in the text area
    2. Adjust location and max articles if needed
    3. Click "Get Summary" button
    4. Wait for the summary to appear
    """)
    
    st.markdown("---")
    st.markdown("### 🔗 API Status")
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        if response.status_code == 200:
            st.success("✅ API Connected")
        else:
            st.error("❌ API Error")
    except:
        st.error("❌ API Not Running")
        st.info("Please start the API server:\n```bash\npython api.py\n```")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🔍 Enter Your News Query")
    query = st.text_area(
        "What news would you like to see?",
        placeholder="e.g., elections, floods, development, sports...",
        height=100,
        help="Enter keywords or a description of the news you want to see"
    )

with col2:
    st.subheader("📊 Quick Stats")
    if language == "English":
        st.info(f"""
        **Current Settings:**
        - Location: {location}
        - Language: {language}
        - Max Articles: {max_articles}
        """)
    else:
        st.info(f"""
        **वर्तमान सेटिंग्स:**
        - स्थान: {location}
        - भाषा: {language}
        - अधिकतम लेख: {max_articles}
        """)

st.markdown("---")

# Submit button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    submit_button = st.button("🚀 Get Summary", use_container_width=True)

# Process request
if submit_button:
    if not query.strip():
        st.warning("⚠️ Please enter a query before clicking 'Get Summary'")
    elif not location.strip():
        st.warning("⚠️ Please enter a location (state or city) before clicking 'Get Summary'")
    else:
        with st.spinner("🔄 Fetching news articles and generating summary..."):
            try:
                # Make API request
                response = requests.post(
                    f"{API_URL}/summarize",
                    json={
                        "query": query,
                        "location": location,
                        "max_articles": max_articles,
                        "language": language
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Store in session state so it persists across reruns
                    st.session_state['last_news_data'] = data
                    st.session_state['last_query'] = query
                    st.session_state['last_location'] = location
                    st.session_state['last_language'] = language
                    st.session_state['last_max_articles'] = max_articles
                    
                    # Display results
                    st.markdown("---")
                    if language == "English":
                        st.subheader("📰 News Summary")
                    else:
                        st.subheader("📰 समाचार सारांश")
                    
                    # Show metadata
                    col1, col2 = st.columns(2)
                    with col1:
                        if language == "English":
                            st.metric("Articles Found", data["articles_found"])
                        else:
                            st.metric("लेख मिले", data["articles_found"])
                    with col2:
                        if language == "English":
                            st.metric("Search Query", data["query"])
                        else:
                            st.metric("खोज क्वेरी", data["query"])
                    
                    # Display summary
                    st.markdown('<div class="summary-box">', unsafe_allow_html=True)
                    st.markdown(data["summary"])
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Store summary text in session state for narration
                    summary_key = f"summary_{data.get('query', 'default')}_{language}"
                    st.session_state[summary_key] = data["summary"]
                    
                    # Narrate button
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        narrate_key = f"narrate_{summary_key}"
                        if language == "English":
                            narrate_button = st.button("🔊 Narrate Summary", key=narrate_key, use_container_width=True)
                        else:
                            narrate_button = st.button("🔊 सारांश सुनें", key=narrate_key, use_container_width=True)
                    
                    # Handle narration
                    narration_audio_key = f"narration_audio_{summary_key}"
                    narration_generated_key = f"narration_generated_{summary_key}"
                    
                    if narrate_button:
                        # Get summary text from session state
                        summary_text = st.session_state.get(summary_key, data.get("summary", ""))
                        
                        if summary_text:
                            with st.spinner("🔊 Generating audio..." if language == "English" else "🔊 ऑडियो तैयार हो रहा है..."):
                                try:
                                    from gtts import gTTS
                                    import io
                                    
                                    # Determine language code for gTTS
                                    lang_code = "hi" if language == "Hindi" else "en"
                                    
                                    # Generate audio
                                    tts = gTTS(text=summary_text, lang=lang_code, slow=False)
                                    
                                    # Save to bytes buffer
                                    audio_buffer = io.BytesIO()
                                    tts.write_to_fp(audio_buffer)
                                    audio_buffer.seek(0)
                                    
                                    # Store in session state with unique key
                                    st.session_state[narration_audio_key] = audio_buffer.read()
                                    st.session_state[narration_generated_key] = True
                                    
                                    st.success("✅ Audio generated successfully!" if language == "English" else "✅ ऑडियो सफलतापूर्वक तैयार!")
                                    
                                except Exception as e:
                                    st.error(f"Error generating audio: {str(e)}" if language == "English" else f"ऑडियो तैयार करने में त्रुटि: {str(e)}")
                        else:
                            st.warning("⚠️ Summary text not available for narration" if language == "English" else "⚠️ सारांश पाठ नारेशन के लिए उपलब्ध नहीं है")
                    
                    # Play audio if available
                    if st.session_state.get(narration_generated_key, False) and narration_audio_key in st.session_state:
                        audio_bytes = st.session_state[narration_audio_key]
                        st.audio(audio_bytes, format='audio/mp3', autoplay=False)
                        
                        if language == "English":
                            st.caption("👆 Click play to listen to the summary")
                        else:
                            st.caption("👆 सारांश सुनने के लिए प्ले पर क्लिक करें")
                    
                    st.markdown("")  # Add some spacing
                    
                    # Display individual articles with expandable details
                    if data.get("articles") and len(data["articles"]) > 0:
                        st.markdown("---")
                        if language == "English":
                            st.subheader("📄 Individual Articles")
                            st.markdown("*Click on any article to see more details*")
                        else:
                            st.subheader("📄 व्यक्तिगत लेख")
                            st.markdown("*अधिक विवरण देखने के लिए किसी भी लेख पर क्लिक करें*")
                        
                        # Store articles in session state to avoid re-fetching
                        if 'articles_data' not in st.session_state:
                            st.session_state.articles_data = {}
                        
                        for idx, article in enumerate(data["articles"], 1):
                            article_key = article.get('link', f'article_{idx}')
                            article_title = article.get('title', 'No Title')
                            
                            # Translate title and summary if language is Hindi
                            translated_title_key = f"{article_key}_title_{language}"
                            translated_summary_key = f"{article_key}_summary_{language}"
                            
                            if translated_title_key not in st.session_state.articles_data:
                                # Translate title and summary
                                try:
                                    from ai.query_model import query_model
                                    from ai.constants import MODEL_GPT_4O
                                    import importlib.util
                                    
                                    constants_path = project_root / "news_summariser" / "constants.py"
                                    constants_spec = importlib.util.spec_from_file_location("constants", constants_path)
                                    constants_module = importlib.util.module_from_spec(constants_spec)
                                    constants_spec.loader.exec_module(constants_module)
                                    translation_prompt = constants_module.get_system_prompt(language)
                                    
                                    # Get and clean summary first (for both languages)
                                    article_summary_raw = article.get('summary', 'N/A')
                                    if '<' in article_summary_raw and '>' in article_summary_raw:
                                        try:
                                            from bs4 import BeautifulSoup
                                            soup = BeautifulSoup(article_summary_raw, 'html.parser')
                                            article_summary_raw = soup.get_text(separator=' ', strip=True)
                                            article_summary_raw = ' '.join(article_summary_raw.split())
                                        except:
                                            pass
                                    
                                    if language.lower() == "hindi":
                                        # Translate title
                                        title_translate_prompt = f"Translate the following news article title to Hindi. Only provide the translation, no explanation:\n\n{article_title}"
                                        translated_title = query_model(title_translate_prompt, translation_prompt, model=MODEL_GPT_4O)
                                        st.session_state.articles_data[translated_title_key] = translated_title.strip()
                                        
                                        # Translate summary
                                        summary_translate_prompt = f"Translate the following news article summary to Hindi. Only provide the translation, no explanation:\n\n{article_summary_raw[:500]}"
                                        translated_summary = query_model(summary_translate_prompt, translation_prompt, model=MODEL_GPT_4O)
                                        st.session_state.articles_data[translated_summary_key] = translated_summary.strip()
                                    else:
                                        # For English, use original
                                        st.session_state.articles_data[translated_title_key] = article_title
                                        st.session_state.articles_data[translated_summary_key] = article_summary_raw
                                except Exception as e:
                                    # Fallback to original if translation fails
                                    st.session_state.articles_data[translated_title_key] = article_title
                                    st.session_state.articles_data[translated_summary_key] = article.get('summary', 'N/A')
                            
                            # Get translated or original title/summary
                            display_title = st.session_state.articles_data.get(translated_title_key, article_title)
                            display_title_short = display_title[:70] + "..." if len(display_title) > 70 else display_title
                            
                            article_summary_display = st.session_state.articles_data.get(translated_summary_key, article.get('summary', 'N/A'))
                            # Clean HTML from summary if present
                            if '<' in article_summary_display and '>' in article_summary_display:
                                try:
                                    from bs4 import BeautifulSoup
                                    soup = BeautifulSoup(article_summary_display, 'html.parser')
                                    article_summary_display = soup.get_text(separator=' ', strip=True)
                                    article_summary_display = ' '.join(article_summary_display.split())
                                except:
                                    pass
                            
                            article_lang = st.session_state.get('last_language', language)
                            if article_lang == "English":
                                expander_label = f"📌 Article {idx}: {display_title_short}"
                            else:
                                expander_label = f"📌 लेख {idx}: {display_title_short}"
                            
                            with st.expander(expander_label, expanded=False):
                                col1, col2 = st.columns([3, 1])
                                
                                with col1:
                                    # Display translated title
                                    if article_lang == "English":
                                        st.markdown(f"**📰 Title:** {display_title}")
                                    else:
                                        st.markdown(f"**📰 शीर्षक:** {display_title}")
                                    st.markdown("---")
                                    if article_lang == "English":
                                        st.markdown(f"**📝 Summary:**")
                                    else:
                                        st.markdown(f"**📝 सारांश:**")
                                    st.info(article_summary_display)
                                
                                with col2:
                                    if article.get('link'):
                                        st.markdown("")
                                        st.markdown("")
                                        # Add button to view full translated article within app
                                        full_article_key = f"{article_key}_full_{article_lang}"
                                        if st.button(f"📖 {'Read Full Article (Translated)' if article_lang == 'English' else 'पूरा लेख पढ़ें (अनुवादित)'}", key=f"full_btn_{idx}", use_container_width=True):
                                            st.session_state[full_article_key] = True
                                            st.rerun()
                                        
                                        # Also show original link
                                        st.markdown(f"[🔗 {'Original Article' if article_lang == 'English' else 'मूल लेख'}]({article.get('link')})", unsafe_allow_html=True)
                                
                                # Show full translated article if button was clicked
                                full_article_key = f"{article_key}_full_{article_lang}"
                                if st.session_state.get(full_article_key, False):
                                    full_translated_key = f"{article_key}_full_translated_{article_lang}"
                                    if full_translated_key not in st.session_state.articles_data:
                                        with st.spinner(f"{'Translating full article' if article_lang == 'English' else 'पूरा लेख अनुवादित किया जा रहा है'}..."):
                                            try:
                                                import importlib.util
                                                news_fetcher_path = project_root / "news_summariser" / "news_fetcher.py"
                                                news_fetcher_spec = importlib.util.spec_from_file_location("news_fetcher", news_fetcher_path)
                                                news_fetcher_module = importlib.util.module_from_spec(news_fetcher_spec)
                                                news_fetcher_spec.loader.exec_module(news_fetcher_module)
                                                
                                                # Get full article content
                                                full_raw_content = news_fetcher_module.get_article_content(article.get('link'))
                                                
                                                if full_raw_content and len(full_raw_content.strip()) > 0:
                                                    from ai.query_model import query_model
                                                    from ai.constants import MODEL_GPT_4O
                                                    
                                                    constants_path = project_root / "news_summariser" / "constants.py"
                                                    constants_spec = importlib.util.spec_from_file_location("constants", constants_path)
                                                    constants_module = importlib.util.module_from_spec(constants_spec)
                                                    constants_spec.loader.exec_module(constants_module)
                                                    system_prompt_full = constants_module.get_system_prompt(article_lang)
                                                    
                                                    # Translate full article content
                                                    if article_lang.lower() == "english":
                                                        full_translate_prompt = f"""Please read the following complete news article and translate/summarize it in English. Provide a comprehensive summary that includes all important details:

{full_raw_content[:8000]}

Provide a clear, detailed summary in English covering all key points of the article."""
                                                    else:
                                                        full_translate_prompt = f"""निम्नलिखित पूर्ण समाचार लेख पढ़ें और इसे हिंदी में अनुवाद/सारांशित करें। सभी महत्वपूर्ण विवरणों को शामिल करते हुए एक व्यापक सारांश प्रदान करें:

{full_raw_content[:8000]}

लेख के सभी मुख्य बिंदुओं को कवर करते हुए हिंदी में एक स्पष्ट, विस्तृत सारांश प्रदान करें।"""
                                                    
                                                    full_translated = query_model(full_translate_prompt, system_prompt_full, model=MODEL_GPT_4O)
                                                    if full_translated and len(full_translated.strip()) > 0:
                                                        st.session_state.articles_data[full_translated_key] = full_translated
                                                    else:
                                                        st.session_state.articles_data[full_translated_key] = None
                                                else:
                                                    st.session_state.articles_data[full_translated_key] = None
                                            except Exception as e:
                                                st.session_state.articles_data[full_translated_key] = None
                                    
                                    # Display full translated article
                                    if st.session_state.articles_data.get(full_translated_key):
                                        st.markdown("---")
                                        st.markdown("### " + ("📰 Full Article (Translated)" if article_lang == "English" else "📰 पूरा लेख (अनुवादित)"))
                                        st.markdown(st.session_state.articles_data[full_translated_key])
                                        st.markdown("---")
                                        if st.button("✖️ " + ("Close" if article_lang == "English" else "बंद करें"), key=f"close_full_{idx}"):
                                            st.session_state[full_article_key] = False
                                            st.rerun()
                                    elif st.session_state.articles_data.get(full_translated_key) is None:
                                        if article_lang.lower() == "english":
                                            st.error("❌ Could not translate the full article. Please try the original link.")
                                        else:
                                            st.error("❌ पूरा लेख अनुवादित नहीं किया जा सका। कृपया मूल लिंक का प्रयास करें।")
                                
                                # Fetch and display more content when expanded
                                if article.get('link'):
                                    article_content_key = f"{article_key}_content_{language}"
                                    if article_content_key not in st.session_state.articles_data:
                                        with st.spinner(f"Loading and translating article details in {language}..."):
                                            try:
                                                # Import news_fetcher to get article content
                                                import importlib.util
                                                news_fetcher_path = project_root / "news_summariser" / "news_fetcher.py"
                                                news_fetcher_spec = importlib.util.spec_from_file_location("news_fetcher", news_fetcher_path)
                                                news_fetcher_module = importlib.util.module_from_spec(news_fetcher_spec)
                                                news_fetcher_spec.loader.exec_module(news_fetcher_module)
                                                
                                                # Get raw article content
                                                raw_content = news_fetcher_module.get_article_content(article.get('link'))
                                                
                                                if raw_content and len(raw_content.strip()) > 0:
                                                    # Translate/summarize the content in user's preferred language
                                                    from ai.query_model import query_model
                                                    from ai.constants import MODEL_GPT_4O
                                                    
                                                    # Get system prompt for translation
                                                    constants_path = project_root / "news_summariser" / "constants.py"
                                                    constants_spec = importlib.util.spec_from_file_location("constants", constants_path)
                                                    constants_module = importlib.util.module_from_spec(constants_spec)
                                                    constants_spec.loader.exec_module(constants_module)
                                                    system_prompt_for_translation = constants_module.get_system_prompt(language)
                                                    
                                                    # Create translation prompt based on language
                                                    if language.lower() == "english":
                                                        user_prompt_for_translation = f"""Please read the following news article content and provide a brief summary in English (limit to 500 words):

{raw_content[:3000]}

Provide a clear, concise summary in English. Include all important details."""
                                                    else:
                                                        user_prompt_for_translation = f"""निम्नलिखित समाचार लेख की सामग्री पढ़ें और हिंदी में एक संक्षिप्त सारांश प्रदान करें (500 शब्दों तक सीमित):

{raw_content[:3000]}

हिंदी में एक स्पष्ट, संक्षिप्त सारांश प्रदान करें। सभी महत्वपूर्ण विवरण शामिल करें।"""
                                                    
                                                    # Translate using AI - user_prompt first, then system_prompt
                                                    try:
                                                        translated_content = query_model(user_prompt_for_translation, system_prompt_for_translation, model=MODEL_GPT_4O)
                                                        if translated_content and len(translated_content.strip()) > 0:
                                                            st.session_state.articles_data[article_content_key] = translated_content
                                                        else:
                                                            st.session_state.articles_data[article_content_key] = None
                                                    except Exception as translation_error:
                                                        # If translation fails, store None
                                                        st.session_state.articles_data[article_content_key] = None
                                                else:
                                                    st.session_state.articles_data[article_content_key] = None
                                            except Exception as e:
                                                # Store error info for debugging (optional)
                                                st.session_state.articles_data[article_content_key] = None
                                    
                                    # Display the translated content if available
                                    if st.session_state.articles_data.get(article_content_key):
                                        st.markdown("---")
                                        if language.lower() == "english":
                                            st.markdown("**📖 More Details:**")
                                        else:
                                            st.markdown("**📖 अधिक विवरण:**")
                                        content = st.session_state.articles_data[article_content_key]
                                        st.markdown(content)
                                        if article.get('link'):
                                            if language.lower() == "english":
                                                st.markdown(f"*[Read full article for complete details]({article.get('link')})*")
                                            else:
                                                st.markdown(f"*[पूर्ण विवरण के लिए पूरा लेख पढ़ें]({article.get('link')})*")
                                    elif st.session_state.articles_data.get(article_content_key) is None:
                                        if language.lower() == "english":
                                            st.info("💡 More details not available. Click the link above to read the full article.")
                                        else:
                                            st.info("💡 अधिक विवरण उपलब्ध नहीं है। पूरा लेख पढ़ने के लिए ऊपर दिए गए लिंक पर क्लिक करें।")
                    
                    # Success message
                    st.success("✅ Summary generated successfully!")
                    
                else:
                    st.error(f"❌ Error: {response.status_code} - {response.text}")
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to API server. Please make sure the API is running.")
                st.info("""
                **To start the API server, run:**
                ```bash
                python api.py
                ```
                Or:
                ```bash
                uvicorn api:app --reload
                ```
                """)
            except requests.exceptions.Timeout:
                st.error("⏱️ Request timed out. The news fetching is taking too long. Please try again.")
            except Exception as e:
                st.error(f"❌ An error occurred: {str(e)}")

# Display summary from session state if available (for when buttons are clicked)
if 'last_news_data' in st.session_state and not submit_button:
    data = st.session_state['last_news_data']
    language = st.session_state.get('last_language', 'Hindi')
    location = st.session_state.get('last_location', '')
    query = st.session_state.get('last_query', '')
    
    # Display results
    st.markdown("---")
    if language == "English":
        st.subheader("📰 News Summary")
    else:
        st.subheader("📰 समाचार सारांश")
    
    # Show metadata
    col1, col2 = st.columns(2)
    with col1:
        if language == "English":
            st.metric("Articles Found", data["articles_found"])
        else:
            st.metric("लेख मिले", data["articles_found"])
    with col2:
        if language == "English":
            st.metric("Search Query", data["query"])
        else:
            st.metric("खोज क्वेरी", data["query"])
    
    # Display summary
    st.markdown('<div class="summary-box">', unsafe_allow_html=True)
    st.markdown(data["summary"])
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Store summary text in session state for narration
    summary_key = f"summary_{data.get('query', 'default')}_{language}"
    st.session_state[summary_key] = data["summary"]
    
    # Narrate button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        narrate_key = f"narrate_{summary_key}"
        if language == "English":
            narrate_button = st.button("🔊 Narrate Summary", key=narrate_key, use_container_width=True)
        else:
            narrate_button = st.button("🔊 सारांश सुनें", key=narrate_key, use_container_width=True)
    
    # Handle narration
    narration_audio_key = f"narration_audio_{summary_key}"
    narration_generated_key = f"narration_generated_{summary_key}"
    
    if narrate_button:
        # Get summary text from session state
        summary_text = st.session_state.get(summary_key, data.get("summary", ""))
        
        if summary_text:
            with st.spinner("🔊 Generating audio..." if language == "English" else "🔊 ऑडियो तैयार हो रहा है..."):
                try:
                    from gtts import gTTS
                    import io
                    
                    # Determine language code for gTTS
                    lang_code = "hi" if language == "Hindi" else "en"
                    
                    # Generate audio
                    tts = gTTS(text=summary_text, lang=lang_code, slow=False)
                    
                    # Save to bytes buffer
                    audio_buffer = io.BytesIO()
                    tts.write_to_fp(audio_buffer)
                    audio_buffer.seek(0)
                    
                                    # Store in session state with unique key
                                    st.session_state[narration_audio_key] = audio_buffer.read()
                                    st.session_state[narration_generated_key] = True
                                    
                                    st.success("✅ Audio generated successfully!" if language == "English" else "✅ ऑडियो सफलतापूर्वक तैयार!")
                                    
                                except Exception as e:
                                    st.error(f"Error generating audio: {str(e)}" if language == "English" else f"ऑडियो तैयार करने में त्रुटि: {str(e)}")
        else:
            st.warning("⚠️ Summary text not available for narration" if language == "English" else "⚠️ सारांश पाठ नारेशन के लिए उपलब्ध नहीं है")
    
    # Play audio if available
    if st.session_state.get(narration_generated_key, False) and narration_audio_key in st.session_state:
        audio_bytes = st.session_state[narration_audio_key]
        st.audio(audio_bytes, format='audio/mp3', autoplay=False)
        
        if language == "English":
            st.caption("👆 Click play to listen to the summary")
        else:
            st.caption("👆 सारांश सुनने के लिए प्ले पर क्लिक करें")
    
    st.markdown("")  # Add some spacing
    
    # Display individual articles if available
    if data.get("articles") and len(data["articles"]) > 0:
        st.markdown("---")
        if language == "English":
            st.subheader("📄 Individual Articles")
            st.markdown("*Click on any article to see more details*")
        else:
            st.subheader("📄 व्यक्तिगत लेख")
            st.markdown("*अधिक विवरण देखने के लिए किसी भी लेख पर क्लिक करें*")
        
        # Display articles (reuse the same article display logic)
        if 'articles_data' not in st.session_state:
            st.session_state.articles_data = {}
        
        for idx, article in enumerate(data["articles"], 1):
            article_key = article.get('link', f'article_{idx}')
            article_title = article.get('title', 'No Title')
            
            # Get translated title/summary if available
            translated_title_key = f"{article_key}_title_{language}"
            translated_summary_key = f"{article_key}_summary_{language}"
            
            display_title = st.session_state.articles_data.get(translated_title_key, article_title)
            display_title_short = display_title[:70] + "..." if len(display_title) > 70 else display_title
            
            if language == "English":
                expander_label = f"📌 Article {idx}: {display_title_short}"
            else:
                expander_label = f"📌 लेख {idx}: {display_title_short}"
            
            with st.expander(expander_label, expanded=False):
                if language == "English":
                    st.markdown(f"**📰 Title:** {display_title}")
                else:
                    st.markdown(f"**📰 शीर्षक:** {display_title}")
                st.markdown("---")
                if article.get('link'):
                    st.markdown(f"🔗 [Read Full Article]({article.get('link')})")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; padding: 1rem;'>"
    "News Summarizer | Powered by OpenAI & Google News"
    "</div>",
    unsafe_allow_html=True
)

