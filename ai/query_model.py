# Take user prompt, and query the OPEN_API_FRONTIER model. User MODEL_GPT_4O_MINI as default model. User prompt is mandatory.       

import os
from pathlib import Path
from dotenv import load_dotenv
import openai
from ai.constants import MODEL_GPT_4O_MINI

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Set OpenAI API key from environment
openai.api_key = os.getenv('OPENAI_API_KEY')

def query_model(user_prompt, system_prompt, model=MODEL_GPT_4O_MINI):
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {
                "role": "user", "content": user_prompt
            }, {
                "role": "system", "content": system_prompt
            }
        ]
    )
    return response.choices[0].message.content

