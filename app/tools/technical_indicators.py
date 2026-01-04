"""
Technical Indicators utility module using pandas-ta library.
Provides wrapper functions for calculating technical indicators from OHLCV data.
"""

import pandas as pd
import pandas_ta as ta
from typing import Optional
from datetime import datetime
from dateutil.relativedelta import relativedelta
from app.tools.vietcap_tools import get_stock_ohlcv


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
) -> dict:
    """
    Calculate all technical indicators for a given DataFrame.

    Args:
        df: DataFrame with OHLCV data (columns: open, high, low, close, volume)
        timeframe: 'short_term' (daily) or 'long_term' (weekly)

    Returns:
        Dictionary containing all calculated indicators
    """
    if df.empty:
        return {}

    # Ensure we have the required columns
    required_cols = ["open", "high", "low", "close", "volume"]
    if not all(col in df.columns for col in required_cols):
        return {"error": "Missing required OHLCV columns"}

    indicators = {}

    # ==========================================================================
    # 1. TREND INDICATORS
    # ==========================================================================

    # Simple Moving Averages
    indicators["sma20"] = _get_last_value(ta.sma(df["close"], length=20))
    indicators["sma50"] = _get_last_value(ta.sma(df["close"], length=50))
    indicators["sma100"] = _get_last_value(ta.sma(df["close"], length=100))
    indicators["sma200"] = _get_last_value(ta.sma(df["close"], length=200))

    # Exponential Moving Averages
    indicators["ema20"] = _get_last_value(ta.ema(df["close"], length=20))
    indicators["ema50"] = _get_last_value(ta.ema(df["close"], length=50))

    # MACD (12, 26, 9)
    macd_result = ta.macd(df["close"], fast=12, slow=26, signal=9)
    if macd_result is not None and not macd_result.empty:
        indicators["macd"] = {
            "line": _get_last_value(macd_result.iloc[:, 0]),  # MACD line
            "signal": _get_last_value(macd_result.iloc[:, 1]),  # Signal line
            "histogram": _get_last_value(macd_result.iloc[:, 2]),  # Histogram
            "series": [
                {"time": t.strftime("%Y-%m-%d"), "value": float(v)}
                for t, v in macd_result.iloc[:, 0].dropna().tail(100).items()
            ],
        }
    else:
        indicators["macd"] = {
            "line": None,
            "signal": None,
            "histogram": None,
            "series": [],
        }

    # ADX - Average Directional Index (for trend strength)
    adx_result = ta.adx(df["high"], df["low"], df["close"], length=14)
    if adx_result is not None and not adx_result.empty:
        indicators["adx"] = {
            "adx": _get_last_value(adx_result.iloc[:, 0]),  # ADX
            "dmp": _get_last_value(adx_result.iloc[:, 1]),  # +DI
            "dmn": _get_last_value(adx_result.iloc[:, 2]),  # -DI
        }
    else:
        indicators["adx"] = {"adx": None, "dmp": None, "dmn": None}

    # ==========================================================================
    # 2. MOMENTUM INDICATORS
    # ==========================================================================

    # RSI (14)
    rsi_series = ta.rsi(df["close"], length=14)
    indicators["rsi"] = {
        "value": _get_last_value(rsi_series),
        "series": (
            [
                {"time": t.strftime("%Y-%m-%d"), "value": float(v)}
                for t, v in rsi_series.dropna().tail(100).items()
            ]
            if rsi_series is not None and not rsi_series.empty
            else []
        ),
    }

    # Stochastic Oscillator (14, 3, 3)
    stoch_result = ta.stoch(df["high"], df["low"], df["close"], k=14, d=3, smooth_k=3)
    if stoch_result is not None and not stoch_result.empty:
        indicators["stochastic"] = {
            "k": _get_last_value(stoch_result.iloc[:, 0]),  # %K
            "d": _get_last_value(stoch_result.iloc[:, 1]),  # %D
            "series": [
                {"time": t.strftime("%Y-%m-%d"), "value": float(v)}
                for t, v in stoch_result.iloc[:, 0].dropna().tail(100).items()
            ],
        }
    else:
        indicators["stochastic"] = {"k": None, "d": None, "series": []}

    # Williams %R (14)
    indicators["willr"] = _get_last_value(
        ta.willr(df["high"], df["low"], df["close"], length=14)
    )

    # ROC - Rate of Change (10)
    indicators["roc"] = _get_last_value(ta.roc(df["close"], length=10))

    # Momentum (10)
    indicators["momentum"] = _get_last_value(ta.mom(df["close"], length=10))

    # ==========================================================================
    # 3. VOLATILITY INDICATORS
    # ==========================================================================

    # Bollinger Bands (20, 2)
    bb_result = ta.bbands(df["close"], length=20, std=2)
    if bb_result is not None and not bb_result.empty:
        indicators["bollinger_bands"] = {
            "lower": _get_last_value(bb_result.iloc[:, 0]),
            "middle": _get_last_value(bb_result.iloc[:, 1]),
            "upper": _get_last_value(bb_result.iloc[:, 2]),
            "bandwidth": _get_last_value(bb_result.iloc[:, 3]),
            "percent_b": _get_last_value(bb_result.iloc[:, 4]),
        }
    else:
        indicators["bollinger_bands"] = {
            "lower": None,
            "middle": None,
            "upper": None,
            "bandwidth": None,
            "percent_b": None,
        }

    # ATR - Average True Range (14)
    indicators["atr"] = _get_last_value(
        ta.atr(df["high"], df["low"], df["close"], length=14)
    )

    # ==========================================================================
    # 4. VOLUME INDICATORS
    # ==========================================================================

    # Volume SMA (20)
    indicators["volume_sma20"] = _get_last_value(ta.sma(df["volume"], length=20))

    # OBV - On Balance Volume
    obv_series = ta.obv(df["close"], df["volume"])
    indicators["obv"] = _get_last_value(obv_series)

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

    # CMF - Chaikin Money Flow (20)
    indicators["cmf"] = _get_last_value(
        ta.cmf(df["high"], df["low"], df["close"], df["volume"], length=20)
    )

    # ==========================================================================
    # 5. SUPPORT / RESISTANCE
    # ==========================================================================

    # Classic Pivot Points
    pivot_points = calculate_pivot_points(
        high=df["high"].iloc[-1],
        low=df["low"].iloc[-1],
        close=df["close"].iloc[-1],
    )
    indicators["pivot_points"] = pivot_points

    # Fibonacci Retracement levels (based on recent high/low)
    lookback = 50 if timeframe == "short_term" else 100
    recent_high = df["high"].tail(lookback).max()
    recent_low = df["low"].tail(lookback).min()
    indicators["fibonacci"] = calculate_fibonacci_levels(recent_high, recent_low)

    # Recent high/low
    indicators["recent_high"] = recent_high
    indicators["recent_low"] = recent_low

    # Current price info
    indicators["current_price"] = df["close"].iloc[-1]
    indicators["price_change"] = df["close"].iloc[-1] - df["close"].iloc[-2]
    indicators["price_change_pct"] = (
        (df["close"].iloc[-1] - df["close"].iloc[-2]) / df["close"].iloc[-2] * 100
    )

    # MA Position Analysis
    current_price = df["close"].iloc[-1]
    indicators["price_vs_sma20"] = _compare_price_to_ma(
        current_price, indicators["sma20"]
    )
    indicators["price_vs_sma50"] = _compare_price_to_ma(
        current_price, indicators["sma50"]
    )
    indicators["price_vs_sma200"] = _compare_price_to_ma(
        current_price, indicators["sma200"]
    )

    return indicators


