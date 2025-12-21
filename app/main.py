import asyncio
import os
from dotenv import load_dotenv
from app.llm.gemini_client import GeminiClient
from app.agents.trading_agent import TradingAgent

async def main():
    client = GeminiClient()
    agent = TradingAgent("StockTraderAssistant", client)

    task = "Không có"
    print(f"User Task: {task}")
    print("-" * 30)

    response = await agent.run(task)
    print("Agent Response:")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
