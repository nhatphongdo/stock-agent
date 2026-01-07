"""
Vietcap API tools for stock data retrieval.
These functions are designed to be used with Google AI function calling.
"""

import requests
import time
import logging
from typing import Optional, Any
from datetime import datetime, timedelta
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Common headers for Vietcap API
VIETCAP_HEADERS = {
    "Content-Type": "application/json",
    "Origin": "https://trading.vietcap.com.vn",
    "Referer": "https://trading.vietcap.com.vn/",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


def _make_request(method: str, url: str, **kwargs) -> Any:
    """
    Helper to make HTTP requests with standardized logging.

    Args:
        method: HTTP method ('GET', 'POST', etc.)
        url: Request URL
        **kwargs: Additional arguments for requests (headers, json, params, etc.)

    Returns:
        JSON response data or None if request fails
    """
    try:
        # Ensure headers are present
        if "headers" not in kwargs:
            kwargs["headers"] = VIETCAP_HEADERS

        start_time = time.time()
        response = requests.request(method, url, **kwargs)
        duration = time.time() - start_time

        content_size = len(response.content)
        logger.info(
            f"Request: {method} {url} - Response: {response.status_code} - Size: {content_size} bytes - Duration: {duration:.2f}s"
        )

        response.raise_for_status()
        return response.json()

    except Exception as e:
        logger.error(f"Request failed: {method} {url} - Error: {str(e)}")
        raise e


# Cache for company list (1 day TTL)
_company_list_cache: dict = {"data": None, "timestamp": None}
_COMPANY_LIST_CACHE_TTL = 86400  # 1 day in seconds

# Cache for companies by sector (1 day TTL)
# Key: icb_code_lv2, Value: {"data": list, "timestamp": float}
_companies_by_sector_cache: dict = {}

# Cache for all symbols (1 day TTL)
_all_symbols_cache: dict = {"data": None, "timestamp": None}
_SYMBOLS_CACHE_TTL = 86400  # 1 day in seconds


def get_company_list() -> list:
    """
    Get list of all companies from Vietcap search-bar API.
    Results are cached for 1 day.

    Returns:
        List of company dictionaries with id, ticker, and name
    """
    global _company_list_cache

    # Check cache validity
    if (
        _company_list_cache["data"] is not None
        and _company_list_cache["timestamp"] is not None
        and (time.time() - _company_list_cache["timestamp"]) < _COMPANY_LIST_CACHE_TTL
    ):
        return _company_list_cache["data"]

    try:
        url = "https://iq.vietcap.com.vn/api/iq-insight-service/v2/company/search-bar?language=1"
        data = _make_request("GET", url, headers=VIETCAP_HEADERS)

        if data and "data" in data and isinstance(data["data"], list):
            results = []
            for item in data["data"]:
                icb_lv1 = item.get("icbLv1") or {}
                icb_lv2 = item.get("icbLv2") or {}
                icb_lv3 = item.get("icbLv3") or {}
                icb_lv4 = item.get("icbLv4") or {}
                results.append(
                    {
                        "id": item.get("id"),
                        "ticker": item.get("code"),
                        "name": item.get("name"),
                        "exchange": item.get("floor"),
                        "icbCodeLv1": icb_lv1.get("code"),
                        "icbNameLv1": icb_lv1.get("name"),
                        "icbCodeLv2": icb_lv2.get("code"),
                        "icbNameLv2": icb_lv2.get("name"),
                        "icbCodeLv3": icb_lv3.get("code"),
                        "icbNameLv3": icb_lv3.get("name"),
                        "icbCodeLv4": icb_lv4.get("code"),
                        "icbNameLv4": icb_lv4.get("name"),
                        "dividendPerShareTsr": item.get("dividendPerShareTsr"),
                        "projectedTsrPercentage": item.get("projectedTsrPercentage"),
                    }
                )
            # Update cache
            _company_list_cache["data"] = results
            _company_list_cache["timestamp"] = time.time()
            return results
        return []
    except Exception as e:
        return [{"error": str(e)}]


def _filter_companies_by_criteria(
    companies: list,
    icb_code_lv2: str = None,
    dividend_rate: float = None,
    return_rate: float = None,
) -> list:
    """
    Internal helper to filter companies by sector and/or financial criteria.

    Args:
        companies: List of company dictionaries to filter
        icb_code_lv2: Optional ICB Level 2 sector code to filter by
        dividend_rate: Optional minimum dividend rate (dividendPerShareTsr / 10000)
        return_rate: Optional minimum projected TSR percentage

    Returns:
        List of filtered company dictionaries with calculated dividendRate added
    """
    # Get all valid symbols to filter out delisted/invalid tickers
    all_symbols = get_all_symbols()

    filtered = []
    for company in companies:
        # Filter out companies not in all_symbols or that are DELISTED
        ticker = company.get("ticker")
        if ticker not in all_symbols:
            continue
        symbol_info = all_symbols.get(ticker, {})
        if symbol_info.get("exchange") == "DELISTED" or (
            symbol_info.get("type") != "STOCK" and symbol_info.get("type") != "ETF"
        ):
            continue

        # Apply sector filter if specified
        if icb_code_lv2 is not None:
            if company.get("icbCodeLv2") != icb_code_lv2:
                continue

        dividend_per_share = company.get("dividendPerShareTsr")
        projected_tsr = company.get("projectedTsrPercentage")

        # Calculate dividend rate if dividend_per_share is available
        calculated_dividend_rate = None
        if dividend_per_share is not None:
            calculated_dividend_rate = dividend_per_share / 10000

        # Apply dividend_rate filter if specified
        if dividend_rate is not None:
            if (
                calculated_dividend_rate is not None
                and calculated_dividend_rate < dividend_rate
            ):
                continue

        # Apply return_rate filter if specified
        if return_rate is not None:
            if projected_tsr is not None and projected_tsr < return_rate:
                continue

        # Add calculated dividend rate to the company data
        company_with_rate = company.copy()
        company_with_rate["dividendRate"] = (
            round(calculated_dividend_rate, 4) if calculated_dividend_rate else None
        )
        filtered.append(company_with_rate)

    return filtered


def get_companies_by_financial_criteria(
    dividend_rate: float = None, return_rate: float = None
) -> list:
    """
    Get list of companies filtered by dividend rate and/or return rate criteria.

    Args:
        dividend_rate: Minimum dividend rate (dividendPerShareTsr / currentPrice).
                       For example, 0.05 means 5% dividend yield.
        return_rate: Minimum projected TSR percentage.
                     For example, 0.10 means 10% projected return.

    Returns:
        List of company dictionaries that meet the specified criteria.
        Each company includes ticker, name, currentPrice, dividendPerShareTsr,
        projectedTsrPercentage, and calculated dividendRate.
    """
    try:
        companies = get_company_list()
        if companies and len(companies) > 0 and "error" in companies[0]:
            return companies  # Return error if get_company_list failed

        return _filter_companies_by_criteria(
            companies, dividend_rate=dividend_rate, return_rate=return_rate
        )
    except Exception as e:
        return [{"error": str(e)}]


def get_companies_by_sector(
    icb_code_lv2: str,
    dividend_rate: float = None,
    return_rate: float = None,
) -> list:
    """
    Get list of companies filtered by their sector (ICB Level 2 code).
    Optionally filter by dividend rate and/or return rate criteria.
    Results are cached for 1 day per sector (base filter only, financial filters applied on cached data).

    Args:
        icb_code_lv2: ICB Level 2 sector code (e.g., '1300' for Chemicals, '8600' for Banks)
        dividend_rate: Optional minimum dividend rate (dividendPerShareTsr / 10000).
                       For example, 0.05 means 5% dividend yield.
        return_rate: Optional minimum projected TSR percentage.
                     For example, 0.10 means 10% projected return.

    Returns:
        List of company dictionaries with id, ticker, name, ICB codes, and dividendRate
        that match the sector and optional financial criteria
    """
    global _companies_by_sector_cache

    # Check cache validity for this sector (base sector filter only)
    cached_sector_companies = None
    if icb_code_lv2 in _companies_by_sector_cache:
        cache_entry = _companies_by_sector_cache[icb_code_lv2]
        if (
            cache_entry["data"] is not None
            and cache_entry["timestamp"] is not None
            and (time.time() - cache_entry["timestamp"]) < _COMPANY_LIST_CACHE_TTL
        ):
            cached_sector_companies = cache_entry["data"]

    try:
        if cached_sector_companies is None:
            companies = get_company_list()
            if companies and len(companies) > 0 and "error" in companies[0]:
                return companies  # Return error if get_company_list failed

            # Filter by sector only for caching
            cached_sector_companies = [
                company
                for company in companies
                if company.get("icbCodeLv2") == icb_code_lv2
            ]

            # Update cache for this sector
            _companies_by_sector_cache[icb_code_lv2] = {
                "data": cached_sector_companies,
                "timestamp": time.time(),
            }

        # Apply financial filters on cached sector data
        if dividend_rate is not None or return_rate is not None:
            return _filter_companies_by_criteria(
                cached_sector_companies,
                dividend_rate=dividend_rate,
                return_rate=return_rate,
            )

        # If no financial filters, add dividendRate calculation and return
        return _filter_companies_by_criteria(cached_sector_companies)
    except Exception as e:
        return [{"error": str(e)}]


def get_company_info(ticker: str) -> dict:
    """
    Get basic company information for a stock ticker.

    Args:
        ticker: Stock ticker symbol (e.g., 'VNM', 'SSI', 'VND')

    Returns:
        Structured company information for the trading agent
    """
    try:
        url = f"https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/{ticker}"
        data = _make_request("GET", url, headers=VIETCAP_HEADERS)

        if data and "data" in data and data["data"]:
            d = data["data"]
            return {
                "ticker": ticker,
                "name": d.get("viOrganName"),
                "sector": d.get("sectorVn"),
                "currentPrice": d.get("currentPrice"),
                "rating": d.get("rating"),
                "analyst": d.get("analyst"),
                "marketCap": d.get("marketCap"),
                "highestPrice1Year": d.get("highestPrice1Year"),
                "lowestPrice1Year": d.get("lowestPrice1Year"),
                "averageMatchValue1Month": d.get("averageMatchValue1Month"),
                "averageMatchVolume1Month": d.get("averageMatchVolume1Month"),
                "dividendPerShareTsr": d.get("dividendPerShareTsr"),
                "projectedTSRPercentage": d.get("projectedTSRPercentage"),
                "numberOfSharesMktCap": d.get("numberOfSharesMktCap"),
            }
        return {"error": "No data found", "ticker": ticker}
    except Exception as e:
        return {"error": str(e), "ticker": ticker}


def get_ohlcv_data(
    ticker: str | list[str],
    count_back: int = 250,
    timeframe: str = "ONE_DAY",
    to_time: Optional[int] = None,
) -> dict:
    """
    Get OHLCV (Open, High, Low, Close, Volume) price data for one or more stocks.

    Args:
        ticker: Single stock ticker symbol or list of symbols
        count_back: Number of data points to retrieve (default 250)
        timeframe: Time interval - ONE_MINUTE, ONE_HOUR, ONE_DAY
        to_time: Optional timestamp to get data up to

    Returns:
        Dict mapping each ticker to its candle data, or error info
    """
    try:
        symbols = [ticker] if isinstance(ticker, str) else ticker
        url = "https://trading.vietcap.com.vn/api/chart/OHLCChart/gap-chart"
        payload = {
            "symbols": symbols,
            "timeFrame": timeframe,
            "countBack": count_back,
            "to": to_time if to_time else int(time.time()),
        }
        data = _make_request("POST", url, json=payload, headers=VIETCAP_HEADERS)

        if not data or not isinstance(data, list):
            return {"error": "No data found", "tickers": symbols}

        results = {}
        for stock_data in data:
            current_symbol = stock_data.get("symbol")
            if current_symbol and "o" in stock_data:
                candles = []
                for i in range(len(stock_data["o"])):
                    time_val = stock_data["t"][i] if i < len(stock_data["t"]) else 0
                    time_str = (
                        datetime.fromtimestamp(int(time_val)).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                        if time_val
                        else "N/A"
                    )
                    candles.append(
                        {
                            "open": (
                                stock_data["o"][i] if i < len(stock_data["o"]) else None
                            ),
                            "high": (
                                stock_data["h"][i] if i < len(stock_data["h"]) else None
                            ),
                            "low": (
                                stock_data["l"][i] if i < len(stock_data["l"]) else None
                            ),
                            "close": (
                                stock_data["c"][i] if i < len(stock_data["c"]) else None
                            ),
                            "volume": (
                                stock_data["v"][i] if i < len(stock_data["v"]) else None
                            ),
                            "timestamp": time_str,
                            "_ts": time_val,  # For sorting
                        }
                    )
                # Sort by timestamp ascending (oldest first, newest last)
                candles.sort(key=lambda x: x.get("_ts", 0))
                # Remove internal sorting key
                for c in candles:
                    c.pop("_ts", None)
                results[current_symbol] = candles

        return results
    except Exception as e:
        return {"error": str(e), "ticker": str(ticker)}


def get_latest_price_batch(tickers: list[str]) -> dict:
    """
    Get the latest OHLCV data for multiple stocks in a single request.
    """
    if not tickers:
        return {}

    # Get data of 1 trading day for buffer, 6.5 hours * 60 minutes
    data = get_ohlcv_data(tickers, count_back=390, timeframe="ONE_MINUTE")
    if "error" in data:
        return data

    results = {}
    for ticker in tickers:
        candles = data.get(ticker, [])
        if candles:
            latest = candles[-1]
            results[ticker] = {
                "ticker": ticker,
                "open": latest.get("open"),
                "high": latest.get("high"),
                "low": latest.get("low"),
                "close": latest.get("close"),
                "volume": latest.get("volume"),
                "timestamp": latest.get("timestamp"),
            }
        else:
            results[ticker] = {"error": "No data found", "ticker": ticker}
    return results


def get_latest_ohlcv(ticker: str) -> dict:
    """
    Get the latest OHLCV (Open, High, Low, Close, Volume) data for a stock.
    """
    results = get_latest_price_batch([ticker])
    if "error" in results:
        return results
    return results.get(ticker, {"error": "No data found", "ticker": ticker})


def get_ohlcv_by_day(ticker: str, days: int = 30) -> dict:
    """
    Get OHLCV data for multiple days, organized by date.

    Args:
        ticker: Stock ticker symbol (e.g., 'VNM', 'SSI')
        days: Number of days to retrieve (default 30)

    Returns:
        Dict with dates (YYYY-MM-DD) as keys and OHLCV data as values
    """
    result = get_ohlcv_data(
        ticker, count_back=days + (days // 7 + 1) * 2, timeframe="ONE_DAY"
    )  # Buffer days for weekends
    if "error" in result:
        return result

    candles = result.get(ticker, [])
    if len(candles) > 0:
        price_by_date = {}
        for candle in candles:
            timestamp = candle.get("timestamp", "")
            # Extract date part (YYYY-MM-DD) from timestamp
            date_key = timestamp.split(" ")[0] if timestamp else None
            if date_key:
                price_by_date[date_key] = {
                    "open": candle.get("open"),
                    "high": candle.get("high"),
                    "low": candle.get("low"),
                    "close": candle.get("close"),
                    "volume": candle.get("volume"),
                }
        return {"ticker": ticker, "prices": price_by_date}
    return {"error": "No data found", "ticker": ticker}


def get_technical_indicators(ticker: str, timeframe: str = "ONE_DAY") -> dict:
    """
    Get technical analysis indicators for a stock.

    Args:
        ticker: Stock ticker symbol
        timeframe: ONE_DAY or ONE_WEEK

    Returns:
        Structured technical indicators (RSI, MACD, Moving Averages, Gauges, Pivot)
    """
    try:
        url = f"https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/{ticker}/technical/{timeframe}"
        data = _make_request("GET", url, headers=VIETCAP_HEADERS)

        if data and "data" in data:
            d = data["data"]

            # Extract all oscillators as dict
            oscillators = {
                osc.get("name", "").lower(): {
                    "value": osc.get("value"),
                    "rating": osc.get("rating"),
                }
                for osc in d.get("oscillators", [])
                if osc and osc.get("name")
            }

            # Extract all moving averages as dict
            moving_averages = {
                ma.get("name", "").lower(): {
                    "value": ma.get("value"),
                    "rating": ma.get("rating"),
                }
                for ma in d.get("movingAverages", [])
                if ma and ma.get("name")
            }

            return {
                "ticker": ticker,
                "timeframe": timeframe,
                "indicators": {
                    # Key oscillators
                    "rsi": (
                        round(oscillators.get("rsi", {}).get("value", 0), 2)
                        if oscillators.get("rsi", {}).get("value")
                        else None
                    ),
                    "macd": (
                        round(oscillators.get("macd", {}).get("value", 0), 2)
                        if oscillators.get("macd", {}).get("value")
                        else None
                    ),
                    "stochastic": oscillators.get("stochastic", {}).get("value"),
                    "momentum": oscillators.get("momentum", {}).get("value"),
                    # Key moving averages
                    "sma20": moving_averages.get("sma20", {}).get("value"),
                    "sma50": moving_averages.get("sma50", {}).get("value"),
                    "sma100": moving_averages.get("sma100", {}).get("value"),
                    "sma200": moving_averages.get("sma200", {}).get("value"),
                    "ema20": moving_averages.get("ema20", {}).get("value"),
                    "ema50": moving_averages.get("ema50", {}).get("value"),
                },
                "gauges": {
                    "summary": d.get("gaugeSummary", {}),
                    "movingAverage": d.get("gaugeMovingAverage", {}),
                    "oscillator": d.get("gaugeOscillator", {}),
                },
                "pivot": d.get("pivot", {}),
                "fibonacci": {
                    "resistance1": (
                        round(d.get("pivot", {}).get("fibResistance1", 0), 2)
                        if d.get("pivot", {}).get("fibResistance1")
                        else None
                    ),
                    "resistance2": (
                        round(d.get("pivot", {}).get("fibResistance2", 0), 2)
                        if d.get("pivot", {}).get("fibResistance2")
                        else None
                    ),
                    "resistance3": (
                        round(d.get("pivot", {}).get("fibResistance3", 0), 2)
                        if d.get("pivot", {}).get("fibResistance3")
                        else None
                    ),
                    "support1": (
                        round(d.get("pivot", {}).get("fibSupport1", 0), 2)
                        if d.get("pivot", {}).get("fibSupport1")
                        else None
                    ),
                    "support2": (
                        round(d.get("pivot", {}).get("fibSupport2", 0), 2)
                        if d.get("pivot", {}).get("fibSupport2")
                        else None
                    ),
                    "support3": (
                        round(d.get("pivot", {}).get("fibSupport3", 0), 2)
                        if d.get("pivot", {}).get("fibSupport3")
                        else None
                    ),
                },
            }
        return {"error": "No data found", "ticker": ticker}
    except Exception as e:
        return {"error": str(e), "ticker": ticker}


def get_financial_ratios(ticker: str, length_report: int = 10) -> dict:
    """
    Get financial ratios (P/E, P/B) for a stock.

    Args:
        ticker: Stock ticker symbol (use 'VNINDEX' for index data)
        length_report: Number of periods to retrieve

    Returns:
        Daily P/E and P/B ratios
    """
    try:
        url = f"https://iq.vietcap.com.vn/api/iq-insight-service/v1/company-ratio-daily/{ticker}?lengthReport=10"
        data = _make_request("GET", url, headers=VIETCAP_HEADERS)

        if data and "data" in data:
            results = []
            # Calculate cutoff date based on length_report (days)
            cutoff_date = (datetime.now() - timedelta(days=length_report)).strftime(
                "%Y-%m-%d"
            )
            for r in data["data"]:
                trade_date = r.get("tradingDate", "").split("T")[0]
                # Filter by date
                if trade_date and trade_date >= cutoff_date:
                    results.append(
                        {
                            "date": trade_date,
                            "pe": (
                                round(r.get("pe"), 2)
                                if r.get("pe") is not None
                                else None
                            ),
                            "pb": (
                                round(r.get("pb"), 2)
                                if r.get("pb") is not None
                                else None
                            ),
                        }
                    )
            return {"ticker": ticker, "ratios": results}
        return {"error": "No data found", "ticker": ticker}

    except Exception as e:
        return {"error": str(e), "ticker": ticker}


def get_short_financial(ticker: str, length_report: int = 10) -> dict:
    """
    Get short financial summary for a stock.

    Args:
        ticker: Stock ticker symbol
        length_report: Number of periods

    Returns:
        Key financial metrics summary
    """
    try:
        url = f"https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/{ticker}/short-financial?lengthReport={length_report}"
        data = _make_request("GET", url, headers=VIETCAP_HEADERS)

        if data and "data" in data:
            results = []
            for r in data["data"]:
                results.append(
                    {
                        "period": r.get("quarter"),
                        "yearReport": r.get("yearReport"),
                        # Revenue & Profit
                        "revenue": r.get("revenue"),
                        "revenueGrowth": (
                            round(r.get("revenueGrowth", 0) * 100, 2)
                            if r.get("revenueGrowth")
                            else None
                        ),
                        "netProfit": r.get("npatMi"),
                        "netProfitGrowth": (
                            round(r.get("npatMiGrowth", 0) * 100, 2)
                            if r.get("npatMiGrowth")
                            else None
                        ),
                        # Margins
                        "grossMargin": (
                            round(r.get("grossMargin", 0) * 100, 2)
                            if r.get("grossMargin")
                            else None
                        ),
                        "netMargin": (
                            round(r.get("npatMiMargin", 0) * 100, 2)
                            if r.get("npatMiMargin")
                            else None
                        ),
                        # Efficiency
                        "eps": r.get("eps"),
                        "roe": (
                            round(r.get("roe", 0) * 100, 2) if r.get("roe") else None
                        ),
                        "roa": (
                            round(r.get("roa", 0) * 100, 2) if r.get("roa") else None
                        ),
                        # Balance sheet
                        "totalAsset": r.get("totalAsset"),
                        "totalEquity": r.get("totalEquity"),
                        "totalDebt": r.get("totalDebts"),
                        "cash": r.get("cash"),
                        "inventory": r.get("inventory"),
                        # Liquidity & Leverage
                        "currentRatio": (
                            round(r.get("currentRatio", 0), 2)
                            if r.get("currentRatio")
                            else None
                        ),
                        "quickRatio": (
                            round(r.get("quickRatio", 0), 2)
                            if r.get("quickRatio")
                            else None
                        ),
                        "debtEquity": (
                            round(r.get("debtPerEquity", 0), 2)
                            if r.get("debtPerEquity")
                            else None
                        ),
                    }
                )
            return {"ticker": ticker, "financials": results}
        return {"error": "No data found", "ticker": ticker}
    except Exception as e:
        return {"error": str(e), "ticker": ticker}


def get_last_quarter_financial(ticker: str) -> dict:
    """
    Get the most recent quarterly financial data for a stock.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Latest quarter financial statements including revenue, profit, assets, liabilities
    """
    try:
        url = f"https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/{ticker}/last-quarter-financial"
        data = _make_request("GET", url, headers=VIETCAP_HEADERS)

        if data and "data" in data:
            d = data["data"]
            return {
                "ticker": ticker,
                "quarter": d.get("quarter"),
                "year": d.get("yearReport"),
                "revenue": d.get("revenue"),
                "netProfit": d.get("npatMi"),
                "eps": d.get("eps"),
                "pe": d.get("pe"),
                "pb": d.get("pb"),
            }
        return {"error": "No data found", "ticker": ticker}
    except Exception as e:
        return {"error": str(e), "ticker": ticker}


def get_price_earnings(ticker: str) -> dict:
    """
    Get price and earnings data for a stock (P/E trends).

    Args:
        ticker: Stock ticker symbol

    Returns:
        Structured P/E history data
    """
    try:
        url = f"https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/{ticker}/price-earnings"
        data = _make_request("GET", url, headers=VIETCAP_HEADERS)

        if data and "data" in data and isinstance(data["data"], list):
            results = []
            for r in data["data"]:
                results.append(
                    {
                        "date": (r.get("publicDate") or "").split("T")[0],
                        "npatMi": r.get("npatMi"),
                    }
                )
            return {"ticker": ticker, "earningsHistory": results}
        return {"error": "No data found", "ticker": ticker}
    except Exception as e:
        return {"error": str(e), "ticker": ticker}


def get_annual_return(ticker: str, length_report: int = 10) -> dict:
    """
    Get annual return percentage for a stock.

    Args:
        ticker: Stock ticker symbol
        length_report: Number of years

    Returns:
        Annual return rates over specified years
    """
    try:
        url = f"https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/{ticker}/annual-return?lengthReport={length_report}"
        data = _make_request("GET", url, headers=VIETCAP_HEADERS)

        if data and "data" in data and data["data"]:
            results = []
            for r in data["data"]:
                results.append(
                    {
                        "year": r.get("year"),
                        "stockReturn": (
                            round(r.get("stockReturn", 0) * 100, 2)
                            if r.get("stockReturn")
                            else None
                        ),
                        "vnIndex": (
                            round(r.get("vnIndex", 0) * 100, 2)
                            if r.get("vnIndex")
                            else None
                        ),
                        "outperformance": (
                            round(r.get("annualOutperformanceVNIndex", 0) * 100, 2)
                            if r.get("annualOutperformanceVNIndex")
                            else None
                        ),
                    }
                )
            return {"ticker": ticker, "returns": results}
        return {"error": "No data found", "ticker": ticker}
    except Exception as e:
        return {"error": str(e), "ticker": ticker}


def get_stock_news(
    ticker: str, from_date: Optional[str] = None, to_date: Optional[str] = None
) -> dict:
    """
    Get news articles related to a stock.

    Args:
        ticker: Stock ticker symbol
        from_date: Start date in YYYYMMDD format (default: 30 days ago)
        to_date: End date in YYYYMMDD format (default: today)

    Returns:
        List of news articles with title, date, and content summary
    """
    try:
        if to_date is None:
            to_date = datetime.now().strftime("%Y%m%d")
        if from_date is None:
            from_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")

        url = f"https://iq.vietcap.com.vn/api/iq-insight-service/v1/news?ticker={ticker}&fromDate={from_date}&toDate={to_date}&languageId=1&page=0&size=20"
        data = _make_request("GET", url, headers=VIETCAP_HEADERS)

        if data and "data" in data and "content" in data["data"]:
            results = []
            for n in data["data"]["content"]:
                results.append(
                    {
                        "title": n.get("newsTitle"),
                        "date": n.get("publicDate", "").split("T")[0],
                        "link": "",
                        "source": "Vietcap",
                    }
                )
            return {"ticker": ticker, "news": results}
        return {"ticker": ticker, "news": []}
    except Exception as e:
        return {"error": str(e), "ticker": ticker}


def get_company_news(ticker: str, lang: str = "vi") -> dict:
    """
    Get company news articles using GraphQL API.

    Args:
        ticker: Stock ticker symbol
        lang: Language code ('vi' or 'en')

    Returns:
        Dictionary containing news articles
    """
    try:
        url = "https://trading.vietcap.com.vn/data-mt/graphql"
        query = """
        query Query($ticker: String!, $lang: String!) {
          News(ticker: $ticker, langCode: $lang) {
            id
            newsTitle
            publicDate
            newsShortContent
            newsSourceLink
          }
        }
        """
        payload = {"query": query, "variables": {"ticker": ticker, "lang": lang}}

        data = _make_request("POST", url, json=payload, headers=VIETCAP_HEADERS)

        def parse_date(d):
            if not d:
                return "N/A"
            if isinstance(d, int):
                # Handle timestamp (ms or s)
                try:
                    ts = d / 1000 if d > 1e11 else d
                    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                except:
                    return str(d)
            if isinstance(d, str):
                return d.split("T")[0]
            return str(d)

        result = {"ticker": ticker, "news": []}

        if data and "data" in data and "News" in data["data"]:
            for n in data["data"]["News"]:
                link = n.get("newsSourceLink")
                source = "Vietcap"
                if link:
                    try:
                        parsed_uri = urlparse(link)
                        source = parsed_uri.netloc.replace("www.", "")
                    except:
                        pass

                result["news"].append(
                    {
                        "title": n.get("newsTitle"),
                        "date": parse_date(n.get("publicDate")),
                        "description": n.get("newsShortContent"),
                        "link": link,
                        "source": source,
                    }
                )

        return result
    except Exception as e:
        return {"error": str(e), "ticker": ticker}


def get_analysis_reports(ticker: str, lang: str = "vi") -> dict:
    """
    Get analysis reports for a stock using GraphQL API.

    Args:
        ticker: Stock ticker symbol
        lang: Language code ('vi' or 'en')

    Returns:
        Dictionary containing analysis reports
    """
    try:
        url = "https://trading.vietcap.com.vn/data-mt/graphql"
        query = """
        query Query($ticker: String!, $lang: String!) {
          AnalysisReportFiles(ticker: $ticker, langCode: $lang) {
            date
            description
            link
            name
            __typename
          }
        }
        """
        payload = {"query": query, "variables": {"ticker": ticker, "lang": lang}}

        data = _make_request("POST", url, json=payload, headers=VIETCAP_HEADERS)

        def parse_date(d):
            if not d:
                return "N/A"
            if isinstance(d, int):
                # Handle timestamp (ms or s)
                try:
                    ts = d / 1000 if d > 1e11 else d
                    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                except:
                    return str(d)
            if isinstance(d, str):
                return d.split("T")[0]
            return str(d)

        result = {"ticker": ticker, "reports": []}

        if data and "data" in data and "AnalysisReportFiles" in data["data"]:
            for r in data["data"]["AnalysisReportFiles"]:
                link = r.get("link")
                source = "Vietcap"
                if link:
                    try:
                        parsed_uri = urlparse(link)
                        source = parsed_uri.netloc.replace("www.", "")
                    except:
                        pass

                result["reports"].append(
                    {
                        "date": parse_date(r.get("date")),
                        "description": r.get("description"),
                        "link": link,
                        "title": r.get("name"),
                        "source": source,
                    }
                )

        return result
    except Exception as e:
        return {"error": str(e), "ticker": ticker}


def get_company_events(ticker: str) -> dict:
    """
    Get corporate events for a stock using GraphQL API.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dictionary containing corporate events
    """
    try:
        url = "https://trading.vietcap.com.vn/data-mt/graphql"
        query = """
        query Query($ticker: String!) {
          OrganizationEvents(ticker: $ticker) {
            id
            eventTitle
            en_EventTitle
            publicDate
            issueDate
            sourceUrl
            eventListCode
            ratio
            value
            recordDate
            exrightDate
            eventListName
            en_EventListName
          }
        }
        """
        payload = {"query": query, "variables": {"ticker": ticker}}

        data = _make_request("POST", url, json=payload, headers=VIETCAP_HEADERS)

        def parse_date(d):
            if not d:
                return "N/A"
            if isinstance(d, int):
                # Handle timestamp (ms or s)
                try:
                    ts = d / 1000 if d > 1e11 else d
                    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                except:
                    return str(d)
            if isinstance(d, str):
                return d.split("T")[0]
            return str(d)

        result = {"ticker": ticker, "events": []}

        if data and "data" in data and "OrganizationEvents" in data["data"]:
            for e in data["data"]["OrganizationEvents"]:
                link = e.get("sourceUrl")
                source = "Vietcap"
                if link:
                    try:
                        parsed_uri = urlparse(link)
                        source = parsed_uri.netloc.replace("www.", "")
                    except:
                        pass

                result["events"].append(
                    {
                        "id": e.get("id"),
                        "title": e.get("eventTitle"),
                        "en_title": e.get("en_EventTitle"),
                        "date": parse_date(e.get("publicDate")),
                        "issueDate": parse_date(e.get("issueDate")),
                        "exrightDate": parse_date(e.get("exrightDate")),
                        "recordDate": parse_date(e.get("recordDate")),
                        "ratio": e.get("ratio"),
                        "value": e.get("value"),
                        "eventTypeName": e.get("eventListName"),
                        "link": link,
                        "source": source,
                    }
                )

        return result
    except Exception as e:
        return {"error": str(e), "ticker": ticker}


def get_stock_events(
    ticker: str, from_date: Optional[str] = None, to_date: Optional[str] = None
) -> dict:
    """
    Get corporate events for a stock (dividends, meetings, etc.).

    Args:
        ticker: Stock ticker symbol
        from_date: Start date in YYYYMMDD format (default: 90 days ago)
        to_date: End date in YYYYMMDD format (default: today)

    Returns:
        List of corporate events including dividends, shareholder meetings, etc.
    """
    try:
        if to_date is None:
            to_date = datetime.now().strftime("%Y%m%d")
        if from_date is None:
            from_date = (datetime.now() - timedelta(days=90)).strftime("%Y%m%d")

        event_codes = "DIV,ISS,AGME,AGMR,EGME,DDIND,DDINS,DDRP,DDALL,OTHE,AIS,NLIS,RETU,SUSP,MA,MOVE"
        url = f"https://iq.vietcap.com.vn/api/iq-insight-service/v2/events?toDate={to_date}&fromDate={from_date}&tickers={ticker}&eventCodes={event_codes}&page=0"
        data = _make_request("GET", url, headers=VIETCAP_HEADERS)

        if data and "data" in data and "content" in data["data"]:
            results = []
            for e in data["data"]["content"]:
                results.append(
                    {
                        "ticker": e.get("ticker"),
                        "event": e.get("eventCode"),
                        "title": e.get("titleVi"),
                        "date": e.get("publishDate", "").split("T")[0],
                        "exDividendDate": (
                            e.get("exDividendDate", "").split("T")[0]
                            if e.get("exDividendDate")
                            else None
                        ),
                    }
                )
            return {"ticker": ticker, "events": results}
        return {"ticker": ticker, "events": []}
    except Exception as e:
        return {"error": str(e), "ticker": ticker}


def get_sector_comparison(ticker: str) -> dict:
    """
    Get stock performance compared to sector peers.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Comparison of stock performance vs sector peers
    """
    try:
        url = f"https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/{ticker}/stock-return-coverage-peers"
        data = _make_request("GET", url, headers=VIETCAP_HEADERS)

        if data and "data" in data:
            results = []
            for p in data["data"]:
                results.append(
                    {
                        "ticker": p.get("ticker"),
                        "name": p.get("viOrganName"),
                        "return1M": (
                            round(p.get("stockReturn1M", 0) * 100, 2)
                            if p.get("stockReturn1M")
                            else None
                        ),
                        "return3M": (
                            round(p.get("stockReturn3M", 0) * 100, 2)
                            if p.get("stockReturn3M")
                            else None
                        ),
                        "return1Y": (
                            round(p.get("stockReturn1Y", 0) * 100, 2)
                            if p.get("stockReturn1Y")
                            else None
                        ),
                        "rating": p.get("rating"),
                    }
                )
            return {"ticker": ticker, "peers": results}
        return {"error": "No data found", "ticker": ticker}
    except Exception as e:
        return {"error": str(e), "ticker": ticker}


def get_all_symbols() -> dict:
    """
    Get all available stock symbols from Vietnamese exchanges.
    Results are cached for 1 day.

    Returns:
        Dictionary mapping symbols to {name, exchange}
    """
    global _all_symbols_cache

    # Check cache validity
    if (
        _all_symbols_cache["data"] is not None
        and _all_symbols_cache["timestamp"] is not None
        and (time.time() - _all_symbols_cache["timestamp"]) < _SYMBOLS_CACHE_TTL
    ):
        return _all_symbols_cache["data"]

    try:
        url = "https://trading.vietcap.com.vn/api/price/symbols/getAll"
        data = _make_request("GET", url, headers=VIETCAP_HEADERS, timeout=15)

        if data:
            results = {}
            for s in data:
                symbol = s.get("symbol")
                if symbol:
                    results[symbol] = {
                        "name": s.get("organName"),
                        "exchange": s.get("board"),
                        "type": s.get("type"),
                    }
            # Update cache
            _all_symbols_cache["data"] = results
            _all_symbols_cache["timestamp"] = time.time()
            return results
        return {}
    except Exception as e:
        return {"error": str(e)}


def get_top_tickers(top_pos: int = 5, top_neg: int = 5, group: str = "all") -> dict:
    """
    Get top performing and worst performing stocks.

    Args:
        top_pos: Number of top gaining stocks to return (default 10)
        top_neg: Number of top losing stocks to return (default 10)
        group: Exchange group - 'hose', 'hnx', 'upcom', or 'all' (default 'hose')

    Returns:
        Dictionary with 'top_positive' and 'top_negative' lists of tickers with price changes
    """
    try:
        url = f"https://ai.vietcap.com.vn/api/get_top_tickers?top_neg={top_neg}&top_pos={top_pos}&group={group}"
        data = _make_request("GET", url, headers=VIETCAP_HEADERS)

        if data and "ticker_info" in data:
            return [
                {
                    "ticker": t.get("ticker"),
                    "name": t.get("organ_name"),
                    "sentiment": t.get("sentiment"),
                    "score": t.get("score"),
                }
                for t in data["ticker_info"]
            ]
        return []
    except Exception as e:
        return {"error": str(e)}


def get_trending_news(language: int = 1) -> dict:
    """
    Get trending news and reports from the market.

    Args:
        language: Language code - 1 for Vietnamese, 2 for English (default 1)

    Returns:
        List of trending news articles and reports
    """
    try:
        url = f"https://www.vietcap.com.vn/api/cms-service/v1/report/trending?language={language}"
        data = _make_request("GET", url, headers=VIETCAP_HEADERS)

        if data and "data" in data:

            def format_datetime(iso_date):
                try:
                    if iso_date:
                        dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
                        return dt.strftime("%d/%m/%Y %H:%M")
                except:
                    pass
                return iso_date or "N/A"

            return [
                {
                    "title": r.get("name"),
                    "ticker": r.get("ticker"),
                    "date": format_datetime(r.get("date")),
                    "detail": r.get("detail"),
                }
                for r in data["data"]
                if r.get("name")
            ]
        return []
    except Exception as e:
        return {"error": str(e)}


def get_coverage_universe() -> dict:
    """
    Get list of stocks covered by Vietcap analysts with ratings and target prices.

    Returns:
        List of stocks with analyst coverage including rating, target price, and recommendations
    """
    try:
        url = "https://iq.vietcap.com.vn/api/iq-insight-service/v1/coverage-universe"
        data = _make_request("GET", url, headers=VIETCAP_HEADERS)

        if data and "data" in data:
            results = []
            for c in data["data"]:
                results.append(
                    {
                        "ticker": c.get("ticker"),
                        "rating": c.get("rating"),
                        "targetPrice": c.get("targetPrice"),
                        "upside": (
                            round(c.get("upside", 0) * 100, 2)
                            if c.get("upside")
                            else None
                        ),
                        "analyst": c.get("analyst"),
                    }
                )
            return results
        return []
    except Exception as e:
        return {"error": str(e)}


# Exclude this from tools
def get_stock_ohlcv(
    symbol: str, start_date: str, end_date: str, interval: str = "1D"
) -> dict:
    """
    Fetches OHLCV data for a stock ticker within a date range.
    """
    import pandas as pd

    # Map interval to vietcap timeframe
    tf_map = {
        "5m": "ONE_MINUTE",
        "15m": "ONE_MINUTE",
        "30m": "ONE_MINUTE",
        "1H": "ONE_HOUR",
        "1D": "ONE_DAY",
        "1W": "ONE_DAY",
        "1M": "ONE_DAY",
    }
    timeframe = tf_map.get(interval, "ONE_DAY")

    # Calculate count_back based on start_date to end_date (or now)
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else datetime.now()

        business_days = len(pd.bdate_range(start=start_dt, end=end_dt))
        business_days += (
            business_days // 260 + 1
        ) * 20  # Buffer holidays, 20 days / year, 260 weekdays / year
        if timeframe == "ONE_DAY":
            # Exact trading days count (excluding weekends)
            count_back = business_days + 1
        elif timeframe == "ONE_HOUR":
            # Days * 6.5 trading hours per day
            count_back = int((business_days * 6.5) + 1)
        elif timeframe == "ONE_MINUTE":
            # Days * 6.5 trading hours per day * 60 minutes per hour
            count_back = int((business_days * 6.5 * 60) + 1)
        else:
            count_back = 1000  # Default fallback

    except Exception as e:
        count_back = 1000

    result = get_ohlcv_data(
        symbol,
        count_back=count_back,
        timeframe=timeframe,
        to_time=int(end_dt.timestamp())
        + 86400,  # end_dt is start of day so need to add 1 day to cover intraday data
    )
    if "error" in result:
        return result

    candles = result.get(symbol, [])
    if not candles:
        return {"symbol": symbol, "interval": interval, "data": []}

    # Convert to DataFrame for easier manipulation and resampling
    df = pd.DataFrame(candles)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.set_index("timestamp", inplace=True)

    # Filter by date range before resampling
    df = df[(df.index >= start_dt) & (df.index <= end_dt + timedelta(days=1))]

    # Map interval to pandas frequency for resampling
    agg_map = {
        "5m": "5min",
        "15m": "15min",
        "30m": "30min",
        "1H": "1h",
        "1D": "1D",
        "1W": "W-MON",
        "1M": "ME",
    }

    freq = agg_map.get(interval)

    if freq and freq != timeframe:
        # Resample data if the interval is different from the base timeframe fetched
        resampled = (
            df.resample(freq, closed="left", label="left")
            .agg(
                {
                    "open": "first",
                    "high": "max",
                    "low": "min",
                    "close": "last",
                    "volume": "sum",
                }
            )
            .dropna()
        )
        df = resampled

    # Convert back to the expected list of dictionaries
    filtered_data = []
    for ts, row in df.iterrows():
        dt_str = ts.strftime("%Y-%m-%d %H:%M:%S")
        # Final filter check (safety)
        if start_date <= dt_str.split(" ")[0] <= (end_date or "9999-12-31"):
            filtered_data.append(
                {
                    "time": dt_str,
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": int(row["volume"]),
                }
            )

    return {"symbol": symbol, "interval": interval, "data": filtered_data}


def get_company_analysis(
    ticker: str,
    page: int = 0,
    size: int = 20,
) -> dict:
    """
    Get company analysis reports from Vietcap CMS.

    Args:
        ticker: Stock ticker symbol (e.g., 'VNM', 'SSI')
        page: Page number for pagination (default 0)
        size: Number of results per page (default 20)

    Returns:
        List of analysis reports for the company
    """
    try:
        # Look up company_id from ticker
        company_list = get_company_list()
        company_id = None
        for company in company_list:
            if company.get("ticker") == ticker.upper():
                company_id = company.get("id")
                break

        if company_id is None:
            return {
                "error": f"Company not found for ticker: {ticker}",
                "ticker": ticker,
            }

        url = (
            f"https://www.vietcap.com.vn/api/cms-service/v2/page/analysis"
            f"?is-all=false&page={page}&size={size}&direction=DESC&sortBy=date"
            f"&companyId={company_id}&page-ids=144&page-ids=141&language=1"
        )
        content = _make_request("GET", url, headers=VIETCAP_HEADERS)

        data = content.get("data") if content else None
        paging_responses = data.get("pagingGeneralResponses") if data else None
        items = paging_responses.get("content") if paging_responses else None

        if items:
            results = []
            for item in items:
                if not item:
                    continue
                created_date = item.get("createdDate")
                link = item.get("link")
                results.append(
                    {
                        "title": item.get("name"),
                        "date": created_date.split("T")[0] if created_date else None,
                        "link": (
                            f"https://trading.vietcap.com.vn/iq/report-detail/vi/{link}"
                            if link
                            else None
                        ),
                    }
                )
            return results
        return {"error": "No data found", "ticker": ticker}
    except Exception as e:
        return {"error": str(e), "ticker": ticker}


# List of all tools for function calling
VIETCAP_TOOLS = [
    get_all_symbols,
    get_top_tickers,
    get_trending_news,
    get_coverage_universe,
    get_company_info,
    get_latest_ohlcv,
    get_ohlcv_by_day,
    get_technical_indicators,
    get_financial_ratios,
    get_short_financial,
    get_last_quarter_financial,
    get_price_earnings,
    get_annual_return,
    get_stock_news,
    get_company_news,
    get_company_events,
    get_stock_events,
    get_sector_comparison,
]
