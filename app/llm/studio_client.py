import os
from google import genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GoogleAIStudioClient:
    def __init__(self, model_name: str = "gemini-2.5-pro"):
        """
        Initializes the Gemini client using the modern Google Gen AI SDK.
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("⚠️  Warning: GEMINI_API_KEY not found in environment variables.")

        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        print(f"✅ Initialized GoogleAIStudioClient using modern SDK (Model: {model_name})")

    async def generate_content(self, prompt: str):
        """
        Generates content using the modern google-genai SDK.
        """
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"❌ Error calling Google AI Studio SDK (Modern): {str(e)}"
