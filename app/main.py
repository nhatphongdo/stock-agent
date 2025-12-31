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
from app.agents.technical_analysis_agent import TechnicalAnalysisAgent
from app.db.database import (
    get_all_users,
    update_user_settings,
    get_user_stocks,
    add_user_stock,
    remove_user_stock,
    update_user_stock,
)
from app.tools.vietcap_tools import (
    get_all_symbols,
    get_stock_ohlcv,
    get_latest_ohlcv,
    get_latest_price_batch,
)

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
        app.state.technical_agent = TechnicalAnalysisAgent(
            "TechnicalAnalysisAssistant", client
        )
        logger.info(
            "🚀 Stock Trading Agent, News Agent, and Technical Analysis Agent initialized and ready"
        )
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
    lifespan=lifespan,
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
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")),
    name="static",
)


class AnalyzeRequest(BaseModel):
    task: Optional[str] = "Phân tích thị trường tổng quan"
    date: Optional[str] = None
    stocks: Optional[List[str]] = None
    blacklist: Optional[List[str]] = None
    whitelist: Optional[List[str]] = None
    return_rate: Optional[float] = None
    dividend_rate: Optional[float] = None
    profit_rate: Optional[float] = None


class AnalyzeResponse(BaseModel):
    agent_response: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    black_list: List[str]
    white_list: List[str]
    return_rate: float
    dividend_rate: float
    profit_rate: float


class SettingsUpdateRequest(BaseModel):
    black_list: List[str]
    white_list: Optional[List[str]] = None
    return_rate: float
    dividend_rate: Optional[float] = None
    profit_rate: Optional[float] = None


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
        media_type="application/x-ndjson",
    )


class TechnicalAnalysisRequest(BaseModel):
    symbol: str
    company_name: Optional[str] = ""
    timeframe: Optional[str] = "ONE_DAY"
    count_back: Optional[int] = 100


@app.post("/technical-analysis")
async def analyze_technical(request: TechnicalAnalysisRequest):
    """
    Analyzes technical indicators for a given stock symbol (Streaming).
    """
    if not hasattr(app.state, "technical_agent"):
        raise HTTPException(
            status_code=503, detail="Technical Analysis Agent not initialized"
        )

    return StreamingResponse(
        app.state.technical_agent.run(
            request.symbol,
            request.company_name,
        ),
        media_type="application/x-ndjson",
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
        logger.info(
            f"Cached {len(_symbols_cache)} stock symbols (TTL: {SYMBOLS_CACHE_TTL}s)"
        )
    return {"symbols": _symbols_cache}


@app.get("/chart/{symbol}")
async def get_chart_data(symbol: str, start: str, end: str, interval: str = "1D"):
    """
    Returns OHLCV data for a stock symbol to render charts.

    Args:
        symbol: Stock ticker symbol (e.g., 'VNM')
        start: Start date in YYYY-MM-DD format
        end: End date in YYYY-MM-DD format
        interval: Data interval ('1D' for daily, '1H' for hourly. Valid: 5m, 15m, 30m, 1H, 1D, 1W, 1M)
    """
    result = get_stock_ohlcv(symbol.upper(), start, end, interval)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/price/{symbol}")
async def get_latest_price(symbol: str):
    """
    Returns the latest price data for a stock symbol.
    """
    result = get_latest_ohlcv(symbol.upper())
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/prices")
async def get_batch_prices(symbols: str):
    """
    Returns the latest price data for multiple stock symbols.
    Args:
        symbols: Comma-separated list of stock ticker symbols (e.g., 'VNM,SSI,HPG')
    """
    if not symbols:
        return {}
    ticker_list = [s.strip().upper() for s in symbols.split(",")]
    result = get_latest_price_batch(ticker_list)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/trade-agent", response_class=HTMLResponse)
async def get_ui():
    """
    Serve the web UI for the stock trading agent with server-side component injection.
    """
    try:
        app_dir = os.path.dirname(__file__)
        html_path = os.path.join(app_dir, "index.html")
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Simple component injection system
        # Looks for <!-- COMPONENT: component_name -->
        import re

        def inject_component(match):
            component_name = match.group(1).strip()
            component_path = os.path.join(
                app_dir, "components", f"{component_name}.html"
            )
            try:
                with open(component_path, "r", encoding="utf-8") as cf:
                    return cf.read()
            except Exception as e:
                logger.error(f"Error reading component {component_name}: {e}")
                return f"<!-- ERROR LOADING COMPONENT: {component_name} -->"

        # Replace all component markers
        html_content = re.sub(
            r"<!--\s*COMPONENT:\s*([\w-]+)\s*-->", inject_component, html_content
        )

        return html_content
    except Exception as e:
        logger.error(f"Error reading index.html: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error reading index.html: {str(e)}"
        )


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
                    whitelist=body.whitelist if body.whitelist else None,
                    return_rate=body.return_rate,
                    dividend_rate=body.dividend_rate,
                    profit_rate=body.profit_rate,
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
    Update a user's blacklist, whitelist, and return rate.
    """
    try:
        # Validate and filter whitelist if provided
        valid_whitelist = None
        if body.white_list is not None:
            valid_symbols = get_all_symbols()
            valid_whitelist = [
                t.upper() for t in body.white_list if t.upper() in valid_symbols
            ][:30]

        updated_user = update_user_settings(
            user_id,
            body.black_list,
            body.return_rate,
            valid_whitelist,
            body.dividend_rate,
            body.profit_rate,
        )
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
            avg_price=body.avg_price,
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
            user_id=0,  # Placeholder or could be passed in body
            stock_name=body.stock_name.upper(),
            avg_price=body.avg_price,
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
        log_level=LOG_LEVEL.lower(),
    )
