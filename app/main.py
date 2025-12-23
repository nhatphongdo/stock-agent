import os
import uvicorn
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.llm.gemini_client import GeminiClient
from app.agents.trading_agent import TradingAgent
from app.agents.news_agent import NewsAgent
from app.db.database import get_all_users, update_user_settings, get_user_stocks, add_user_stock, remove_user_stock, update_user_stock
from app.tools.stock_tools import get_all_symbols, get_stock_ohlcv

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
        app.state.news_agent = NewsAgent("StockNewsAssistant", client)
        logger.info("🚀 Stock Trading Agent and News Agent initialized and ready")
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

class AnalyzeRequest(BaseModel):
    task: Optional[str] = "Phân tích thị trường tổng quan"
    date: Optional[str] = None
    stocks: Optional[List[str]] = None
    blacklist: Optional[List[str]] = None
    dividend_rate: Optional[float] = None

class AnalyzeResponse(BaseModel):
    agent_response: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    black_list: List[str]
    dividend_rate: float

class SettingsUpdateRequest(BaseModel):
    black_list: List[str]
    dividend_rate: float

class StockResponse(BaseModel):
    id: int
    user_id: int
    stock_name: str
    avg_price: Optional[float]

class StockCreateRequest(BaseModel):
    stock_name: str
    avg_price: float

@app.get("/")
async def root():
    return {"message": "Welcome to the Stock Trading Agent API", "status": "online"}

class NewsRequest(BaseModel):
    symbol: str
    company_name: Optional[str] = ""

from fastapi.responses import StreamingResponse

@app.post("/news-analysis")
async def analyze_news(request: NewsRequest):
    """
    Analyzes news for a given stock symbol using NewsAgent (Streaming).
    """
    if not hasattr(app.state, "news_agent"):
         raise HTTPException(status_code=503, detail="News Agent not initialized")

    # Use StreamingResponse
    return StreamingResponse(
        app.state.news_agent.run(request.symbol, request.company_name),
        media_type="application/x-ndjson"
    )

# Cache for stock symbols (symbol -> company name) with TTL
_symbols_cache: dict = {}
_symbols_cache_timestamp: float = 0
SYMBOLS_CACHE_TTL: int = 3600  # 1 hour in seconds

def is_symbols_cache_valid() -> bool:
    """Check if the symbols cache is still valid based on TTL."""
    import time
    if not _symbols_cache:
        return False
    return (time.time() - _symbols_cache_timestamp) < SYMBOLS_CACHE_TTL

@app.get("/symbols")
async def get_symbols():
    """
    Returns a dictionary mapping stock symbols to company names.
    Results are cached in memory with TTL for performance.
    """
    import time
    global _symbols_cache, _symbols_cache_timestamp

    if not is_symbols_cache_valid():
        logger.info("Fetching stock symbols from vnstock...")
        _symbols_cache = get_all_symbols()
        _symbols_cache_timestamp = time.time()
        logger.info(f"Cached {len(_symbols_cache)} stock symbols (TTL: {SYMBOLS_CACHE_TTL}s)")
    return {"symbols": _symbols_cache}

@app.get("/chart/{symbol}")
async def get_chart_data(symbol: str, start: str, end: str, interval: str = "1D"):
    """
    Returns OHLCV data for a stock symbol to render charts.

    Args:
        symbol: Stock ticker symbol (e.g., 'VNM')
        start: Start date in YYYY-MM-DD format
        end: End date in YYYY-MM-DD format
        interval: Data interval ('1D' for daily, '1H' for hourly)
    """
    result = get_stock_ohlcv(symbol.upper(), start, end, interval)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

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
                    blacklist=body.blacklist if body.blacklist else None,
                    divident_rate=body.dividend_rate,
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

@app.get("/users", response_model=List[UserResponse])
async def get_users_endpoint():
    """
    Fetch all users from the SQLite database.
    """
    try:
        return get_all_users()
    except Exception as e:
        logger.error(f"❌ Error fetching users: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.put("/users/{user_id}/settings", response_model=UserResponse)
async def update_user_settings_endpoint(user_id: int, body: SettingsUpdateRequest):
    """
    Update a user's blacklist and dividend rate.
    """
    try:
        updated_user = update_user_settings(user_id, body.black_list, body.dividend_rate)
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        return updated_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating settings: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/users/{user_id}/stocks", response_model=List[StockResponse])
async def get_stocks_endpoint(user_id: int):
    """Fetch all stocks for a user portfolio."""
    try:
        return get_user_stocks(user_id)
    except Exception as e:
        logger.error(f"❌ Error fetching stocks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/users/{user_id}/stocks", response_model=StockResponse)
async def add_stock_endpoint(user_id: int, body: StockCreateRequest):
    """Add a stock to user portfolio."""
    try:
        stock_id = add_user_stock(user_id, body.stock_name, body.avg_price)
        return StockResponse(
            id=stock_id,
            user_id=user_id,
            stock_name=body.stock_name.upper(),
            avg_price=body.avg_price
        )
    except Exception as e:
        logger.error(f"❌ Error adding stock: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/stocks/{stock_id}")
async def remove_stock_endpoint(stock_id: int):
    """Remove a stock from portfolio."""
    try:
        success = remove_user_stock(stock_id)
        if not success:
            raise HTTPException(status_code=404, detail="Stock not found")
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error removing stock: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/stocks/{stock_id}", response_model=StockResponse)
async def update_stock_endpoint(stock_id: int, body: StockCreateRequest):
    """Update a stock in the portfolio."""
    try:
        success = update_user_stock(stock_id, body.stock_name, body.avg_price)
        if not success:
            raise HTTPException(status_code=404, detail="Stock not found")
        # Since we don't have user_id easily here without another query,
        # but the frontend model expects it, let's just return a generic response
        # or adjust the model. For now, let's keep it consistent.
        # Minimal change: return the update info.
        return StockResponse(
            id=stock_id,
            user_id=0, # Placeholder or could be passed in body
            stock_name=body.stock_name.upper(),
            avg_price=body.avg_price
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating stock: {e}")
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
