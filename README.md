# Stock Trading Agent (Trade Agent)

A professional AI-powered stock analysis system built with FastAPI and Google's Gemini Models. Designed to provide deep insights into the Vietnam stock market with a premium, modern interface.

## 🌟 Features
- **Modern Premium Interface**: Responsive web UI with glassmorphism, dark mode (default), and resizable analysis panels.
- **AI Streaming Content**: Real-time response generation using Gemini with a smooth typing effect.
- **Vietnam Market Support**: Integrated with `vnstock` for real-time data on all VN tickers.
- **Advanced Markdown Tables**: High-contrast tables with semantic color coding for "BUY", "WATCH", and "CAUTION" signals.
- **Dual Client Support**: Seamlessly switch between **Gemini CLI** and **Google AI Studio SDK**.

## 🚀 API & Web Interface

- **Web UI**: Access the interactive dashboard at `http://localhost:8000/trade-agent`
- **Streaming endpoint**: `POST /stock-analyze`
    - Body: `{"task": "nội dung yêu cầu", "date": "YYYY-MM-DD", "stocks": ["SSI", "VND"]}`

### Example CLI Query
```bash
curl -X POST http://localhost:8000/stock-analyze \
     -H "Content-Type: application/json" \
     -d '{"task": "Phân tích nhóm ngành ngân hàng"}'
```

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
   - `GEMINI_CLIENT_TYPE`: `studio` (SDK) or `cli`.
   - `GEMINI_MODEL_NAME`: e.g., `gemini-2.5-pro`.
   - `GEMINI_API_KEY`: Required for `studio` mode.
   - `LOG_LEVEL`: Set processing verbosity.

4. **Launch Application**:
   ```bash
   python -m app.main
   ```

## 📂 Project Structure
- `app/main.py`: FastAPI application server and static file hosting.
- `app/index.html`: Modern, single-page dashboard with vanilla JS and Tailwind CSS.
- `app/agents/`: Core AI logic and prompt engineering for trading analysis.
- `app/tools/`: Integration with financial data sources (vnstock, etc.).
- `app/llm/`: Flexible LLM client bridge (CLI vs SDK).

## 📈 Roadmap
- [x] Modern Web Interface with Dark Mode
- [x] Real-time Streaming Responses
- [ ] Multi-chart technical analysis integration
- [ ] User portfolio tracking and automated alerts
