"""
Technical Indicators utility module using pandas library.
"""

import pandas as pd
from typing import Optional
from datetime import datetime
from app.tools.vietcap_tools import get_stock_ohlcv
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
    indicators["price_change"] = float(df["close"].iloc[-1] - df["close"].iloc[-2])
    indicators["price_change_pct"] = float(
        (df["close"].iloc[-1] - df["close"].iloc[-2]) / df["close"].iloc[-2] * 100
    )

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
