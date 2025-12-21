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

# Tool mapping for the agent
STOCK_TOOLS = [
    get_stock_price,
    get_company_info
]
