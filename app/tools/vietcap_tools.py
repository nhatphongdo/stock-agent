"""
Vietcap API tools for stock data retrieval.
These functions are designed to be used with Google AI function calling.
"""
import requests
import time
from typing import Optional
from datetime import datetime, timedelta

# Common headers for Vietcap API
VIETCAP_HEADERS = {
    "Content-Type": "application/json",
    "Origin": "https://trading.vietcap.com.vn",
    "Referer": "https://trading.vietcap.com.vn/",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def get_company_info(ticker: str) -> dict:
    """
    Get basic company information for a stock ticker.

    Args:
        ticker: Stock ticker symbol (e.g., 'VNM', 'SSI', 'VND')

    Returns:
        Company information including name, sector, industry, and description
    """
    try:
        url = f"https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/{ticker}"
        response = requests.get(url, headers=VIETCAP_HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e), "ticker": ticker}


def get_ohlcv_data(ticker: str, count_back: int = 250, timeframe: str = "ONE_DAY") -> dict:
    """
    Get OHLCV (Open, High, Low, Close, Volume) price data for a stock.

    Args:
        ticker: Stock ticker symbol (e.g., 'VNM', 'SSI')
        count_back: Number of data points to retrieve (default 250)
        timeframe: Time interval - ONE_DAY, ONE_WEEK, ONE_MONTH

    Returns:
        Historical price data with timestamp, open, high, low, close, volume
    """
    try:
        url = "https://trading.vietcap.com.vn/api/chart/OHLCChart/gap-chart"
        payload = {
            "symbols": [ticker],
            "timeFrame": timeframe,
            "countBack": count_back,
            "to": int(time.time())
        }
        response = requests.post(url, json=payload, headers=VIETCAP_HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e), "ticker": ticker}


def get_technical_indicators(ticker: str, timeframe: str = "ONE_DAY") -> dict:
    """
    Get technical analysis indicators for a stock.

    Args:
        ticker: Stock ticker symbol
        timeframe: ONE_DAY or ONE_WEEK

    Returns:
        Technical indicators including RSI, MACD, moving averages, support/resistance levels
    """
    try:
        url = f"https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/{ticker}/technical/{timeframe}"
        response = requests.get(url, headers=VIETCAP_HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
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
        url = f"https://iq.vietcap.com.vn/api/iq-insight-service/v1/company-ratio-daily/{ticker}?lengthReport={length_report}"
        response = requests.get(url, headers=VIETCAP_HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
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
        response = requests.get(url, headers=VIETCAP_HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
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
        response = requests.get(url, headers=VIETCAP_HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e), "ticker": ticker}


def get_price_earnings(ticker: str) -> dict:
    """
    Get price and earnings data for a stock (revenue, profit trends).

    Args:
        ticker: Stock ticker symbol

    Returns:
        Historical price and earnings data
    """
    try:
        url = f"https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/{ticker}/price-earnings"
        response = requests.get(url, headers=VIETCAP_HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
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
        response = requests.get(url, headers=VIETCAP_HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e), "ticker": ticker}


def get_stock_news(ticker: str, from_date: Optional[str] = None, to_date: Optional[str] = None) -> dict:
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
        response = requests.get(url, headers=VIETCAP_HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e), "ticker": ticker}


def get_stock_events(ticker: str, from_date: Optional[str] = None, to_date: Optional[str] = None) -> dict:
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
        response = requests.get(url, headers=VIETCAP_HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
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
        response = requests.get(url, headers=VIETCAP_HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e), "ticker": ticker}


def get_all_symbols() -> dict:
    """
    Get all available stock symbols from Vietnamese exchanges.

    Returns:
        List of all stock symbols with basic info (ticker, name, exchange, sector)
    """
    try:
        url = "https://trading.vietcap.com.vn/api/price/symbols/getAll"
        response = requests.get(url, headers=VIETCAP_HEADERS, timeout=15)
        response.raise_for_status()
        return response.json()
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
        response = requests.get(url, headers=VIETCAP_HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
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
        response = requests.get(url, headers=VIETCAP_HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
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
        response = requests.get(url, headers=VIETCAP_HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


# List of all tools for function calling
VIETCAP_TOOLS = [
    get_all_symbols,
    get_top_tickers,
    get_trending_news,
    get_coverage_universe,
    get_company_info,
    get_ohlcv_data,
    get_technical_indicators,
    get_financial_ratios,
    get_short_financial,
    get_last_quarter_financial,
    get_price_earnings,
    get_annual_return,
    get_stock_news,
    get_stock_events,
    get_sector_comparison,
]
