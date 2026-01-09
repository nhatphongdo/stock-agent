"""
Technical Indicators utility module using pandas library.
"""

import pandas as pd
from typing import Optional
from datetime import datetime
from app.tools.vietcap_tools import (
    get_stock_ohlcv,
    get_company_info,
    get_annual_return,
)
from app.tools.indicator_calculation import calculate_indicators


def create_ohlcv_dataframe(ohlcv_data: list) -> pd.DataFrame:
    """
    Convert OHLCV list data to pandas DataFrame.

    Args:
        ohlcv_data: List of dicts with keys: time, open, high, low, close, volume

    Returns:
        DataFrame with datetime index and OHLCV columns
    """
    if not ohlcv_data:
        return pd.DataFrame()

    df = pd.DataFrame(ohlcv_data)
    df["time"] = pd.to_datetime(df["time"])
    df.set_index("time", inplace=True)
    df.columns = [c.lower() for c in df.columns]
    return df


def calculate_all_indicators(
    df: pd.DataFrame,
    timeframe: str = "short_term",
    config: "IndicatorConfig" = None,
) -> dict:
    """
    Calculate technical indicators used for analysis for a given DataFrame.

    Args:
        df: DataFrame with OHLCV data (columns: open, high, low, close, volume)
        timeframe: 'short_term' (daily) or 'long_term' (weekly)
        config: Optional IndicatorConfig instance with custom parameters

    Returns:
        Dictionary containing all calculated indicators
    """

    indicators = {}

    # ==========================================================================
    # Calculate indicators that not required series
    # ==========================================================================
    no_series_indicators = calculate_indicators(
        df,
        [
            "ma_20",
            "ma_50",
            "ma_100",
            "ma_200",
            "ema_20",
            "ema_50",
            "bb",
            "adx",
            "williams",
            "roc",
            "mom",
            "atr",
            "vol_sma_20",
            "cmf",
            "pivot",
            "fib",
            "vwap",
        ],
        None,
        False,
    )
    # Simple Moving Averages
    indicators["sma20"] = no_series_indicators.get("ma_20", {}).get("lastValue")
    indicators["sma50"] = no_series_indicators.get("ma_50", {}).get("lastValue")
    indicators["sma100"] = no_series_indicators.get("ma_100", {}).get("lastValue")
    indicators["sma200"] = no_series_indicators.get("ma_200", {}).get("lastValue")

    # Exponential Moving Averages
    indicators["ema20"] = no_series_indicators.get("ema_20", {}).get("lastValue")
    indicators["ema50"] = no_series_indicators.get("ema_50", {}).get("lastValue")

    # ADX - Average Directional Index (for trend strength)
    adx = no_series_indicators.get("adx", {}).get("lastValue", {})
    indicators["adx"] = {
        "adx": adx.get("adx"),
        "dmp": adx.get("plusDI"),
        "dmn": adx.get("minusDI"),
    }

    # Williams %R (14)
    indicators["willr"] = no_series_indicators.get("williams", {}).get("lastValue")

    # ROC - Rate of Change (10)
    indicators["roc"] = no_series_indicators.get("roc", {}).get("lastValue")

    # Momentum (10)
    indicators["momentum"] = no_series_indicators.get("mom", {}).get("lastValue")

    # Bollinger Bands (20, 2)
    bb = no_series_indicators.get("bb", {}).get("lastValue", {})
    indicators["bollinger_bands"] = {
        "lower": bb.get("lower"),
        "middle": bb.get("middle"),
        "upper": bb.get("upper"),
        "bandwidth": bb.get("bandwidth"),
        "percent_b": bb.get("percentage"),
    }

    # ATR - Average True Range (14)
    indicators["atr"] = no_series_indicators.get("atr", {}).get("lastValue")

    # Volume SMA (20)
    indicators["volume_sma20"] = no_series_indicators.get("vol_sma_20", {}).get(
        "lastValue"
    )

    # CMF - Chaikin Money Flow (20)
    indicators["cmf"] = no_series_indicators.get("cmf", {}).get("lastValue")

    # Classic Pivot Points
    indicators["pivot_points"] = no_series_indicators.get("pivot", {}).get("lastValue")

    # Fibonacci Retracement levels
    indicators["fibonacci"] = no_series_indicators.get("fib", {}).get("lastValue")

    # VWAP - Volume Weighted Average Price
    indicators["vwap"] = no_series_indicators.get("vwap", {}).get("lastValue")

    # ==========================================================================
    # Chart-required series data (for frontend visualization)
    # ==========================================================================
    series_indicators = calculate_indicators(
        df, ["rsi", "macd", "stoch", "obv"], None, True
    )
    # MACD (12, 26, 9)
    macd = series_indicators.get("macd", {})
    indicators["macd"] = {
        "line": macd.get("lastValue", {}).get("line"),
        "signal": macd.get("lastValue", {}).get("signal"),
        "histogram": macd.get("lastValue", {}).get("histogram"),
        "series": [
            {
                "time": datetime.fromtimestamp(item.get("time")).strftime("%Y-%m-%d"),
                "value": float(item.get("value")),
            }
            for item in macd.get("series", {}).get("line", [])[-100:]
        ],
    }
    # Stochastic Oscillator (14, 3, 3)
    stoch = series_indicators.get("stoch", {})
    indicators["stochastic"] = {
        "k": stoch.get("lastValue", {}).get("k"),
        "d": stoch.get("lastValue", {}).get("d"),
        "series": [
            {
                "time": datetime.fromtimestamp(item.get("time")).strftime("%Y-%m-%d"),
                "value": float(item.get("value")),
            }
            for item in stoch.get("series", {}).get("k", [])[-100:]
        ],
    }
    # RSI (14)
    rsi = series_indicators.get("rsi", {})
    indicators["rsi"] = {
        "value": rsi.get("lastValue"),
        "series": [
            {
                "time": datetime.fromtimestamp(item.get("time")).strftime("%Y-%m-%d"),
                "value": float(item.get("value")),
            }
            for item in rsi.get("series", {}).get("value", [])[-100:]
        ],
    }
    # OBV - On Balance Volume
    obv = series_indicators.get("obv", {})
    obv_series = obv.get("series", [])
    indicators["obv"] = obv.get("lastValue")
    # OBV change (last 5 periods)
    if obv_series is not None and len(obv_series) >= 5:
        obv_values = obv_series.dropna().tail(5).tolist()
        if len(obv_values) >= 2:
            indicators["obv_trend"] = (
                "increasing" if obv_values[-1] > obv_values[0] else "decreasing"
            )
        else:
            indicators["obv_trend"] = "neutral"
    else:
        indicators["obv_trend"] = "neutral"

    # Recent high/low
    indicators["recent_high"] = float(df["high"].max())
    indicators["recent_low"] = float(df["low"].min())

    # Current price info
    indicators["current_price"] = float(df["close"].iloc[-1])
    indicators["current_volume"] = float(df["volume"].iloc[-1])
    indicators["price_change"] = float(df["close"].iloc[-1] - df["close"].iloc[-2])
    indicators["price_change_pct"] = float(
        (df["close"].iloc[-1] - df["close"].iloc[-2]) / df["close"].iloc[-2] * 100
    )

    # Close series for divergence detection (last 10 values)
    indicators["close_series"] = df["close"].tail(10).tolist()

    # MA Position Analysis
    current_price = df["close"].iloc[-1]
    indicators["price_vs_sma20"] = _compare_price_to_ma(
        current_price, indicators.get("sma20")
    )
    indicators["price_vs_sma50"] = _compare_price_to_ma(
        current_price, indicators.get("sma50")
    )
    indicators["price_vs_sma200"] = _compare_price_to_ma(
        current_price, indicators.get("sma200")
    )

    return indicators


