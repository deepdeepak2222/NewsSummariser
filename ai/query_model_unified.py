"""
Unified AI model query interface
Supports both OpenAI and Ollama (open-source) models
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Literal

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Determine which provider to use
AI_PROVIDER = os.getenv('AI_PROVIDER', 'openai').lower()  # 'openai' or 'ollama'

# Import providers
try:
    from ai.query_model import query_model as query_openai
except ImportError:
    query_openai = None

try:
    from ai.query_model_ollama import query_ollama
except ImportError:
    query_ollama = None


def query_model(
    user_prompt: str,
    system_prompt: str,
    model: str = None,
    provider: Literal['openai', 'ollama', 'auto'] = 'auto'
) -> str:
    """
    Unified function to query AI models (OpenAI or Ollama)
    
    Args:
        user_prompt: User's query/prompt
        system_prompt: System prompt/instructions
        model: Model name (provider-specific)
            - OpenAI: 'gpt-4o', 'gpt-4o-mini', etc.
            - Ollama: 'llama3.1:8b', 'mistral', 'qwen2.5:7b', etc.
        provider: Which provider to use ('openai', 'ollama', or 'auto')
            - 'auto': Uses AI_PROVIDER env var or defaults to OpenAI
    
    Returns:
        Response content from the model
    """
    # Determine provider
    if provider == 'auto':
        provider = AI_PROVIDER
    
    # Default models if not specified
    if model is None:
        if provider == 'ollama':
            model = os.getenv('OLLAMA_DEFAULT_MODEL', 'llama3.1:8b')
        else:
            from ai.constants import MODEL_GPT_4O_MINI
            model = MODEL_GPT_4O_MINI
    
    # Route to appropriate provider
    if provider == 'ollama':
        if query_ollama is None:
            raise Exception(
                "Ollama not available. Install: pip install requests\n"
                "Make sure Ollama is running: ollama serve"
            )
        try:
            return query_ollama(user_prompt, system_prompt, model=model)
        except Exception as e:
            # Fallback to OpenAI if Ollama fails and OpenAI is available
            openai_key = os.getenv('OPENAI_API_KEY')
            if query_openai is not None and openai_key:
                print(f"⚠️  Ollama failed: {e}. Falling back to OpenAI...")
                return query_openai(user_prompt, system_prompt, model=model)
            raise
    
    elif provider == 'openai':
        if query_openai is None:
            raise Exception("OpenAI client not available. Check your installation.")
        return query_openai(user_prompt, system_prompt, model=model)
    
    else:
        raise ValueError(f"Unknown provider: {provider}. Use 'openai' or 'ollama'")


def get_available_providers() -> list:
    """Get list of available AI providers"""
    providers = []
    
    if query_openai is not None:
        providers.append('openai')
    
    if query_ollama is not None:
        providers.append('ollama')
    
    return providers

