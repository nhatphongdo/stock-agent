import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GeminiClient:
    def __init__(self, model_name: str = None):
        """
        Initializes the Gemini client using the Google Gen AI SDK.
        """
        if model_name is None:
            model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("⚠️  Warning: GEMINI_API_KEY not found in environment variables.")

        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        print(f"✅ Initialized GeminiClient (Model: {model_name})")

    async def generate_content(self, prompt: str):
        """
        Generates content using the google-genai SDK with streaming.
        Simple generation without tools.
        """
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

    async def generate_with_tools(self, prompt: str, tools: list, on_tool_call: callable = None):
        """
        Generates content with function calling support.
        Implements the agentic loop: generate -> call tools -> continue until done.

        Args:
            prompt: The user prompt
            tools: List of Python functions to use as tools
            on_tool_call: Optional callback(tool_name, args, result) for streaming tool progress

        Yields:
            Text chunks from the model's final response
        """
        try:
            # Build conversation history
            contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]

            # Configure tools
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
                # We need to construct a Content object that has both text and function_calls parts
                model_parts = []
                for t in text_accumulated:
                    model_parts.append(types.Part.from_text(text=t))
                for fc in function_calls:
                    model_parts.append(types.Part(function_call=fc))

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
