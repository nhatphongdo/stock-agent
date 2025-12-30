# Stock Trading Agent (Trade Agent)

A professional AI-powered stock analysis system built with FastAPI and Google's Gemini Models. Designed to provide deep insights into the Vietnam stock market with a premium, modern interface.

## 🌟 Features

- **Modern Premium Interface**: Responsive web UI with glassmorphism, dark mode (default), and resizable analysis panels.
- **Dual LLM Providers**: Supports both **Google Gen AI SDK** and **Gemini CLI** (via MCP).
- **AI Streaming Content**: Real-time response generation with internal reasoning visibility.
- **Advanced Technical Charts**: Interactive price and volume charts using Lightweight Charts with real-time technical indicator tooltips (MA, EMA, BB, RSI, MACD).
- **Vietnam Market Support**: Integrated with `vnstock` for real-time data on all VN tickers.
- **Model Context Protocol (MCP)**: Custom MCP server to expose Python tools to the Gemini CLI.

## 🚀 API & Web Interface

- **Web UI**: Access the interactive dashboard at `http://localhost:8000/trade-agent`
- **Streaming endpoint**: `POST /stock-analyze`
  - Body: `{"task": "nội dung yêu cầu", "stocks": ["SSI", "VND"]}`

## 🛠 Setup

1. **Clone the repository**.
2. **Environment Setup**:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   ```

3. **Configure Environment Variables**:
   Set up your `.env` file:

   - `GEMINI_PROVIDER`: `api` (SDK) or `cli` (Gemini CLI).
   - `GEMINI_API_KEY`: Your Google AI API key (required for `api` mode).
   - `GEMINI_MODEL_NAME`: e.g., `gemini-2.5-flash`.

4. **Gemini CLI Setup (Optional for `cli` mode)**:

   ```bash
   npm install -g @google/gemini-cli
   # Register the MCP server
   gemini mcp add stock-agent-tools "python3 /path/to/project/app/llm/mcp_server.py"
   ```

5. **Launch Application**:
   ```bash
   python -m app.main
   ```

## 📂 Project Structure

- `app/main.py`: FastAPI application server and static file hosting.
- `app/index.html`: Modern dashboard with vanilla JS and Tailwind CSS.
- `app/agents/`: Core AI agents (Trading, News) and logic.
- `app/tools/`: Financial data tools (Vietcap, Stock tools).
- `app/llm/`:
  - `gemini_client.py`: Multi-provider client (SDK/CLI).
  - `mcp_server.py`: Standard MCP server for CLI tool-calling.
  - `gemini_sandbox/`: Isolated working directory for the CLI.

## 📈 Roadmap

- [x] Modern Web Interface with Dark Mode
- [x] Real-time Streaming Responses (SDK/CLI)
- [x] Advanced Technical Analysis Charts
- [x] MCP Integration for local tool-calling
