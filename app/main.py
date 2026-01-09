import os
import uvicorn
import logging
from fastapi import FastAPI, HTTPException, Request, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from bs4 import BeautifulSoup
import re
import time

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
    get_company_list,
)
from app.tools.technical_indicators import (
    get_price_patterns,
    create_ohlcv_dataframe,
    calculate_all_indicators,
)
from app.tools.price_patterns import get_chart_patterns, get_support_resistance
from app.tools.indicator_calculation import (
    calculate_indicators,
    get_available_indicators,
)
from app.tools.analysis_methods import (
    generate_method_evaluations,
    get_available_analysis_methods,
    generate_signal_points,
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
    sector: Optional[str] = None  # ICB sector code for sector analysis
    sector_name: Optional[str] = None


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


@app.get("/candle-patterns/{symbol}")
async def analyze_patterns(
    symbol: str = Path(..., description="Stock ticker symbol (e.g., 'VNM')"),
    start: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end: str = Query(..., description="End date (YYYY-MM-DD)"),
    interval: str = Query(
        "1D", description="Data interval (5m, 15m, 30m, 1H, 1D, 1W, 1M)"
    ),
):
    """
    Detects candlestick patterns for a given stock symbol.

    Args:
        symbol: Stock ticker symbol (e.g., 'VNM')
        start: Start date in YYYY-MM-DD format
        end: End date in YYYY-MM-DD format
        interval: Data interval ('1D' for daily, '1H' for hourly. Valid: 5m, 15m, 30m, 1H, 1D, 1W, 1M)
    """
    result = get_price_patterns(symbol.upper(), start, end, interval)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/chart-patterns/{symbol}")
async def analyze_chart_patterns(
    symbol: str = Path(..., description="Stock ticker symbol (e.g., 'VNM')"),
    start: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end: str = Query(..., description="End date (YYYY-MM-DD)"),
    interval: str = Query(
        "1D", description="Data interval (5m, 15m, 30m, 1H, 1D, 1W, 1M)"
    ),
):
    """
    Detects chart patterns (Double Top, Head & Shoulders, Wedges, Triangles, etc.)
    for a given stock symbol.

    Args:
        symbol: Stock ticker symbol (e.g., 'VNM')
        start: Start date in YYYY-MM-DD format
        end: End date in YYYY-MM-DD format
        interval: Data interval ('1D' for daily, '1H' for hourly. Valid: 5m, 15m, 30m, 1H, 1D, 1W, 1M)
    """
    result = get_chart_patterns(symbol.upper(), start, end, interval)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/support-resistance/{symbol}")
async def analyze_support_resistance(
    symbol: str = Path(..., description="Stock ticker symbol (e.g., 'VNM')"),
    start: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end: str = Query(..., description="End date (YYYY-MM-DD)"),
    interval: str = Query(
        "1D", description="Data interval (5m, 15m, 30m, 1H, 1D, 1W, 1M)"
    ),
):
    """
    Detects support and resistance zones for a given stock symbol.

    Args:
        symbol: Stock ticker symbol (e.g., 'VNM')
        start: Start date in YYYY-MM-DD format
        end: End date in YYYY-MM-DD format
        interval: Data interval ('1D' for daily, '1H' for hourly. Valid: 5m, 15m, 30m, 1H, 1D, 1W, 1M)
    """
    result = get_support_resistance(symbol.upper(), start, end, interval)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


def _get_visualization_type(method_id: str) -> str:
    """Get visualization type for a method."""
    visualization_types = {
        "rsi": "marker",
        "macd": "marker",
        "golden_death_cross": "marker",
        "volume_breakout": "marker",
        "stochastic": "marker",
        "bollinger_bands": "band",
        "bb_squeeze": "zone",
        "support_resistance": "line",
        "moving_average": "line",
        "adx": "marker",
        "volume": "marker",
        "vwap": "line",
        "rsi_divergence": "trendline",
        "macd_rsi_confluence": "marker",
    }
    return visualization_types.get(method_id, "marker")


@app.get("/analysis-methods/{symbol}")
async def get_analysis_methods(
    symbol: str = Path(..., description="Stock ticker symbol (e.g., 'VNM')"),
    start: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end: str = Query(..., description="End date (YYYY-MM-DD)"),
    interval: str = Query(
        "1D", description="Data interval (5m, 15m, 30m, 1H, 1D, 1W, 1M)"
    ),
):
    """
    Get technical analysis method evaluations for a stock.

    Returns a list of analysis methods with their signals, confidence levels,
    and descriptions. Each method includes:
    - id: Unique identifier
    - name: Method name
    - category: Category (Momentum, Trend, Volume, etc.)
    - description: Explanation of the method
    - evaluation: Current market condition
    - signal: Bullish, Bearish, or Neutral
    - confidence: High, Medium, or Low
    - value: Indicator values used

    Args:
        symbol: Stock symbol
        start: Start date in YYYY-MM-DD format
        end: End date in YYYY-MM-DD format
        interval: Data interval (5m, 15m, 30m, 1H, 1D, 1W, 1M)
    """

    # Fetch OHLCV data
    ohlcv_result = get_stock_ohlcv(
        symbol=symbol.upper(),
        start_date=start,
        end_date=end,
        interval=interval,
    )

    if "error" in ohlcv_result or not ohlcv_result.get("data"):
        raise HTTPException(
            status_code=404,
            detail=ohlcv_result.get("error", "No data available"),
        )

    # Create DataFrame and calculate indicators
    df = create_ohlcv_dataframe(ohlcv_result.get("data", []))
    if df.empty:
        raise HTTPException(status_code=404, detail="Empty data")

    # Calculate all indicators
    indicators = calculate_all_indicators(df)

    # Generate method evaluations (without timeframe label for main chart)
    methods = generate_method_evaluations(indicators, ticker=symbol.upper())

    # Add visualization data (signal points) for each method
    for method in methods:
        signals = generate_signal_points(df, method["id"])
        method["visualization"] = {
            "type": _get_visualization_type(method["id"]),
            "signals": signals,
        }

    return {
        "symbol": symbol.upper(),
        "interval": interval,
        "methods": methods,
        "available_methods": get_available_analysis_methods(),
    }


# Cache for stock symbols (symbol -> company name) with TTL
_symbols_cache: dict = {}
_symbols_cache_timestamp: float = 0
SYMBOLS_CACHE_TTL: int = 3600  # 1 hour in seconds


def is_symbols_cache_valid() -> bool:
    """Check if the symbols cache is still valid based on TTL."""
    if not _symbols_cache:
        return False
    return (time.time() - _symbols_cache_timestamp) < SYMBOLS_CACHE_TTL


@app.get("/symbols")
async def get_symbols():
    """
    Returns a dictionary mapping stock symbols to company names.
    Results are cached in memory with TTL for performance.
    """
    global _symbols_cache, _symbols_cache_timestamp

    if not is_symbols_cache_valid():
        logger.info("Fetching stock symbols from vnstock...")
        _symbols_cache = get_all_symbols()
        _symbols_cache_timestamp = time.time()
        logger.info(
            f"Cached {len(_symbols_cache)} stock symbols (TTL: {SYMBOLS_CACHE_TTL}s)"
        )
    return {"symbols": _symbols_cache}


@app.get("/sectors")
async def get_sectors_endpoint():
    """
    Returns list of ICB sectors from company data.
    Extracts icbLv1 and icbLv2 from companies and groups level 2 by level 1.
    """
    try:
        companies = get_company_list()
        if companies and len(companies) > 0 and "error" in companies[0]:
            raise Exception(companies[0]["error"])

        # Build unique sectors and group level 2 by level 1
        sectors_lv1 = {}  # code -> {code, name, children: []}

        for company in companies:
            code_lv1 = company.get("icbCodeLv1")
            name_lv1 = company.get("icbNameLv1")
            code_lv2 = company.get("icbCodeLv2")
            name_lv2 = company.get("icbNameLv2")

            if code_lv1 and name_lv1:
                if code_lv1 not in sectors_lv1:
                    sectors_lv1[code_lv1] = {
                        "icbCode": code_lv1,
                        "icbName": name_lv1,
                        "icbLevel": 1,
                        "children": {},
                    }

                # Add level 2 as child of level 1
                if code_lv2 and name_lv2:
                    if code_lv2 not in sectors_lv1[code_lv1]["children"]:
                        sectors_lv1[code_lv1]["children"][code_lv2] = {
                            "icbCode": code_lv2,
                            "icbName": name_lv2,
                            "icbLevel": 2,
                        }

        return {"sectors": sectors_lv1}
    except Exception as e:
        logger.error(f"❌ Error fetching sectors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chart/{symbol}")
async def get_chart_data(
    symbol: str = Path(..., description="Stock ticker symbol (e.g., 'VNM')"),
    start: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end: str = Query(..., description="End date (YYYY-MM-DD)"),
    interval: str = Query(
        "1D", description="Data interval (5m, 15m, 30m, 1H, 1D, 1W, 1M)"
    ),
):
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


class IndicatorRequest(BaseModel):
    indicators: List[str]  # List of indicator keys to calculate
    seriesIncluded: bool = True  # Whether to return full series or just last value


@app.post("/indicators/{symbol}")
async def get_indicators(
    symbol: str = Path(..., description="Stock ticker symbol (e.g., 'VNM')"),
    start: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end: str = Query(..., description="End date (YYYY-MM-DD)"),
    interval: str = Query(
        "1D", description="Data interval (5m, 15m, 30m, 1H, 1D, 1W, 1M)"
    ),
    request: IndicatorRequest = ...,
):
    """
    Calculate technical indicators for a stock symbol.

    Args:
        symbol: Stock ticker symbol (e.g., 'VNM')
        start: Start date in YYYY-MM-DD format
        end: End date in YYYY-MM-DD format
        interval: Data interval ('1D' for daily, '1H' for hourly. Valid: 5m, 15m, 30m, 1H, 1D, 1W, 1M)
        request: IndicatorRequest with list of indicators to calculate

    Returns:
        Dictionary with calculated indicator data including series for charting
    """
    # Fetch OHLCV data
    ohlcv_result = get_stock_ohlcv(symbol.upper(), start, end, interval)
    if "error" in ohlcv_result:
        raise HTTPException(status_code=404, detail=ohlcv_result["error"])

    candles = ohlcv_result.get("data", [])
    if not candles:
        raise HTTPException(status_code=404, detail="No data found")

    # Convert to DataFrame
    df = create_ohlcv_dataframe(candles)

    # Calculate requested indicators with series_included parameter
    indicators_data = calculate_indicators(
        df, request.indicators, series_included=request.seriesIncluded
    )

    return {
        "symbol": symbol.upper(),
        "start": start,
        "end": end,
        "interval": interval,
        "indicators": indicators_data,
    }


@app.get("/indicators/available")
async def get_available_indicators_endpoint():
    """
    Returns list of all available indicators with their metadata.
    """
    return {"indicators": get_available_indicators()}


@app.get("/price/{symbol}")
async def get_latest_price(
    symbol: str = Path(..., description="Stock ticker symbol (e.g., 'VNM')"),
):
    """
    Returns the latest price data for a stock symbol.
    """
    result = get_latest_ohlcv(symbol.upper())
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/prices")
async def get_batch_prices(
    symbols: str = Query(
        ...,
        description="Comma-separated list of stock ticker symbols (e.g., 'VNM,SSI,HPG')",
    ),
):
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

        def get_component_content(component_name):
            component_path = os.path.join(
                app_dir, "components", f"{component_name}.html"
            )
            try:
                with open(component_path, "r", encoding="utf-8") as cf:
                    return cf.read()
            except Exception as e:
                logger.error(f"Error reading component {component_name}: {e}")
                return f"<!-- ERROR LOADING COMPONENT: {component_name} -->"

        def inject_component(match):
            component_name = match.group(1).strip()
            component_content = get_component_content(component_name)

            # Use BeautifulSoup to handle template attributes: <tag template="name">...</tag>
            soup = BeautifulSoup(component_content, "html.parser")
            for tag in soup.find_all(attrs={"template": True}):
                template_name = tag["template"]
                # Create the template tag
                template_tag = soup.new_tag("template", id=template_name)
                # Parse the content to allow nested tags within the template
                template_tag.extend(tag.contents)

                # Append after the original component content
                component_content = (
                    f"{component_content}\n{str(template_tag.prettify())}"
                )

            return component_content

        # 1. Replace all comment component markers: <!-- COMPONENT: component_name -->
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
                    sector=body.sector,
                    sector_name=body.sector_name,
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
