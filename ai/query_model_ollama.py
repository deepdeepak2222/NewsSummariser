"""
Query open-source models via Ollama API
Supports: Llama 3, Mistral, Qwen, Phi-3, Gemma, and more
"""
import os
import requests
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Ollama API endpoint (default: localhost:11434)
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')

def query_ollama(
    user_prompt: str,
    system_prompt: str,
    model: str = "llama3.1:8b",
    base_url: Optional[str] = None
) -> str:
    """
    Query Ollama model with user and system prompts
    
    Args:
        user_prompt: User's query/prompt
        system_prompt: System prompt/instructions
        model: Model to use (default: llama3.1:8b)
        base_url: Ollama API base URL (default: from env or localhost:11434)
    
    Returns:
        Response content from the model
    
    Raises:
        Exception: If Ollama API request fails
    """
    if base_url is None:
        base_url = OLLAMA_BASE_URL
    
    # Combine system and user prompts (Ollama doesn't have separate system/user roles in all models)
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    
    try:
        response = requests.post(
            f"{base_url}/api/generate",
            json={
                "model": model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                }
            },
            timeout=300  # 5 minutes timeout for large summaries
        )
        response.raise_for_status()
        
        result = response.json()
        return result.get('response', '').strip()
    
    except requests.exceptions.ConnectionError:
        raise Exception(
            f"Could not connect to Ollama at {base_url}. "
            "Make sure Ollama is running: 'ollama serve'"
        )
    except requests.exceptions.Timeout:
        raise Exception("Ollama request timed out. Try a smaller model or reduce max_articles.")
    except Exception as e:
        raise Exception(f"Ollama API error: {str(e)}")


def list_available_models(base_url: Optional[str] = None) -> list:
    """
    List available Ollama models
    
    Args:
        base_url: Ollama API base URL
    
    Returns:
        List of available model names
    """
    if base_url is None:
        base_url = OLLAMA_BASE_URL
    
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=10)
        response.raise_for_status()
        models = response.json().get('models', [])
        return [model['name'] for model in models]
    except Exception as e:
        print(f"Error listing models: {e}")
        return []