def _compare_price_to_ma(price: float, ma: Optional[float]) -> Optional[str]:
    """Compare current price to a moving average."""
    if ma is None:
        return None
    if price > ma:
        return "above"
    elif price < ma:
        return "below"
    return "at"


def detect_candlestick_patterns(df: pd.DataFrame) -> list[dict]:
    """
    Detect candlestick patterns from a DataFrame.

    Args:
        df: DataFrame with OHLCV data

    Returns:
        List of detected patterns
    """
    # Detect patterns
    # 'all' detects all patterns available in pandas-ta
    patterns = df.ta.cdl_pattern(name="all")

    if patterns is None or patterns.empty:
        return []

    detected_patterns = []

    # patterns DataFrame has columns like 'CDL_DOJI', 'CDL_HAMMER', etc.
    # Values are usually 100 (bullish) or -100 (bearish)
    for col in patterns.columns:
        # Filter rows where pattern is detected
        detected = patterns[patterns[col] != 0]

        for date, value in detected[col].items():
            pattern_name = col.replace("CDL_", "").replace("_", " ").title()
            signal = "bullish" if value > 0 else "bearish"

            # Find the candle data for this date
            if date in df.index:
                candle = df.loc[date]
                detected_patterns.append(
                    {
                        "name": pattern_name,
                        "date": date.strftime("%Y-%m-%d %H:%M:%S"),
                        "signal": signal,
                        "price": float(candle["close"]),
                        "description": f"{signal.capitalize()} {pattern_name} detected",
                    }
                )

    # Sort by date descending (newest first)
    detected_patterns.sort(key=lambda x: x["date"], reverse=True)
    return detected_patterns


def get_price_patterns(
    ticker: str,
    start_date: str,
    end_date: str,
    interval: str = "1D",
) -> dict:
    """
    Detect price action patterns using pandas-ta.

    Args:
        ticker: Stock ticker symbol
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        interval: 5m, 15m, 30m, 1H, 1D (default), 1W, 1M

    Returns:
        Dictionary containing detected patterns and their locations.
    """
    try:
        ohlcv_data = get_stock_ohlcv(
            symbol=ticker,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
        )

        if "error" in ohlcv_data:
            return ohlcv_data

        candles = ohlcv_data.get("data", [])
        if not candles:
            return {"error": "No data found", "ticker": ticker}

        # Convert to DataFrame
        df = create_ohlcv_dataframe(candles)

        # Detect patterns
        detected_patterns = detect_candlestick_patterns(df)

        return {"ticker": ticker, "patterns": detected_patterns}

    except Exception as e:
        return {"error": str(e), "ticker": ticker}
