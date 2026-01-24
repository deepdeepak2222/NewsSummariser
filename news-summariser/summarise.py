# Summarise news in Bihar state in hindi language
import sys
from pathlib import Path

from ai.constants import MODEL_GPT_4O

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai.query_model import query_model

# Import constants directly (since directory name has hyphen, can't use normal import)
import importlib.util
constants_path = Path(__file__).parent / "constants.py"
spec = importlib.util.spec_from_file_location("news_summariser_constants", constants_path)
constants_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(constants_module)
SUMMARISE_NEWS_IN_BIHAR_STATE_IN_HINDI_LANGUAGE_SYSTEM_PROMPT = constants_module.SUMMARISE_NEWS_IN_BIHAR_STATE_IN_HINDI_LANGUAGE_SYSTEM_PROMPT

def get_news(user_prompt):
    return query_model(user_prompt, SUMMARISE_NEWS_IN_BIHAR_STATE_IN_HINDI_LANGUAGE_SYSTEM_PROMPT, model=MODEL_GPT_4O)


if __name__ == "__main__":
    print(get_news("Get me the latest news in Bihar state"))
    