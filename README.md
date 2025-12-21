# Stock Trading Agent Framework

A modular Python framework for building stock trading agents using Google's Gemini Models.

## Features
- **Vietnam Market Support**: Integrated with the modern `vnstock` library for real-time VN stock data.
- **Dual Client Support**: Use either the **Gemini CLI** tool or the official **Google AI Studio SDK** (`google-genai`).
- **Flexible Configuration**: Control model types, model names, and authentication via environment variables.
- **Simplified Agent Logic**: Lightweight agent architecture without unnecessary abstractions.

## Setup

1. **Clone the repository** (if not already done).
2. **Run the setup script**:
   ```bash
   ./setup.sh
   ```
   *This will create a virtual environment, install dependencies, and setup your `.env` file.*

3. **Configure Environment Variables**:
   Edit the `.env` file to set your preferences:
   - `GEMINI_CLIENT_TYPE`: Choose `studio` (SDK) or `cli` (sub-process). Default is `studio`.
   - `GEMINI_MODEL_NAME`: Set your preferred model (e.g., `gemini-2.5-pro`, `gemini-2.5-flash`).
   - `GEMINI_API_KEY`: Required if using `studio` client type.

4. **Activate & Run**:
   ```bash
   source venv/bin/activate
   python -m app.main
   ```

## Vietnam Market
The framework uses the `vnstock` library (version 3.x). You can use any VN stock ticker (e.g., `VNM`, `HPG`, `SSI`, `VCB`).

## Directory Structure
- `app/agents/`: Define your trading agents here (e.g., `trading_agent.py`).
- `app/tools/`: Add new tools for your agents to use (e.g., `stock_tools.py`).
- `app/llm/`: Client implementations for Gemini CLI and Google AI Studio.
- `config/`: App settings and configuration.

## Customization
- **TradingAgent**: Update `app/agents/trading_agent.py` to refine the system prompt and agent behavior.
- **Tools**: Add generic tools in `app/tools/` and register them in the agent's prompt to expand capabilities.

## Next Steps
- Implement advanced technical indicators as tools.
- Add real-time news sentiment analysis.
- Integrate with trading platform APIs for automated execution.
