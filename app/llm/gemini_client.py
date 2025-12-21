import os
from dotenv import load_dotenv
from app.llm.cli_client import GeminiCLIClient
from app.llm.studio_client import GoogleAIStudioClient

# Load environment variables
load_dotenv()

def get_gemini_client(model_name: str = None):
    """
    Factory function to get the appropriate Gemini client based on configuration.
    """
    client_type = os.getenv("GEMINI_CLIENT_TYPE", "studio").lower()

    if model_name is None:
        model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-pro")

    if client_type == "cli":
        return GeminiCLIClient(model_name=model_name)
    else:
        # Default to studio if not specified or different
        return GoogleAIStudioClient(model_name=model_name)

# For backward compatibility if needed, though get_gemini_client is preferred
class GeminiClient:
    def __new__(cls, model_name: str = None):
        return get_gemini_client(model_name)
