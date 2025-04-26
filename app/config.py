from dotenv import load_dotenv
from pathlib import Path
import os

# Load environment variables from .env in project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# OpenAI API key for AI features
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
# OpenAI model to use for API calls
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4.1-nano")