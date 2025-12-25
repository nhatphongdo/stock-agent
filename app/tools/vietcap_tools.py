"""
Vietcap API tools for stock data retrieval.
These functions are designed to be used with Google AI function calling.
"""
import requests
import time
from typing import Optional
from datetime import datetime, timedelta
from urllib.parse import urlparse

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
        Structured company information for the trading agent
    """
    try:
        url = f"https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/{ticker}"
        response = requests.get(url, headers=VIETCAP_HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data and "data" in data:
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
            }
        return {"error": "No data found", "ticker": ticker}
    except Exception as e:
        return {"error": str(e), "ticker": ticker}


def get_ohlcv_data(ticker: str, count_back: int = 250, timeframe: str = "ONE_DAY", to_time: Optional[int] = None) -> dict:
    """
    Get OHLCV (Open, High, Low, Close, Volume) price data for a stock.

    Args:
        ticker: Stock ticker symbol (e.g., 'VNM', 'SSI')
        count_back: Number of data points to retrieve (default 250)
        timeframe: Time interval - ONE_MINUTE, ONE_HOUR, ONE_DAY
        to_time: Optional timestamp to get data up to

    Returns:
        Historical price data as a list of dictionaries
    """
    try:
        url = "https://trading.vietcap.com.vn/api/chart/OHLCChart/gap-chart"
        payload = {
            "symbols": [ticker],
            "timeFrame": timeframe,
            "countBack": count_back,
            "to": to_time if to_time else int(time.time())
        }
        response = requests.post(url, json=payload, headers=VIETCAP_HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data and isinstance(data, list) and len(data) > 0:
            stock_data = data[0]
            if "o" in stock_data:
                results = []
                for i in range(len(stock_data["o"])):
                    time_val = stock_data["t"][i] if i < len(stock_data["t"]) else 0
                    time_str = datetime.fromtimestamp(int(time_val)).strftime("%Y-%m-%d %H:%M:%S") if time_val else "N/A"
                    results.append({
                        "open": stock_data["o"][i] if i < len(stock_data["o"]) else None,
                        "high": stock_data["h"][i] if i < len(stock_data["h"]) else None,
                        "low": stock_data["l"][i] if i < len(stock_data["l"]) else None,
                        "close": stock_data["c"][i] if i < len(stock_data["c"]) else None,
                        "volume": stock_data["v"][i] if i < len(stock_data["v"]) else None,
                        "timestamp": time_str
                    })
                return {"ticker": ticker, "candles": results}
        return {"error": "No data found", "ticker": ticker}
    except Exception as e:
        return {"error": str(e), "ticker": ticker}


def get_latest_ohlcv(ticker: str) -> dict:
    """
    Get the latest OHLCV (Open, High, Low, Close, Volume) data for a stock.

    Args:
        ticker: Stock ticker symbol (e.g., 'VNM', 'SSI')

    Returns:
        Latest price data with open, high, low, close, volume and timestamp
    """
    result = get_ohlcv_data(ticker, count_back=1, timeframe="ONE_MINUTE")
    if "error" in result:
        return result
    if "candles" in result and len(result["candles"]) > 0:
        latest = result["candles"][-1]
        return {
            "ticker": ticker,
            "open": latest.get("open"),
            "high": latest.get("high"),
            "low": latest.get("low"),
            "close": latest.get("close"),
            "volume": latest.get("volume"),
            "timestamp": latest.get("timestamp"),
        }
    return {"error": "No data found", "ticker": ticker}


def get_ohlcv_by_day(ticker: str, days: int = 30) -> dict:
    """
    Get OHLCV data for multiple days, organized by date.

    Args:
        ticker: Stock ticker symbol (e.g., 'VNM', 'SSI')
        days: Number of days to retrieve (default 30)

    Returns:
        Dict with dates (YYYY-MM-DD) as keys and OHLCV data as values
    """
    result = get_ohlcv_data(ticker, count_back=days + (days // 7 + 1) * 2, timeframe="ONE_DAY") # Buffer days for weekends
    if "error" in result:
        return result
    if "candles" in result and len(result["candles"]) > 0:
        price_by_date = {}
        for candle in result["candles"]:
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
        response = requests.get(url, headers=VIETCAP_HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data and "data" in data:
            d = data["data"]

            # Extract all oscillators as dict
            oscillators = {osc.get("name", "").lower(): {"value": osc.get("value"), "rating": osc.get("rating")}
                          for osc in d.get("oscillators", []) if osc and osc.get("name")}

            # Extract all moving averages as dict
            moving_averages = {ma.get("name", "").lower(): {"value": ma.get("value"), "rating": ma.get("rating")}
                              for ma in d.get("movingAverages", []) if ma and ma.get("name")}

            return {
                "ticker": ticker,
                "timeframe": timeframe,
                "indicators": {
                    # Key oscillators
                    "rsi": round(oscillators.get("rsi", {}).get("value", 0), 2) if oscillators.get("rsi", {}).get("value") else None,
                    "macd": round(oscillators.get("macd", {}).get("value", 0), 2) if oscillators.get("macd", {}).get("value") else None,
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
                    "resistance1": round(d.get("pivot", {}).get("fibResistance1", 0), 2) if d.get("pivot", {}).get("fibResistance1") else None,
                    "resistance2": round(d.get("pivot", {}).get("fibResistance2", 0), 2) if d.get("pivot", {}).get("fibResistance2") else None,
                    "resistance3": round(d.get("pivot", {}).get("fibResistance3", 0), 2) if d.get("pivot", {}).get("fibResistance3") else None,
                    "support1": round(d.get("pivot", {}).get("fibSupport1", 0), 2) if d.get("pivot", {}).get("fibSupport1") else None,
                    "support2": round(d.get("pivot", {}).get("fibSupport2", 0), 2) if d.get("pivot", {}).get("fibSupport2") else None,
                    "support3": round(d.get("pivot", {}).get("fibSupport3", 0), 2) if d.get("pivot", {}).get("fibSupport3") else None,
                }
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
        response = requests.get(url, headers=VIETCAP_HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data and "data" in data:
            results = []
            # Calculate cutoff date based on length_report (days)
            cutoff_date = (datetime.now() - timedelta(days=length_report)).strftime("%Y-%m-%d")
            for r in data["data"]:
                trade_date = r.get("tradingDate", "").split("T")[0]
                # Filter by date
                if trade_date and trade_date >= cutoff_date:
                    results.append({
                        "date": trade_date,
                        "pe": round(r.get("pe"), 2) if r.get("pe") is not None else None,
                        "pb": round(r.get("pb"), 2) if r.get("pb") is not None else None,
                    })
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
        response = requests.get(url, headers=VIETCAP_HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data and "data" in data:
            results = []
            for r in data["data"]:
                results.append({
                    "period": r.get("quarter"),
                    "yearReport": r.get("yearReport"),
                    # Revenue & Profit
                    "revenue": r.get("revenue"),
                    "revenueGrowth": round(r.get("revenueGrowth", 0) * 100, 2) if r.get("revenueGrowth") else None,
                    "netProfit": r.get("npatMi"),
                    "netProfitGrowth": round(r.get("npatMiGrowth", 0) * 100, 2) if r.get("npatMiGrowth") else None,
                    # Margins
                    "grossMargin": round(r.get("grossMargin", 0) * 100, 2) if r.get("grossMargin") else None,
                    "netMargin": round(r.get("npatMiMargin", 0) * 100, 2) if r.get("npatMiMargin") else None,
                    # Efficiency
                    "eps": r.get("eps"),
                    "roe": round(r.get("roe", 0) * 100, 2) if r.get("roe") else None,
                    "roa": round(r.get("roa", 0) * 100, 2) if r.get("roa") else None,
                    # Balance sheet
                    "totalAsset": r.get("totalAsset"),
                    "totalEquity": r.get("totalEquity"),
                    "totalDebt": r.get("totalDebts"),
                    "cash": r.get("cash"),
                    "inventory": r.get("inventory"),
                    # Liquidity & Leverage
                    "currentRatio": round(r.get("currentRatio", 0), 2) if r.get("currentRatio") else None,
                    "quickRatio": round(r.get("quickRatio", 0), 2) if r.get("quickRatio") else None,
                    "debtEquity": round(r.get("debtPerEquity", 0), 2) if r.get("debtPerEquity") else None,
                })
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
        response = requests.get(url, headers=VIETCAP_HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

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
        response = requests.get(url, headers=VIETCAP_HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data and "data" in data and isinstance(data["data"], list):
            results = []
            for r in data["data"]:
                results.append({
                    "date": (r.get("publicDate") or "").split("T")[0],
                    "npatMi": r.get("npatMi"),
                })
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
        response = requests.get(url, headers=VIETCAP_HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data and "data" in data:
            results = []
            for r in data["data"]:
                results.append({
                    "year": r.get("year"),
                    "stockReturn": round(r.get("stockReturn", 0) * 100, 2) if r.get("stockReturn") else None,
                    "vnIndex": round(r.get("vnIndex", 0) * 100, 2) if r.get("vnIndex") else None,
                    "outperformance": round(r.get("annualOutperformanceVNIndex", 0) * 100, 2) if r.get("annualOutperformanceVNIndex") else None,
                })
            return {"ticker": ticker, "returns": results}
        return {"error": "No data found", "ticker": ticker}
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
        data = response.json()

        if data and "data" in data and "content" in data["data"]:
            results = []
            for n in data["data"]["content"]:
                results.append({
                    "title": n.get("newsTitle"),
                    "date": n.get("publicDate", "").split("T")[0],
                    "link": "",
                    "source": "Vietcap",
                })
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
        payload = {
            "query": query,
            "variables": {"ticker": ticker, "lang": lang}
        }

        response = requests.post(url, json=payload, headers=VIETCAP_HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

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

                result["news"].append({
                    "title": n.get("newsTitle"),
                    "date": parse_date(n.get("publicDate")),
                    "description": n.get("newsShortContent"),
                    "link": link,
                    "source": source,
                })

        return result
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
        data = response.json()

        if data and "data" in data and "content" in data["data"]:
            results = []
            for e in data["data"]["content"]:
                results.append({
                    "ticker": e.get("ticker"),
                    "event": e.get("eventCode"),
                    "title": e.get("titleVi"),
                    "date": e.get("publishDate", "").split("T")[0],
                    "exDividendDate": e.get("exDividendDate", "").split("T")[0] if e.get("exDividendDate") else None,
                })
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
        response = requests.get(url, headers=VIETCAP_HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data and "data" in data:
            results = []
            for p in data["data"]:
                results.append({
                    "ticker": p.get("ticker"),
                    "name": p.get("viOrganName"),
                    "return1M": round(p.get("stockReturn1M", 0) * 100, 2) if p.get("stockReturn1M") else None,
                    "return3M": round(p.get("stockReturn3M", 0) * 100, 2) if p.get("stockReturn3M") else None,
                    "return1Y": round(p.get("stockReturn1Y", 0) * 100, 2) if p.get("stockReturn1Y") else None,
                    "rating": p.get("rating"),
                })
            return {"ticker": ticker, "peers": results}
        return {"error": "No data found", "ticker": ticker}
    except Exception as e:
        return {"error": str(e), "ticker": ticker}


def get_all_symbols() -> dict:
    """
    Get all available stock symbols from Vietnamese exchanges.

    Returns:
        Dictionary mapping symbols to {name, exchange}
    """
    try:
        url = "https://trading.vietcap.com.vn/api/price/symbols/getAll"
        response = requests.get(url, headers=VIETCAP_HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()

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
        response = requests.get(url, headers=VIETCAP_HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data and "ticker_info" in data:
            return [{
                "ticker": t.get("ticker"),
                "name": t.get("organ_name"),
                "sentiment": t.get("sentiment"),
                "score": t.get("score"),
            } for t in data["ticker_info"]]
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
        response = requests.get(url, headers=VIETCAP_HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data and "data" in data:
            def format_datetime(iso_date):
                try:
                    if iso_date:
                        dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
                        return dt.strftime("%d/%m/%Y %H:%M")
                except:
                    pass
                return iso_date or "N/A"

            return [{
                "title": r.get("name"),
                "ticker": r.get("ticker"),
                "date": format_datetime(r.get("date")),
                "detail": r.get("detail"),
            } for r in data["data"] if r.get("name")]
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
        response = requests.get(url, headers=VIETCAP_HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data and "data" in data:
            results = []
            for c in data["data"]:
                results.append({
                    "ticker": c.get("ticker"),
                    "rating": c.get("rating"),
                    "targetPrice": c.get("targetPrice"),
                    "upside": round(c.get("upside", 0) * 100, 2) if c.get("upside") else None,
                    "analyst": c.get("analyst"),
                })
            return results
        return []
    except Exception as e:
        return {"error": str(e)}


def get_stock_ohlcv(symbol: str, start_date: str, end_date: str, interval: str = '1D') -> dict:
    """
    Fetches OHLCV data for a stock ticker within a date range.
    Equivalent to stock_tools.get_stock_ohlcv.
    """
    import pandas as pd
    # Map interval to vietcap timeframe
    tf_map = {
        '5m': 'ONE_MINUTE',
        '15m': 'ONE_MINUTE',
        '30m': 'ONE_MINUTE',
        '1H': 'ONE_HOUR',
        '1D': 'ONE_DAY',
        '1W': 'ONE_DAY',
        '1M': 'ONE_DAY',
    }
    timeframe = tf_map.get(interval, 'ONE_DAY')

    # Calculate count_back based on start_date to end_date (or now)
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else datetime.now()

        business_days = len(pd.bdate_range(start=start_dt, end=end_dt))
        business_days += (business_days // 260 + 1) * 20 # Buffer holidays, 20 days / year, 260 weekdays / year
        if timeframe == 'ONE_DAY':
            # Exact trading days count (excluding weekends)
            count_back = business_days + 1
        elif timeframe == 'ONE_HOUR':
            # Days * 6.5 trading hours per day
            count_back = int((business_days * 6.5) + 1)
        elif timeframe == 'ONE_MINUTE':
            # Days * 6.5 trading hours per day * 60 minutes per hour
            count_back = int((business_days * 6.5 * 60) + 1)
        else:
            count_back = 1000 # Default fallback

    except Exception as e:
        count_back = 1000

    result = get_ohlcv_data(symbol, count_back=count_back, timeframe=timeframe, to_time=int(end_dt.timestamp()))
    if "error" in result:
        return result

    candles = result.get("candles", [])
    if not candles:
        return {"symbol": symbol, "interval": interval, "data": []}

    # Convert to DataFrame for easier manipulation and resampling
    df = pd.DataFrame(candles)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)

    # Filter by date range before resampling
    df = df[(df.index >= start_dt) & (df.index <= end_dt + timedelta(days=1))]

    # Map interval to pandas frequency for resampling
    agg_map = {
        '5m': '5min',
        '15m': '15min',
        '30m': '30min',
        '1H': '1H',
        '1D': '1D',
        '1W': 'W-MON',
        '1M': 'ME',
    }

    freq = agg_map.get(interval)

    if freq and freq != timeframe:
        # Resample data if the interval is different from the base timeframe fetched
        resampled = df.resample(freq, closed='left', label='left').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        df = resampled

    # Convert back to the expected list of dictionaries
    filtered_data = []
    for ts, row in df.iterrows():
        dt_str = ts.strftime("%Y-%m-%d %H:%M:%S")
        # Final filter check (safety)
        if start_date <= dt_str.split(" ")[0] <= (end_date or "9999-12-31"):
            filtered_data.append({
                "time": dt_str,
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": int(row["volume"]),
            })

    return {"symbol": symbol, "interval": interval, "data": filtered_data}

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
    get_stock_events,
    get_sector_comparison,
]
