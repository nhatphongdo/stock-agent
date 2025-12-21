import subprocess

class GeminiCLIClient:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
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
        Generates content by calling the 'gemini' CLI via subprocess with streaming and JSON parsing.
        """
        import asyncio
        import json

        try:
            # Command to use streaming with JSON output
            # Use positional argument for prompt as --prompt is deprecated
            cmd = ["gemini", "--sandbox", "--output-format", "stream-json", "--model", self.model_name, prompt]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            while True:
                line_bytes = await process.stdout.readline()
                if not line_bytes:
                    break

                line = line_bytes.decode().strip()
                if not line:
                    continue

                # Aggressively skip logs and metadata (lines starting with [)
                # This covers [STARTUP], [WARNING], etc.
                if line.startswith("["):
                    continue

                try:
                    # Attempt to parse as JSON
                    data = json.loads(line)

                    # Filter out technical JSON types (tool use, tool result, etc.)
                    technical_types = ["tool_use", "tool_result", "init", "result", "call"]
                    if data.get("type") in technical_types:
                        continue

                    # Only yield if it's an assistant message
                    if data.get("type") == "message":
                        role = data.get("role")
                        content = data.get("content")
                        if role == "assistant" and content:
                            yield content

                    # Ignore other roles like 'user' or 'system'

                except json.JSONDecodeError:
                    # Strictly suppress raw non-JSON text to hide traces or partial echoes
                    pass

            # Check for errors on stderr if the process fails
            await process.wait()
            if process.returncode != 0:
                stderr = await process.stderr.read()
                error_msg = stderr.decode().strip()
                if error_msg:
                    yield f"\n❌ CLI Error (Exit {process.returncode}): {error_msg}"
                else:
                    yield f"\n❌ CLI Error: Process exited with code {process.returncode}"

        except Exception as e:
            yield f"❌ Unexpected CLI error: {str(e)}"
