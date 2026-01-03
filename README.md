# Stock Trading Agent (Trade Agent)

A professional AI-powered stock analysis system built with FastAPI and Google's Gemini Models. Designed to provide deep insights into the Vietnam stock market with a premium, modern interface.

## 🌟 Features

### 🧠 Core AI & Agents

- **Dual LLM Providers**: Supports both **Google Gen AI SDK** and **Gemini CLI** (via MCP).
- **AI Streaming Content**: Real-time response generation with internal reasoning visibility.
- **Specialized Agents**:
  - **Technical Analysis Agent**: automated chart pattern recognition and trend analysis.
  - **News Agent**: real-time market news aggregation (optional integration).
- **Model Context Protocol (MCP)**: Custom MCP server to expose Python financial tools to the Gemini CLI.

### 📊 Advanced Technical Analysis

- **Comprehensive Pattern Recognition**:
  - **Price Patterns**: Automatically detects and visualizes complex geometric patterns:
    - Head & Shoulders (Normal & Inverse)
    - Double Top / Double Bottom
    - Triangles (Ascending, Descending, Symmetrical)
    - Wedges (Rising, Falling)
    - Rectangles
  - **Candlestick Analysis**: Identifies 50+ candlestick patterns (Hammer, Doji, Engulfing, Morning Star, etc.) with bullish/bearish classification.
- **Smart Trend Analysis**:
  - **Trendlines**: Dynamic best-fit trendline calculation and visualization.
  - **Support & Resistance**: Automated identification and visualization of key price levels and demand/supply zones.
- **Technical Indicators**: Real-time calculation of MA, EMA, BB, RSI, MACD with interactive tooltips.

### 💻 Modern Web Interface

- **Premium UI/UX**: Responsive design with glassmorphism, tailored dark mode, and smooth animations.
- **Interactive Charting 2.0**:
  - Powered by Lightweight Charts.
  - Toggleable geometric pattern overlays.
  - Interactive candlestick pattern markers with tooltips.
  - Customizable timeframes and chart types.
- **Vietnam Market Support**: Integrated with `vnstock` for real-time data on all VN tickers.

## 🚀 API & Web Interface

- **Web UI**: Access the interactive dashboard at `http://localhost:8000/trade-agent`
- **Streaming endpoint**: `POST /stock-analyze`
  - Body: `{"task": "nội dung yêu cầu", "stocks": ["SSI", "VND"]}`
- **Pattern Analysis Endpoints**:
  - `/chart-patterns`: Geometric patterns (Triangles, Wedges, etc.)
  - `/candle-patterns`: Candlestick formations
  - `/support-resistance`: S/R lines and zones

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
   - `GEMINI_MODEL_NAME`: e.g., `gemini-2.0-flash`.

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
- `app/index.html` & `app/static/`: Modern dashboard with vanilla JS (Chart.js logic) and Tailwind CSS.
- `app/agents/`:
  - `technical_analysis_agent.py`: Pattern detection orchestration.
  - `trading_agent.py`: Main trading logic agent.
- `app/tools/`:
  - `price_patterns.py`: Geometric pattern detection algorithms.
  - `technical_indicators.py`: TA indicators and Candlestick patterns.
  - `vietcap_tools.py`: Data fetching tools.
- `app/llm/`:
  - `gemini_client.py`: Multi-provider client (SDK/CLI).
  - `mcp_server.py`: Standard MCP server for CLI tool-calling.

## 📈 Roadmap

- [x] Modern Web Interface with Dark Mode
- [x] Real-time Streaming Responses (SDK/CLI)
- [x] Advanced Technical Analysis Charts
- [x] Geometric Price Pattern Detection (Triangles, Wedges, H&S)
- [x] Candlestick Pattern Recognition
- [x] Automated S/R and Trendlines
- [x] MCP Integration for local tool-calling
