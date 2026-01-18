# News Summarizer

A web application that fetches news articles and summarizes them in Hindi using OpenAI's GPT models.

## Features

- 📰 Fetches real-time news from Google News RSS feeds
- 🤖 Summarizes news articles using OpenAI GPT models
- 🌐 FastAPI backend with REST API
- 💻 Streamlit web UI
- 🇮🇳 Hindi language summaries

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   Create a `.env` file in the root directory:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

## Running the Application

### Option 1: Run Both Server and UI (Recommended)

**Terminal 1 - Start FastAPI Server:**
```bash
python api.py
```
Or:
```bash
uvicorn api:app --reload
```

The API will be available at: `http://localhost:8000`
API docs: `http://localhost:8000/docs`

**Terminal 2 - Start Streamlit UI:**
```bash
streamlit run app.py
```

The UI will be available at: `http://localhost:8501`

### Option 2: Run API Only

```bash
python api.py
```

Then access the API at `http://localhost:8000/docs` for interactive API documentation.

## API Endpoints

### POST `/summarize`
Summarize news articles based on a query.

**Request Body:**
```json
{
  "query": "Jehanabad district",
  "location": "Bihar",
  "max_articles": 5
}
```

**Response:**
```json
{
  "summary": "Hindi summary text...",
  "articles_found": 5,
  "query": "Bihar Jehanabad district"
}
```

### GET `/articles`
Fetch news articles without summarization.

**Query Parameters:**
- `query`: Search query
- `location`: Location (default: "Bihar")
- `max_articles`: Max articles to fetch (default: 5)

### GET `/health`
Health check endpoint.

## Project Structure

```
NewsSummariser/
├── api.py                 # FastAPI server
├── app.py                 # Streamlit UI
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (create this)
├── ai/
│   ├── constants.py       # AI model constants
│   └── query_model.py     # OpenAI API integration
└── news_summariser/
    ├── constants.py       # System prompts
    ├── news_fetcher.py    # News fetching logic
    └── summarise.py       # Summarization logic
```

## Usage

1. Start the FastAPI server
2. Start the Streamlit UI
3. Enter your news query in the UI
4. Click "Get Summary" to fetch and summarize news

## Notes

- The application fetches news from Google News RSS feeds
- Summaries are generated in Hindi
- Default location is set to "Bihar" but can be changed
- Make sure your OpenAI API key is set in the `.env` file