def calculate_pivot_points(high: float, low: float, close: float) -> dict:
    """
    Calculate Classic Pivot Points.

    Args:
        high: Previous period high
        low: Previous period low
        close: Previous period close

    Returns:
        Dictionary with pivot, support and resistance levels
    """
    pivot = (high + low + close) / 3
    r1 = 2 * pivot - low
    s1 = 2 * pivot - high
    r2 = pivot + (high - low)
    s2 = pivot - (high - low)
    r3 = high + 2 * (pivot - low)
    s3 = low - 2 * (high - pivot)

    return {
        "pivot": round(pivot, 2),
        "r1": round(r1, 2),
        "r2": round(r2, 2),
        "r3": round(r3, 2),
        "s1": round(s1, 2),
        "s2": round(s2, 2),
        "s3": round(s3, 2),
    }


def calculate_fibonacci_levels(high: float, low: float) -> dict:
    """
    Calculate Fibonacci Retracement levels.

    Args:
        high: Range high price
        low: Range low price

    Returns:
        Dictionary with Fibonacci retracement levels
    """
    diff = high - low
    return {
        "level_0": round(high, 2),
        "level_236": round(high - diff * 0.236, 2),
        "level_382": round(high - diff * 0.382, 2),
        "level_500": round(high - diff * 0.5, 2),
        "level_618": round(high - diff * 0.618, 2),
        "level_786": round(high - diff * 0.786, 2),
        "level_100": round(low, 2),
    }


