import os
import uvicorn
import logging
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi.responses import HTMLResponse, StreamingResponse

from app.llm.gemini_client import GeminiClient
from app.agents.trading_agent import TradingAgent

# Load environment variables early
load_dotenv()

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO))
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle startup and shutdown events.
    """
    try:
        # Initialize Client and Agent once
        client = GeminiClient()
        app.state.agent = TradingAgent("StockTraderAssistant", client)
        logger.info("🚀 Stock Trading Agent initialized and ready")
    except Exception as e:
        logger.error(f"❌ Failed to initialize agent: {e}", exc_info=True)
        raise e
    yield
    # Cleanup if needed
    logger.info("🛑 Shutting down...")

app = FastAPI(
    title="Stock Trading Agent API",
    description="A modular API for building stock trading agents using Gemini Pro",
    version="1.0.0",
    lifespan=lifespan
)

class AnalyzeRequest(BaseModel):
    task: Optional[str] = "Phân tích thị trường tổng quan"
    date: Optional[str] = None
    stocks: Optional[List[str]] = []

class AnalyzeResponse(BaseModel):
    agent_response: str

@app.get("/")
async def root():
    return {"message": "Welcome to the Stock Trading Agent API", "status": "online"}

@app.get("/trade-agent", response_class=HTMLResponse)
async def get_ui():
    """
    Serve the web UI for the stock trading agent.
    """
    try:
        html_path = os.path.join(os.path.dirname(__file__), "index.html")
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading index.html: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading index.html: {str(e)}")

@app.post("/stock-analyze")
async def analyze_stock(request: Request, body: AnalyzeRequest):
    """
    Endpoint to trigger the trading agent's analysis with streaming output.
    """
    try:
        # Access the agent from app state via request object
        agent = request.app.state.agent
        logger.debug(f"Received streaming analysis request: {body.task}")

        async def event_generator():
            try:
                async for chunk in agent.run(
                    task=body.task,
                    date=body.date,
                    stocks=body.stocks,
                    blacklist=["Bất động sản"],
                ):
                    if chunk:
                        yield chunk
            except Exception as e:
                logger.error(f"❌ Error in streaming generator: {e}", exc_info=True)
                yield f"❌ Error: {str(e)}"

        return StreamingResponse(event_generator(), media_type="text/plain")

    except Exception as e:
        logger.error(f"❌ Error initiating analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    # Note: Use the string format for uvicorn.run to support reload correctly
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level=LOG_LEVEL.lower()
    )
