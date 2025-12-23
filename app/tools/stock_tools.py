from typing import Dict, Any
import pandas as pd

def get_stock_price(symbol: str) -> Dict[str, Any]:
    """
    Retrieves the latest stock price for a given Vietnamese stock symbol.
    """
    try:
        from vnstock import Vnstock
        # Initialize vnstock inside the function to avoid top-level import hangs
        stock = Vnstock().stock
        df = stock.quote(symbol=symbol)
        if not df.empty:
            latest_row = df.iloc[0]
            return {
                "symbol": symbol,
                "price": latest_row.get("matchPrice", 0),
                "change": latest_row.get("change", 0),
                "percent_change": latest_row.get("percentChange", 0),
                "currency": "VND"
            }
        return {"error": f"No data found for symbol {symbol}"}
    except Exception as e:
        return {"error": str(e)}

def get_company_info(symbol: str) -> Dict[str, Any]:
    """
    Retrieves basic company information for a Vietnamese stock.
    """
    try:
        from vnstock import Vnstock
        # Initialize vnstock inside the function to avoid top-level import hangs
        stock = Vnstock().stock
        info = stock.profile(symbol=symbol)
        if not info.empty:
            row = info.iloc[0]
            return {
                "name": row.get("companyName"),
                "sector": row.get("sectorName"),
                "industry": row.get("industryName"),
                "summary": row.get("shortName")
            }
        return {"error": f"No profile found for symbol {symbol}"}
    except Exception as e:
        return {"error": str(e)}

def get_all_symbols() -> dict:
    """
    Retrieves all valid stock symbols from Vietnamese exchanges.
    Uses vnstock Listing class to get the complete list with exchange info.
    Returns a dictionary mapping symbol to {name, exchange}.
    """
    try:
        from vnstock import Listing
        listing = Listing()
        # Get all symbols with exchange info
        df = listing.symbols_by_exchange()
        if not df.empty and 'symbol' in df.columns:
            result = {}
            for _, row in df.iterrows():
                symbol = row.get('symbol', '')
                if symbol:
                    result[symbol] = {
                        'name': row.get('organ_name', 'N/A'),
                        'exchange': row.get('exchange', 'HOSE')  # Default to HOSE
                    }
            return result
        return {}
    except Exception as e:
        print(f"Error fetching symbols: {e}")
        return {}

def get_stock_ohlcv(symbol: str, start_date: str, end_date: str, interval: str = '1D') -> dict:
    """
    Fetches OHLCV (Open, High, Low, Close, Volume) data for a stock symbol.
    Uses vnstock VCI source for reliability.

    Args:
        symbol: Stock ticker symbol (e.g., 'VNM')
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        interval: Data interval ('1D' for daily, '1H' for hourly)

    Returns:
        Dict with 'data' array containing OHLCV records, or 'error' if failed
    """
    try:
        from vnstock import Vnstock
        stock = Vnstock().stock(symbol, 'VCI')
        df = stock.quote.history(start=start_date, end=end_date, interval=interval)

        if df.empty:
            return {"error": f"No data found for {symbol}"}

        # Convert to list of dicts for JSON serialization
        records = []
        for _, row in df.iterrows():
            # Add +07:00 timezone suffix for Vietnam time
            time_str = row['time'].isoformat() if hasattr(row['time'], 'isoformat') else str(row['time'])
            if '+' not in time_str and 'Z' not in time_str:
                time_str += '+07:00'
            records.append({
                "time": time_str,
                "open": float(row['open']),
                "high": float(row['high']),
                "low": float(row['low']),
                "close": float(row['close']),
                "volume": int(row['volume'])
            })

        return {"symbol": symbol, "interval": interval, "data": records}
    except Exception as e:
        print(f"Error fetching OHLCV for {symbol}: {e}")
        return {"error": str(e)}

def get_stock_news(symbol: str) -> dict:
    """
    Retrieves latest news for a specific stock symbol.
    Uses vnstock VCI source.
    Returns a list of news items (title, link, publishedDate, source).
    """
    try:
        from vnstock import Vnstock
        stock = Vnstock().stock(symbol=symbol, source='VCI')
        news_df = stock.company.news()

        if news_df.empty:
            return {"symbol": symbol, "news": []}

        news_items = []
        for _, row in news_df.iterrows():
            # Convert timestamp to date string (public_date is usually in ms)
            date_str = ""
            try:
                pub_date = row.get('public_date')
                if pub_date:
                    date_str = pd.to_datetime(pub_date, unit='ms').strftime('%Y-%m-%d')
            except Exception:
                pass # Keep empty if parsing fails

            # Extract source from link if possible
            link = row.get('news_source_link', '')
            source = "N/A"
            if link:
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(link).netloc
                    source = domain.replace('www.', '')
                except:
                    pass

            news_items.append({
                "title": row.get('news_title', ''),
                "link": link,
                "date": date_str,
                "source": source
            })

        return {"symbol": symbol, "news": news_items[:20]} # Limit to latest 20
    except Exception as e:
        print(f"Error fetching news for {symbol}: {e}")
        return {"error": str(e)}

# Tool mapping for the agent
STOCK_TOOLS = [
    get_stock_price,
    get_company_info
]