def generate_method_evaluations(
    indicators: dict, timeframe: str = "short_term"
) -> list:
    """
    Generate detailed method evaluations based on calculated indicators.

    Args:
        indicators: Dictionary of calculated indicators
        timeframe: 'short_term' or 'long_term'

    Returns:
        List of method evaluation dictionaries
    """
    methods = []
    timeframe_label = "ngắn hạn (1D)" if timeframe == "short_term" else "dài hạn (1W)"

    # 1. RSI Analysis
    rsi_data = indicators.get("rsi", {})
    rsi = rsi_data.get("value")
    if rsi is not None:
        if rsi < 30:
            rsi_eval = (
                f"RSI = {rsi:.1f}, trong vùng quá bán (<30). Có thể là cơ hội mua vào."
            )
            rsi_signal = "Bullish"
        elif rsi > 70:
            rsi_eval = (
                f"RSI = {rsi:.1f}, trong vùng quá mua (>70). Có thể cân nhắc chốt lời."
            )
            rsi_signal = "Bearish"
        else:
            rsi_eval = f"RSI = {rsi:.1f}, trong vùng trung tính (30-70). Chưa có tín hiệu rõ ràng."
            rsi_signal = "Neutral"

        methods.append(
            {
                "name": "RSI Analysis",
                "category": "Momentum",
                "description": f"Phân tích chỉ số sức mạnh tương đối RSI(14) cho khung {timeframe_label}",
                "evaluation": rsi_eval,
                "signal": rsi_signal,
                "value": round(rsi, 2),
            }
        )

    # 2. MACD Analysis
    macd = indicators.get("macd", {})
    macd_line = macd.get("line")
    macd_signal = macd.get("signal")
    macd_hist = macd.get("histogram")

    if macd_line is not None and macd_signal is not None:
        if macd_line > macd_signal and macd_hist > 0:
            macd_eval = f"MACD ({macd_line:.2f}) > Signal ({macd_signal:.2f}), Histogram dương. Xu hướng tăng."
            macd_sig = "Bullish"
        elif macd_line < macd_signal and macd_hist < 0:
            macd_eval = f"MACD ({macd_line:.2f}) < Signal ({macd_signal:.2f}), Histogram âm. Xu hướng giảm."
            macd_sig = "Bearish"
        else:
            macd_eval = f"MACD = {macd_line:.2f}, Signal = {macd_signal:.2f}. Chờ xác nhận xu hướng."
            macd_sig = "Neutral"

        methods.append(
            {
                "name": "MACD Analysis",
                "category": "Trend",
                "description": f"Phân tích đường MACD(12,26,9) cho khung {timeframe_label}",
                "evaluation": macd_eval,
                "signal": macd_sig,
                "value": {"line": round(macd_line, 2), "signal": round(macd_signal, 2)},
            }
        )

    # 3. Moving Average Analysis
    current_price = indicators.get("current_price")
    sma20 = indicators.get("sma20")
    sma50 = indicators.get("sma50")
    sma200 = indicators.get("sma200")

    if current_price and sma20 and sma50:
        above_sma20 = current_price > sma20
        above_sma50 = current_price > sma50
        above_sma200 = current_price > sma200 if sma200 else None

        if above_sma20 and above_sma50:
            ma_eval = f"Giá ({current_price:,.0f}) > SMA20 ({sma20:,.0f}) > SMA50 ({sma50:,.0f}). Xu hướng tăng mạnh."
            ma_sig = "Bullish"
        elif not above_sma20 and not above_sma50:
            ma_eval = f"Giá ({current_price:,.0f}) < SMA20 ({sma20:,.0f}) < SMA50 ({sma50:,.0f}). Xu hướng giảm."
            ma_sig = "Bearish"
        else:
            ma_eval = (
                f"Giá ({current_price:,.0f}) đang ở giữa các đường MA. Vùng tích lũy."
            )
            ma_sig = "Neutral"

        methods.append(
            {
                "name": "Moving Average Analysis",
                "category": "Trend",
                "description": f"Phân tích vị trí giá so với các đường MA (SMA20, SMA50, SMA200) cho khung {timeframe_label}",
                "evaluation": ma_eval,
                "signal": ma_sig,
                "value": {"sma20": sma20, "sma50": sma50, "sma200": sma200},
            }
        )

    # 4. Bollinger Bands Analysis
    bb = indicators.get("bollinger_bands", {})
    bb_upper = bb.get("upper")
    bb_lower = bb.get("lower")
    bb_pct = bb.get("percent_b")

    if bb_upper and bb_lower and current_price:
        if current_price > bb_upper:
            bb_eval = f"Giá ({current_price:,.0f}) > BB Upper ({bb_upper:,.0f}). Có thể quá mua, cẩn thận breakout giả."
            bb_sig = "Bearish"
        elif current_price < bb_lower:
            bb_eval = f"Giá ({current_price:,.0f}) < BB Lower ({bb_lower:,.0f}). Có thể quá bán, theo dõi hỗ trợ."
            bb_sig = "Bullish"
        else:
            bb_eval = f"Giá nằm trong biên BB ({bb_lower:,.0f} - {bb_upper:,.0f}). Biến động bình thường."
            bb_sig = "Neutral"

        methods.append(
            {
                "name": "Bollinger Bands Analysis",
                "category": "Volatility",
                "description": f"Phân tích Bollinger Bands(20,2) cho khung {timeframe_label}",
                "evaluation": bb_eval,
                "signal": bb_sig,
                "value": {"upper": bb_upper, "lower": bb_lower},
            }
        )

    # 5. Stochastic Analysis
    stoch = indicators.get("stochastic", {})
    stoch_k = stoch.get("k")
    stoch_d = stoch.get("d")

    if stoch_k is not None:
        if stoch_k < 20:
            stoch_eval = (
                f"%K = {stoch_k:.1f}, trong vùng quá bán (<20). Tín hiệu mua tiềm năng."
            )
            stoch_sig = "Bullish"
        elif stoch_k > 80:
            stoch_eval = (
                f"%K = {stoch_k:.1f}, trong vùng quá mua (>80). Tín hiệu bán tiềm năng."
            )
            stoch_sig = "Bearish"
        else:
            stoch_eval = (
                f"%K = {stoch_k:.1f}, %D = {stoch_d:.1f}. Trong vùng trung tính."
            )
            stoch_sig = "Neutral"

        methods.append(
            {
                "name": "Stochastic Oscillator",
                "category": "Momentum",
                "description": f"Phân tích Stochastic(14,3,3) cho khung {timeframe_label}",
                "evaluation": stoch_eval,
                "signal": stoch_sig,
                "value": {"k": stoch_k, "d": stoch_d},
            }
        )

    # 6. ADX Analysis (Trend Strength)
    adx_data = indicators.get("adx", {})
    adx_val = adx_data.get("adx")
    dmp = adx_data.get("dmp")
    dmn = adx_data.get("dmn")

    if adx_val is not None:
        if adx_val > 25:
            if dmp and dmn and dmp > dmn:
                adx_eval = f"ADX = {adx_val:.1f} (>25), +DI > -DI. Xu hướng tăng mạnh."
                adx_sig = "Bullish"
            elif dmp and dmn and dmp < dmn:
                adx_eval = f"ADX = {adx_val:.1f} (>25), -DI > +DI. Xu hướng giảm mạnh."
                adx_sig = "Bearish"
            else:
                adx_eval = (
                    f"ADX = {adx_val:.1f} (>25). Xu hướng mạnh nhưng chưa rõ hướng."
                )
                adx_sig = "Neutral"
        else:
            adx_eval = f"ADX = {adx_val:.1f} (<25). Thị trường đi ngang, không có xu hướng rõ ràng."
            adx_sig = "Neutral"

        methods.append(
            {
                "name": "ADX Trend Strength",
                "category": "Trend",
                "description": f"Phân tích sức mạnh xu hướng ADX(14) cho khung {timeframe_label}",
                "evaluation": adx_eval,
                "signal": adx_sig,
                "value": adx_val,
            }
        )

    # 7. Volume Analysis
    volume_sma = indicators.get("volume_sma20")
    obv_trend = indicators.get("obv_trend")
    cmf = indicators.get("cmf")

    if obv_trend:
        if obv_trend == "increasing" and cmf and cmf > 0:
            vol_eval = f"OBV tăng, CMF = {cmf:.3f} (>0). Dòng tiền vào tích cực, hỗ trợ xu hướng tăng."
            vol_sig = "Bullish"
        elif obv_trend == "decreasing" and cmf and cmf < 0:
            vol_eval = f"OBV giảm, CMF = {cmf:.3f} (<0). Dòng tiền rút ra, cảnh báo xu hướng giảm."
            vol_sig = "Bearish"
        else:
            cmf_str = f"{cmf:.3f}" if cmf is not None else "N/A"
            vol_eval = f"OBV {obv_trend}, CMF = {cmf_str}. Khối lượng trung tính."
            vol_sig = "Neutral"

        methods.append(
            {
                "name": "Volume Analysis",
                "category": "Volume",
                "description": f"Phân tích khối lượng OBV và CMF(20) cho khung {timeframe_label}",
                "evaluation": vol_eval,
                "signal": vol_sig,
                "value": {"obv_trend": obv_trend, "cmf": cmf},
            }
        )

    # 8. Support/Resistance Analysis
    pivot = indicators.get("pivot_points", {})
    fib = indicators.get("fibonacci", {})

    if pivot and current_price:
        pivot_val = pivot.get("pivot")
        r1 = pivot.get("r1")
        s1 = pivot.get("s1")

        if current_price > pivot_val:
            sr_eval = f"Giá ({current_price:,.0f}) > Pivot ({pivot_val:,.0f}). Kháng cự gần nhất: R1 = {r1:,.0f}."
            sr_sig = "Bullish"
        else:
            sr_eval = f"Giá ({current_price:,.0f}) < Pivot ({pivot_val:,.0f}). Hỗ trợ gần nhất: S1 = {s1:,.0f}."
            sr_sig = "Bearish"

        methods.append(
            {
                "name": "Support/Resistance Analysis",
                "category": "Price Levels",
                "description": f"Phân tích mức Pivot và Fibonacci cho khung {timeframe_label}",
                "evaluation": sr_eval,
                "signal": sr_sig,
                "value": {"pivot": pivot_val, "fibonacci_618": fib.get("level_618")},
            }
        )

    return methods


def _get_last_value(series: Optional[pd.Series]) -> Optional[float]:
    """Get the last non-null value from a pandas Series."""
    if series is None or series.empty:
        return None
    last_val = series.dropna().iloc[-1] if not series.dropna().empty else None
    return round(float(last_val), 2) if last_val is not None else None


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
