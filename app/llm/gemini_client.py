import os
import json
import subprocess
import asyncio
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GeminiClient:
    def __init__(self, model_name: str = None):
        """
        Initializes the Gemini client.
        Supports 'api' (SDK) and 'cli' (subprocess) providers.
        """
        self.provider = os.getenv("GEMINI_PROVIDER", "api").lower()

        if model_name is None:
            model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")
        self.model_name = model_name

        if self.provider == "api":
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                print("⚠️ Warning: GEMINI_API_KEY not found in environment variables.")
            self.client = genai.Client(api_key=api_key)
            print(f"✅ Initialized GeminiClient (SDK Mode, Model: {model_name})")
        else:
            print(f"✅ Initialized GeminiClient (CLI Mode, Model: {model_name})")

    async def generate_content(self, prompt: str):
        """
        Generates content using the chosen provider.
        """
        if self.provider == "api":
            async for chunk in self._generate_api(prompt):
                yield chunk
        else:
            async for chunk in self._generate_cli(prompt):
                yield chunk

    async def generate_with_tools(self, prompt: str, tools: list, on_tool_call: callable = None):
        """
        Generates content with tools.
        SDK mode handles tool loop manually.
        CLI mode delegates everything to the gemini command.
        """
        if self.provider == "api":
            async for chunk in self._generate_with_tools_api(prompt, tools, on_tool_call):
                yield chunk
        else:
            # In CLI mode, the gemini CLI handles tools via registered MCP servers
            async for chunk in self._generate_cli(prompt):
                yield chunk

    async def _generate_api(self, prompt: str):
        try:
            response_stream = self.client.models.generate_content_stream(
                model=self.model_name,
                contents=prompt
            )
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"❌ Error calling Google AI SDK: {str(e)}"

    async def _generate_with_tools_api(self, prompt: str, tools: list, on_tool_call: callable = None):
        try:
            contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
            config = types.GenerateContentConfig(
                tools=tools,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=True  # We handle function calls manually for streaming
                )
            )

            max_iterations = 10  # Prevent infinite loops
            iteration = 0

            while iteration < max_iterations:
                iteration += 1

                # Generate response stream
                response_stream = self.client.models.generate_content_stream(
                    model=self.model_name,
                    contents=contents,
                    config=config
                )

                function_calls = []
                text_accumulated = [] # To keep track of text in current candidate for history

                # Process the stream
                for chunk in response_stream:
                    for part in chunk.candidates[0].content.parts:
                        if part.function_call:
                            function_calls.append(part.function_call)
                        elif part.text:
                            text_accumulated.append(part.text)
                            yield part.text

                # If no function calls, we're done with the agent loop
                if not function_calls:
                    break

                # Add model's response (with function calls) to conversation history
                model_parts = [types.Part.from_text(text=t) for t in text_accumulated]
                model_parts.extend([types.Part(function_call=fc) for fc in function_calls])
                contents.append(types.Content(role="model", parts=model_parts))

                # Execute function calls
                function_responses = []
                for fc in function_calls:
                    tool_name = fc.name
                    tool_args = dict(fc.args) if fc.args else {}

                    # Find and execute the tool
                    result = {"error": f"Tool {tool_name} not found"}
                    for tool in tools:
                        if tool.__name__ == tool_name:
                            try:
                                result = tool(**tool_args)
                            except Exception as e:
                                result = {"error": str(e)}
                            break

                    # Notify about tool call if callback provided
                    if on_tool_call:
                        on_tool_call(tool_name, tool_args, result)

                    # Build function response part
                    function_responses.append(
                        types.Part.from_function_response(
                            name=tool_name,
                            response=result if isinstance(result, dict) else {"result": result}
                        )
                    )

                # Add function responses to conversation
                contents.append(types.Content(role="user", parts=function_responses))

            if iteration >= max_iterations:
                yield "\n\n⚠️ Đã đạt giới hạn số lần gọi công cụ."
        except Exception as e:
            yield f"❌ Error in generate_with_tools: {str(e)}"

    async def _generate_cli(self, prompt: str):
        """
        Executes the gemini CLI via subprocess and streams its output.
        Restricted to gemini_sandbox directory.
        """
        try:
            # gemini CLI command
            # --sandbox: enables sandbox mode (if supported by CLI)
            # --yolo: auto-approve tools
            # --output-format text: standard text output
            cmd = ["gemini", "--sandbox", "--yolo", "--output-format", "text", "--prompt", prompt]
            if self.model_name:
                cmd.extend(["--model", self.model_name])

            # Path to sandbox directory
            sandbox_path = "app/llm/gemini_sandbox"

            # Run in a separate thread to avoid blocking asyncio
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=sandbox_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            async def read_stream(stream):
                while True:
                    # Read in chunks to avoid blocking on newlines or breaking on blank lines
                    chunk = await stream.read(1024)
                    if not chunk:
                        break
                    yield chunk.decode('utf-8')

            async for line in read_stream(process.stdout):
                yield line

            # Wait for completion
            await process.wait()

            if process.returncode != 0:
                stderr = await process.stderr.read()
                err_msg = stderr.decode('utf-8')
                if err_msg:
                    yield f"\n❌ CLI Error: {err_msg}"

        except Exception as e:
            yield f"❌ Exception calling Gemini CLI: {str(e)}"
