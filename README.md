# Stock Trading Agent Framework

A modular Python framework for building stock trading agents using Google's Gemini Pro.

## Features
- **Vietnam Market Support**: Integrated with `vnstock3` for real-time VN stock data.
- **Gemini Pro Integration**: Easy-to-use wrapper for asynchronous content generation.
- **Agent Architecture**: Base class for defining custom agent logic.
- **Config Management**: Environment variable handling via `pydantic-settings`.

## Setup

1. **Clone the repository** (if not already done).
2. **Run the setup script**:
   ```bash
   ./setup.sh
   ```
   *This will create a virtual environment, install dependencies, and setup your `.env` file.*
3. **Configure Authentication**:
   - The framework uses the **`gemini`** CLI tool installed on your system.
   - Ensure the `gemini` command is available in your terminal.
   - You can test it with: `gemini -p "Are you working?"`

4. **Activate & Run**:
   ```bash
   source venv/bin/activate
   python -m app.main
   ```

## Vietnam Market
The framework uses the `vnstock3` library. You can use any VN stock ticker (e.g., `VNM`, `HPG`, `SSI`, `VCB`).

## Directory Structure
- `app/agents/`: Define your agents here.
- `app/tools/`: Add new tools for your agents to use.
- `app/llm/`: LLM client configurations.
- `config/`: App settings and configuration.

## Next Steps
- Implement advanced reasoning logic in `TradingAgent.run`.
- Add more tools (e.g., technical indicators, news sentiment).
- Integrate with trading platforms (e.g., Alpaca, Interactive Brokers).
