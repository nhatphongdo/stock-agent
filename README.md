# Stock Trading Agent API

A modular FastAPI web framework for building stock trading agents using Google's Gemini Models.

## Features
- **FastAPI Web Interface**: RESTful API endpoints for interacting with the agent.
- **Vietnam Market Support**: Integrated with the modern `vnstock` library for real-time VN stock data.
- **Dual Client Support**: Use either the **Gemini CLI** tool or the official **Google AI Studio SDK** (`google-genai`).
- **Flexible Configuration**: Control model types, model names, and authentication via environment variables.

## API Endpoints
- **POST /stock-analyze**: Nhận yêu cầu phân tích và trả về kết quả qua livestream (StreamingResponse).
  - Body: `{"task": "nội dung yêu cầu"}`

### Ví dụ API
```bash
curl -X POST http://localhost:8000/stock-analyze \
     -H "Content-Type: application/json" \
     -d '{"task": "Phân tích HPG"}'
```

## Setup

1. **Clone the repository** (if not already done).
2. **Setup the environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   ```

3. **Configure Environment Variables**:
   Edit the `.env` file to set your preferences:
   - `GEMINI_CLIENT_TYPE`: Choose `studio` (SDK) or `cli` (sub-process). Default is `studio`.
   - `GEMINI_MODEL_NAME`: Set your preferred model (e.g., `gemini-2.5-pro`, `gemini-2.5-flash`).
   - `GEMINI_API_KEY`: Required if using `studio` client type.

4. **Run the Server**:
   ```bash
   python -m app.main
   ```
   Or using uvicorn directly:
   ```bash
   uvicorn app.main:app --reload
   ```

## API Documentation
Once the server is running, you can access the interactive API docs at:
- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Redoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Directory Structure
- `app/main.py`: FastAPI application setup and routes.
- `app/agents/`: Define your trading agents here (e.g., `trading_agent.py`).
- `app/tools/`: Add new tools for your agents to use (e.g., `stock_tools.py`).
- `app/llm/`: Client implementations for Gemini CLI and Google AI Studio.

## Next Steps
- Implement frontend UI (React/Next.js).
- Add user authentication and session management.
- Implement technical indicators as API tools.
