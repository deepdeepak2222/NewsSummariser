# Take user prompt, and query the OPEN_API_FRONTIER model. User MODEL_GPT_4O_MINI as default model. User prompt is mandatory.       

import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from ai.constants import MODEL_GPT_4O_MINI

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def query_model(user_prompt, system_prompt, model=MODEL_GPT_4O_MINI):
    """
    Query OpenAI model with user and system prompts
    
    Args:
        user_prompt: User's query/prompt
        system_prompt: System prompt/instructions
        model: Model to use (default: MODEL_GPT_4O_MINI)
    
    Returns:
        Response content from the model
    """
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system", "content": system_prompt
            },
            {
                "role": "user", "content": user_prompt
            }
        ]
    )
    return response.choices[0].message.content

