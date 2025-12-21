import subprocess

class GeminiCLIClient:
    def __init__(self, model_name: str = "gemini-2.5-pro"):
        """
        Initializes the Gemini client using the 'gemini' CLI tool.
        """
        self.model_name = model_name
        # Check if gemini CLI is available
        try:
            subprocess.run(["gemini", "--version"], capture_output=True, check=True)
            print("✅ Initialized using 'gemini' CLI tool")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  Warning: 'gemini' CLI tool not found in PATH.")

    async def generate_content(self, prompt: str):
        """
        Generates content by calling the 'gemini' CLI via subprocess.
        """
        try:
            # Using 'gemini -p "prompt"'
            process = subprocess.run(
                ["gemini", "-m", self.model_name, "-p", prompt],
                capture_output=True,
                text=True,
                check=True
            )
            return process.stdout.strip()
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() or str(e)
            return f"❌ Error calling gemini CLI: {error_msg}"
        except Exception as e:
            return f"❌ Unexpected error: {str(e)}"
