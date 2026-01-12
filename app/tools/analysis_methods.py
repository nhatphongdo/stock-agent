"""
Analysis Methods module - Contains strategy evaluation functions for technical analysis.
Refactored from technical_indicators.py for cleaner separation of concerns.
"""

from typing import Optional
from app.tools.vietcap_tools import get_company_info, get_annual_return


# =============================================================================
# SIGNAL DETECTION CONSTANTS
# =============================================================================

# RSI Thresholds
RSI_OVERSOLD = 30  # RSI below this level indicates oversold condition
RSI_OVERBOUGHT = 70  # RSI above this level indicates overbought condition
RSI_NEUTRAL = 50  # RSI neutral level for confluence signals

# Stochastic Oscillator Thresholds
STOCH_OVERSOLD = 20  # %K below this level indicates oversold condition
STOCH_OVERBOUGHT = 80  # %K above this level indicates overbought condition

# ADX Trend Strength Threshold
ADX_TREND_STRENGTH = 25  # ADX above this indicates a strong trend

# Volume Analysis
VOLUME_SPIKE_MULTIPLIER = 1.5  # Volume > avg * this = significant spike

# Bollinger Bands Squeeze
# Bandwidth is in percentage scale (typically 10-50%)
# A squeeze is indicated by bandwidth < this threshold
BB_SQUEEZE_THRESHOLD = 6.0

# RSI Divergence Detection
DIVERGENCE_WINDOW = 5  # Look for peaks/troughs within this many bars
DIVERGENCE_MIN_BARS = 20  # Minimum bars required for divergence analysis

# OBV Trend Detection
OBV_LOOKBACK = 5  # Periods to analyze OBV trend


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================


def generate_method_evaluations(
    indicators: dict, timeframe: str = None, ticker: str = None
) -> list:
    """
    Generate detailed method evaluations based on calculated indicators.

    Args:
        indicators: Dictionary of calculated indicators
        timeframe: Optional 'short_term' or 'long_term' (for Analysis chart only)
        ticker: Optional stock ticker for API-based strategies

    Returns:
        List of method evaluation dictionaries with keys:
        - id: Unique identifier for the method
        - name: Strategy name
        - category: Strategy category (Momentum, Trend, Volume, etc.)
        - description: Detailed explanation of the strategy and its impact
        - evaluation: Current market condition based on indicators
        - signal: Bullish, Bearish, or Neutral
        - confidence: Confidence level (High, Medium, Low)
        - value: Indicator values used
    """
    methods = []
    # Only show timeframe label if specified (for Analysis chart)
    if timeframe:
        timeframe_label = (
            "ngắn hạn (1Y theo ngày)"
            if timeframe == "short_term"
            else "dài hạn (5Y theo ngày)"
        )
    else:
        timeframe_label = ""  # Empty for main chart

    # Basic strategies
    _add_if_valid(methods, _eval_rsi(indicators, timeframe_label))
    _add_if_valid(methods, _eval_macd(indicators, timeframe_label))
    _add_if_valid(methods, _eval_moving_average(indicators, timeframe_label))
    _add_if_valid(methods, _eval_bollinger_bands(indicators, timeframe_label))
    _add_if_valid(methods, _eval_stochastic(indicators, timeframe_label))
    _add_if_valid(methods, _eval_adx(indicators, timeframe_label))
    _add_if_valid(methods, _eval_volume(indicators, timeframe_label))
    _add_if_valid(methods, _eval_support_resistance(indicators, timeframe_label))

    # Advanced strategies
    _add_if_valid(methods, _eval_golden_death_cross(indicators, timeframe_label))
    _add_if_valid(methods, _eval_rsi_divergence(indicators, timeframe_label))
    _add_if_valid(methods, _eval_volume_breakout(indicators, timeframe_label))
    _add_if_valid(methods, _eval_macd_rsi_confluence(indicators, timeframe_label))
    _add_if_valid(methods, _eval_bb_squeeze(indicators, timeframe_label))
    _add_if_valid(methods, _eval_vwap(indicators, timeframe_label))

    # API-based strategies (require ticker)
    if ticker:
        _add_if_valid(methods, _eval_52_week_proximity(indicators, ticker))
        _add_if_valid(methods, _eval_relative_strength_vnindex(ticker))

    return methods


def get_available_analysis_methods() -> list:
    """
    Returns list of all available analysis method definitions (without calculated values).
    Used for populating dropdown UI.
    """
    return [
        {
            "id": "rsi",
            "name": "RSI Analysis",
            "category": "Momentum",
            "description": "RSI đo lường tốc độ và mức độ thay đổi giá. RSI < 30 = quá bán, > 70 = quá mua.",
        },
        {
            "id": "macd",
            "name": "MACD Analysis",
            "category": "Trend",
            "description": "MACD xác định xu hướng và momentum. MACD cắt lên Signal = mua, cắt xuống = bán.",
        },
        {
            "id": "moving_average",
            "name": "Moving Average Analysis",
            "category": "Trend",
            "description": "Phân tích vị trí giá so với các đường MA ngắn, trung và dài hạn.",
        },
        {
            "id": "bollinger_bands",
            "name": "Bollinger Bands Analysis",
            "category": "Volatility",
            "description": "Đo lường biến động giá. Giá chạm upper band = quá mua, lower band = quá bán.",
        },
        {
            "id": "stochastic",
            "name": "Stochastic Oscillator",
            "category": "Momentum",
            "description": "So sánh giá đóng cửa với phạm vi giá. K < 20 = quá bán, K > 80 = quá mua.",
        },
        {
            "id": "adx",
            "name": "ADX Trend Strength",
            "category": "Trend",
            "description": "Đo sức mạnh xu hướng. ADX > 25 = xu hướng mạnh, < 25 = đi ngang.",
        },
        {
            "id": "volume",
            "name": "Volume Analysis",
            "category": "Volume",
            "description": "OBV và CMF đo dòng tiền. OBV tăng + CMF > 0 = tích lũy.",
        },
        {
            "id": "support_resistance",
            "name": "Support/Resistance Analysis",
            "category": "Price Levels",
            "description": "Pivot Points và Fibonacci xác định vùng hỗ trợ/kháng cự.",
        },
        {
            "id": "golden_death_cross",
            "name": "Golden Cross / Death Cross",
            "category": "Trend",
            "description": "SMA50 cắt lên SMA200 = Golden Cross (tăng), cắt xuống = Death Cross (giảm).",
        },
        {
            "id": "rsi_divergence",
            "name": "RSI Divergence",
            "category": "Momentum",
            "description": "Phân kỳ RSI là tín hiệu đảo chiều mạnh. Giá giảm + RSI tăng = mua.",
        },
        {
            "id": "volume_breakout",
            "name": "Volume Breakout",
            "category": "Volume",
            "description": "Khối lượng cao (>1.5x TB) xác nhận breakout. Volume spike + giá tăng = mua.",
        },
        {
            "id": "macd_rsi_confluence",
            "name": "MACD + RSI Confluence",
            "category": "Multi-Indicator",
            "description": "Kết hợp MACD và RSI cho tín hiệu mạnh hơn, giảm false signals.",
        },
        {
            "id": "bb_squeeze",
            "name": "Bollinger Band Squeeze",
            "category": "Volatility",
            "description": "Bandwidth thu hẹp (<10%) báo hiệu breakout sắp xảy ra.",
        },
        {
            "id": "vwap",
            "name": "VWAP Strategy",
            "category": "Volume",
            "description": "VWAP là giá trung bình có trọng số. Giá > VWAP = bên mua đang kiểm soát.",
        },
        {
            "id": "52_week_proximity",
            "name": "52-Week High/Low Proximity",
            "category": "Price Levels",
            "description": "Giá gần 52W High = momentum mạnh, gần 52W Low = có thể đảo chiều.",
        },
        {
            "id": "relative_strength_vnindex",
            "name": "Relative Strength vs VN-Index",
            "category": "Performance",
            "description": "So sánh hiệu suất cổ phiếu với VN-Index để đánh giá alpha.",
        },
    ]


def _add_if_valid(methods: list, result: dict) -> None:
    """Add evaluation result to methods list if valid."""
    if result:
        methods.append(result)


def generate_signal_points(df, method_id: str) -> list:
    """
    Scan DataFrame for signal points where a method triggers.
    Returns list of { time, type, price, direction } dicts for marker rendering.

    Args:
        df: DataFrame with OHLCV and indicator data
        method_id: The analysis method ID

    Returns:
        List of signal point dictionaries
    """
    import pandas as pd
    from app.tools.indicator_calculation import calculate_indicators

    signals = []

    if df is None or df.empty:
        return signals

    try:
        # Calculate required indicators based on method
        if method_id == "rsi":
            indicators = calculate_indicators(df, ["rsi"], series_included=True)
            rsi_series = indicators.get("rsi", {}).get("series", {}).get("value", [])
            if rsi_series:
                # Find RSI crossings of 30 (oversold) and 70 (overbought)
                for i in range(1, len(rsi_series)):
                    curr = rsi_series[i]
                    prev = rsi_series[i - 1]
                    if prev["value"] is None or curr["value"] is None:
                        continue
                    # Crossing below 30 (entering oversold)
                    if prev["value"] >= RSI_OVERSOLD and curr["value"] < RSI_OVERSOLD:
                        signals.append(
                            {
                                "time": curr["time"],
                                "type": "Quá bán",
                                "price": float(df.iloc[i]["close"]),
                                "direction": "up",
                            }
                        )
                    # Crossing above 70 (entering overbought)
                    elif (
                        prev["value"] <= RSI_OVERBOUGHT
                        and curr["value"] > RSI_OVERBOUGHT
                    ):
                        signals.append(
                            {
                                "time": curr["time"],
                                "type": "Quá mua",
                                "price": float(df.iloc[i]["close"]),
                                "direction": "down",
                            }
                        )
                    # RSI crossing above 30 (exiting oversold - buy signal)
                    elif prev["value"] < RSI_OVERSOLD and curr["value"] >= RSI_OVERSOLD:
                        signals.append(
                            {
                                "time": curr["time"],
                                "type": "Thoát quá bán",
                                "price": float(df.iloc[i]["close"]),
                                "direction": "up",
                            }
                        )
                    # RSI crossing below 70 (exiting overbought - sell signal)
                    elif (
                        prev["value"] > RSI_OVERBOUGHT
                        and curr["value"] <= RSI_OVERBOUGHT
                    ):
                        signals.append(
                            {
                                "time": curr["time"],
                                "type": "Thoát quá mua",
                                "price": float(df.iloc[i]["close"]),
                                "direction": "down",
                            }
                        )

        elif method_id == "macd":
            indicators = calculate_indicators(df, ["macd"], series_included=True)
            macd_data = indicators.get("macd", {}).get("series", {})
            line_series = macd_data.get("line", [])
            signal_series = macd_data.get("signal", [])
            if line_series and signal_series and len(line_series) == len(signal_series):
                for i in range(1, len(line_series)):
                    curr_line = line_series[i]["value"]
                    prev_line = line_series[i - 1]["value"]
                    curr_sig = signal_series[i]["value"]
                    prev_sig = signal_series[i - 1]["value"]
                    if None in [curr_line, prev_line, curr_sig, prev_sig]:
                        continue
                    # Bullish crossover (MACD crosses above Signal)
                    if prev_line <= prev_sig and curr_line > curr_sig:
                        signals.append(
                            {
                                "time": line_series[i]["time"],
                                "type": "Cắt lên",
                                "price": float(df.iloc[i]["close"]),
                                "direction": "up",
                            }
                        )
                    # Bearish crossover (MACD crosses below Signal)
                    elif prev_line >= prev_sig and curr_line < curr_sig:
                        signals.append(
                            {
                                "time": line_series[i]["time"],
                                "type": "Cắt xuống",
                                "price": float(df.iloc[i]["close"]),
                                "direction": "down",
                            }
                        )

        elif method_id == "golden_death_cross":
            indicators = calculate_indicators(
                df, ["ma_50", "ma_200"], series_included=True
            )
            ma50_series = indicators.get("ma_50", {}).get("series", {}).get("value", [])
            ma200_series = (
                indicators.get("ma_200", {}).get("series", {}).get("value", [])
            )

            # SMA200 will be shorter than SMA50 (requires more data points)
            # Align from the end (most recent data)
            if ma50_series and ma200_series:
                len_50 = len(ma50_series)
                len_200 = len(ma200_series)
                # Offset for SMA50 to align with SMA200
                offset = len_50 - len_200

                for i in range(1, len_200):
                    idx_50 = i + offset
                    curr_50 = ma50_series[idx_50]["value"]
                    prev_50 = ma50_series[idx_50 - 1]["value"]
                    curr_200 = ma200_series[i]["value"]
                    prev_200 = ma200_series[i - 1]["value"]
                    if None in [curr_50, prev_50, curr_200, prev_200]:
                        continue
                    # Golden Cross (SMA50 crosses above SMA200)
                    if prev_50 <= prev_200 and curr_50 > curr_200:
                        signals.append(
                            {
                                "time": ma200_series[i]["time"],
                                "type": "Golden Cross",
                                "price": float(df.iloc[i + offset]["close"]),
                                "direction": "up",
                            }
                        )
                    # Death Cross (SMA50 crosses below SMA200)
                    elif prev_50 >= prev_200 and curr_50 < curr_200:
                        signals.append(
                            {
                                "time": ma200_series[i]["time"],
                                "type": "Death Cross",
                                "price": float(df.iloc[i + offset]["close"]),
                                "direction": "down",
                            }
                        )

        elif method_id == "volume_breakout":
            indicators = calculate_indicators(df, ["vol_sma_20"], series_included=True)
            vol_sma = (
                indicators.get("vol_sma_20", {}).get("series", {}).get("value", [])
            )

            # vol_sma series will be shorter than df (requires lookback period)
            if vol_sma:
                offset = len(df) - len(vol_sma)
                for i in range(len(vol_sma)):
                    sma_val = vol_sma[i]["value"]
                    if sma_val is None:
                        continue
                    df_idx = i + offset
                    current_vol = df.iloc[df_idx]["volume"]
                    current_close = df.iloc[df_idx]["close"]
                    prev_close = (
                        df.iloc[df_idx - 1]["close"] if df_idx > 0 else current_close
                    )
                    # Volume spike (> VOLUME_SPIKE_MULTIPLIER x average) with price movement
                    if current_vol > sma_val * VOLUME_SPIKE_MULTIPLIER:
                        direction = "up" if current_close > prev_close else "down"
                        signals.append(
                            {
                                "time": vol_sma[i]["time"],
                                "type": "KL đột biến",
                                "price": float(current_close),
                                "direction": direction,
                            }
                        )

        elif method_id == "rsi_divergence":
            indicators = calculate_indicators(df, ["rsi"], series_included=True)
            rsi_series = indicators.get("rsi", {}).get("series", {}).get("value", [])

            if rsi_series and len(rsi_series) >= DIVERGENCE_MIN_BARS:
                offset = len(df) - len(rsi_series)

                # Find local highs and lows using a simple window approach
                window = DIVERGENCE_WINDOW  # Look for peaks/troughs within n bars

                def find_local_extremes(data, is_high=True):
                    """Find local highs or lows in data."""
                    extremes = []
                    for i in range(window, len(data) - window):
                        val = data[i]
                        if val is None:
                            continue
                        window_vals = [
                            data[j]
                            for j in range(i - window, i + window + 1)
                            if data[j] is not None
                        ]
                        if not window_vals:
                            continue
                        if is_high and val == max(window_vals):
                            extremes.append((i, val))
                        elif not is_high and val == min(window_vals):
                            extremes.append((i, val))
                    return extremes

                # Extract price and RSI values
                prices = [
                    df.iloc[i + offset]["high"] if i + offset < len(df) else None
                    for i in range(len(rsi_series))
                ]
                price_lows = [
                    df.iloc[i + offset]["low"] if i + offset < len(df) else None
                    for i in range(len(rsi_series))
                ]
                rsi_vals = [r["value"] for r in rsi_series]

                # Find highs and lows
                price_highs = find_local_extremes(prices, is_high=True)
                price_low_pts = find_local_extremes(price_lows, is_high=False)
                rsi_highs = find_local_extremes(rsi_vals, is_high=True)
                rsi_lows = find_local_extremes(rsi_vals, is_high=False)

                # Detect bearish divergence: price higher high + RSI lower high
                for i in range(1, min(len(price_highs), len(rsi_highs))):
                    prev_ph, curr_ph = price_highs[i - 1], price_highs[i]
                    prev_rh, curr_rh = rsi_highs[i - 1], rsi_highs[i]

                    # Price made higher high, RSI made lower high
                    if curr_ph[1] > prev_ph[1] and curr_rh[1] < prev_rh[1]:
                        signals.append(
                            {
                                "time": rsi_series[curr_ph[0]]["time"],
                                "type": "Phân kỳ giảm",
                                "price": float(curr_ph[1]),
                                "direction": "down",
                                "trendline": {
                                    "price": [
                                        {
                                            "time": rsi_series[prev_ph[0]]["time"],
                                            "value": float(prev_ph[1]),
                                        },
                                        {
                                            "time": rsi_series[curr_ph[0]]["time"],
                                            "value": float(curr_ph[1]),
                                        },
                                    ],
                                    "rsi": [
                                        {
                                            "time": rsi_series[prev_rh[0]]["time"],
                                            "value": float(prev_rh[1]),
                                        },
                                        {
                                            "time": rsi_series[curr_rh[0]]["time"],
                                            "value": float(curr_rh[1]),
                                        },
                                    ],
                                },
                            }
                        )

                # Detect bullish divergence: price lower low + RSI higher low
                for i in range(1, min(len(price_low_pts), len(rsi_lows))):
                    prev_pl, curr_pl = price_low_pts[i - 1], price_low_pts[i]
                    prev_rl, curr_rl = rsi_lows[i - 1], rsi_lows[i]

                    # Price made lower low, RSI made higher low
                    if curr_pl[1] < prev_pl[1] and curr_rl[1] > prev_rl[1]:
                        signals.append(
                            {
                                "time": rsi_series[curr_pl[0]]["time"],
                                "type": "Phân kỳ tăng",
                                "price": float(curr_pl[1]),
                                "direction": "up",
                                "trendline": {
                                    "price": [
                                        {
                                            "time": rsi_series[prev_pl[0]]["time"],
                                            "value": float(prev_pl[1]),
                                        },
                                        {
                                            "time": rsi_series[curr_pl[0]]["time"],
                                            "value": float(curr_pl[1]),
                                        },
                                    ],
                                    "rsi": [
                                        {
                                            "time": rsi_series[prev_rl[0]]["time"],
                                            "value": float(prev_rl[1]),
                                        },
                                        {
                                            "time": rsi_series[curr_rl[0]]["time"],
                                            "value": float(curr_rl[1]),
                                        },
                                    ],
                                },
                            }
                        )

        elif method_id == "bollinger_bands":
            indicators = calculate_indicators(df, ["bb"], series_included=True)
            bb_data = indicators.get("bb", {}).get("series", {})
            upper = bb_data.get("upper", [])
            lower = bb_data.get("lower", [])

            if upper and lower:
                offset = len(df) - len(upper)
                for i in range(len(upper)):
                    if upper[i]["value"] is None or lower[i]["value"] is None:
                        continue
                    df_idx = i + offset
                    if df_idx < 0 or df_idx >= len(df):
                        continue
                    close = df.iloc[df_idx]["close"]
                    high = df.iloc[df_idx]["high"]
                    low = df.iloc[df_idx]["low"]

                    # Touch upper band (overbought)
                    if high >= upper[i]["value"]:
                        signals.append(
                            {
                                "time": upper[i]["time"],
                                "type": "Chạm Upper Band",
                                "price": float(high),
                                "direction": "down",
                            }
                        )
                    # Touch lower band (oversold)
                    elif low <= lower[i]["value"]:
                        signals.append(
                            {
                                "time": lower[i]["time"],
                                "type": "Chạm Lower Band",
                                "price": float(low),
                                "direction": "up",
                            }
                        )

        elif method_id == "stochastic":
            indicators = calculate_indicators(df, ["stoch"], series_included=True)
            stoch_data = indicators.get("stoch", {}).get("series", {})
            k_series = stoch_data.get("k", [])
            d_series = stoch_data.get("d", [])

            if k_series and d_series and len(k_series) == len(d_series):
                offset = len(df) - len(k_series)
                for i in range(1, len(k_series)):
                    curr_k = k_series[i]["value"]
                    prev_k = k_series[i - 1]["value"]
                    curr_d = d_series[i]["value"]
                    prev_d = d_series[i - 1]["value"]
                    if None in [curr_k, prev_k, curr_d, prev_d]:
                        continue

                    df_idx = i + offset
                    if df_idx < 0 or df_idx >= len(df):
                        continue
                    price = float(df.iloc[df_idx]["close"])

                    # K crosses above D (bullish)
                    if prev_k <= prev_d and curr_k > curr_d:
                        signals.append(
                            {
                                "time": k_series[i]["time"],
                                "type": "K cắt lên D",
                                "price": price,
                                "direction": "up",
                            }
                        )
                    # K crosses below D (bearish)
                    elif prev_k >= prev_d and curr_k < curr_d:
                        signals.append(
                            {
                                "time": k_series[i]["time"],
                                "type": "K cắt xuống D",
                                "price": price,
                                "direction": "down",
                            }
                        )
                    # Oversold zone exit
                    elif prev_k < STOCH_OVERSOLD and curr_k >= STOCH_OVERSOLD:
                        signals.append(
                            {
                                "time": k_series[i]["time"],
                                "type": "Thoát quá bán",
                                "price": price,
                                "direction": "up",
                            }
                        )
                    # Overbought zone exit
                    elif prev_k > STOCH_OVERBOUGHT and curr_k <= STOCH_OVERBOUGHT:
                        signals.append(
                            {
                                "time": k_series[i]["time"],
                                "type": "Thoát quá mua",
                                "price": price,
                                "direction": "down",
                            }
                        )

        elif method_id == "moving_average":
            indicators = calculate_indicators(df, ["ma_20"], series_included=True)
            ma_series = indicators.get("ma_20", {}).get("series", {}).get("value", [])

            if ma_series:
                offset = len(df) - len(ma_series)
                for i in range(1, len(ma_series)):
                    if (
                        ma_series[i]["value"] is None
                        or ma_series[i - 1]["value"] is None
                    ):
                        continue
                    df_idx = i + offset
                    if df_idx < 1 or df_idx >= len(df):
                        continue

                    curr_close = df.iloc[df_idx]["close"]
                    prev_close = df.iloc[df_idx - 1]["close"]
                    curr_ma = ma_series[i]["value"]
                    prev_ma = ma_series[i - 1]["value"]

                    # Price crosses above MA20
                    if prev_close <= prev_ma and curr_close > curr_ma:
                        signals.append(
                            {
                                "time": ma_series[i]["time"],
                                "type": "Cắt lên MA20",
                                "price": float(curr_close),
                                "direction": "up",
                            }
                        )
                    # Price crosses below MA20
                    elif prev_close >= prev_ma and curr_close < curr_ma:
                        signals.append(
                            {
                                "time": ma_series[i]["time"],
                                "type": "Cắt xuống MA20",
                                "price": float(curr_close),
                                "direction": "down",
                            }
                        )

        elif method_id == "adx":
            indicators = calculate_indicators(df, ["adx"], series_included=True)
            adx_data = indicators.get("adx", {}).get("series", {})
            adx_series = adx_data.get("adx", [])
            plus_di = adx_data.get("plusDI", [])
            minus_di = adx_data.get("minusDI", [])

            if adx_series and plus_di and minus_di:
                min_len = min(len(adx_series), len(plus_di), len(minus_di))
                offset = len(df) - min_len
                for i in range(1, min_len):
                    if None in [
                        adx_series[i]["value"],
                        plus_di[i]["value"],
                        minus_di[i]["value"],
                    ]:
                        continue
                    prev_plus = plus_di[i - 1]["value"]
                    curr_plus = plus_di[i]["value"]
                    prev_minus = minus_di[i - 1]["value"]
                    curr_minus = minus_di[i]["value"]
                    adx_val = adx_series[i]["value"]

                    if None in [prev_plus, prev_minus]:
                        continue

                    df_idx = i + offset
                    if df_idx < 0 or df_idx >= len(df):
                        continue
                    price = float(df.iloc[df_idx]["close"])

                    # +DI crosses above -DI (bullish trend)
                    if (
                        adx_val >= ADX_TREND_STRENGTH
                        and prev_plus <= prev_minus
                        and curr_plus > curr_minus
                    ):
                        signals.append(
                            {
                                "time": adx_series[i]["time"],
                                "type": "+DI cắt lên -DI",
                                "price": price,
                                "direction": "up",
                            }
                        )
                    # -DI crosses above +DI (bearish trend)
                    elif (
                        adx_val >= ADX_TREND_STRENGTH
                        and prev_plus >= prev_minus
                        and curr_plus < curr_minus
                    ):
                        signals.append(
                            {
                                "time": adx_series[i]["time"],
                                "type": "-DI cắt lên +DI",
                                "price": price,
                                "direction": "down",
                            }
                        )

        elif method_id == "bb_squeeze":
            indicators = calculate_indicators(df, ["bb"], series_included=True)
            bb_data = indicators.get("bb", {}).get("series", {})
            bandwidth = bb_data.get("bandwidth", [])

            if bandwidth:
                offset = len(df) - len(bandwidth)
                for i in range(1, len(bandwidth)):
                    if (
                        bandwidth[i]["value"] is None
                        or bandwidth[i - 1]["value"] is None
                    ):
                        continue
                    df_idx = i + offset
                    if df_idx < 0 or df_idx >= len(df):
                        continue

                    curr_bw = bandwidth[i]["value"]
                    prev_bw = bandwidth[i - 1]["value"]
                    price = float(df.iloc[df_idx]["close"])

                    # Squeeze breakout (bandwidth expanding after squeeze)
                    # Note: bandwidth is in percentage scale (typically 10-50%)
                    # A squeeze is indicated by bandwidth < 6%, breakout when it expands above 6%
                    if (
                        prev_bw < BB_SQUEEZE_THRESHOLD
                        and curr_bw >= BB_SQUEEZE_THRESHOLD
                    ):
                        prev_close = df.iloc[df_idx - 1]["close"]
                        direction = "up" if price > prev_close else "down"
                        signals.append(
                            {
                                "time": bandwidth[i]["time"],
                                "type": "Squeeze Breakout",
                                "price": price,
                                "direction": direction,
                            }
                        )

        elif method_id == "macd_rsi_confluence":
            indicators = calculate_indicators(df, ["macd", "rsi"], series_included=True)
            macd_data = indicators.get("macd", {}).get("series", {})
            rsi_series = indicators.get("rsi", {}).get("series", {}).get("value", [])
            line_series = macd_data.get("line", [])
            signal_series = macd_data.get("signal", [])

            if line_series and signal_series and rsi_series:
                min_len = min(len(line_series), len(signal_series), len(rsi_series))
                offset = len(df) - min_len
                for i in range(1, min_len):
                    curr_line = line_series[i]["value"]
                    prev_line = line_series[i - 1]["value"]
                    curr_sig = signal_series[i]["value"]
                    prev_sig = signal_series[i - 1]["value"]
                    curr_rsi = rsi_series[i]["value"]

                    if None in [curr_line, prev_line, curr_sig, prev_sig, curr_rsi]:
                        continue

                    df_idx = i + offset
                    if df_idx < 0 or df_idx >= len(df):
                        continue
                    price = float(df.iloc[df_idx]["close"])

                    # Bullish confluence: MACD crosses up AND RSI < RSI_NEUTRAL
                    if (
                        prev_line <= prev_sig
                        and curr_line > curr_sig
                        and curr_rsi < RSI_NEUTRAL
                    ):
                        signals.append(
                            {
                                "time": line_series[i]["time"],
                                "type": "Tín hiệu mua mạnh",
                                "price": price,
                                "direction": "up",
                            }
                        )
                    # Bearish confluence: MACD crosses down AND RSI > RSI_NEUTRAL
                    elif (
                        prev_line >= prev_sig
                        and curr_line < curr_sig
                        and curr_rsi > RSI_NEUTRAL
                    ):
                        signals.append(
                            {
                                "time": line_series[i]["time"],
                                "type": "Tín hiệu bán mạnh",
                                "price": price,
                                "direction": "down",
                            }
                        )

        elif method_id == "vwap":
            indicators = calculate_indicators(df, ["vwap"], series_included=True)
            vwap_series = indicators.get("vwap", {}).get("series", {}).get("value", [])

            if vwap_series:
                offset = len(df) - len(vwap_series)
                for i in range(1, len(vwap_series)):
                    if (
                        vwap_series[i]["value"] is None
                        or vwap_series[i - 1]["value"] is None
                    ):
                        continue
                    df_idx = i + offset
                    if df_idx < 1 or df_idx >= len(df):
                        continue

                    curr_close = df.iloc[df_idx]["close"]
                    prev_close = df.iloc[df_idx - 1]["close"]
                    curr_vwap = vwap_series[i]["value"]
                    prev_vwap = vwap_series[i - 1]["value"]

                    # Price crosses above VWAP
                    if prev_close <= prev_vwap and curr_close > curr_vwap:
                        signals.append(
                            {
                                "time": vwap_series[i]["time"],
                                "type": "Cắt lên VWAP",
                                "price": float(curr_close),
                                "direction": "up",
                            }
                        )
                    # Price crosses below VWAP
                    elif prev_close >= prev_vwap and curr_close < curr_vwap:
                        signals.append(
                            {
                                "time": vwap_series[i]["time"],
                                "type": "Cắt xuống VWAP",
                                "price": float(curr_close),
                                "direction": "down",
                            }
                        )

        elif method_id == "volume":
            # Volume Analysis - OBV trend changes and CMF zero crossings
            indicators = calculate_indicators(df, ["obv", "cmf"], series_included=True)
            obv_series = indicators.get("obv", {}).get("series", {}).get("value", [])
            cmf_series = indicators.get("cmf", {}).get("series", {}).get("value", [])

            # OBV trend detection (using short-term MA comparison)
            if obv_series and len(obv_series) >= OBV_LOOKBACK * 2:
                offset = len(df) - len(obv_series)
                for i in range(OBV_LOOKBACK * 2, len(obv_series)):
                    if obv_series[i]["value"] is None:
                        continue

                    # Calculate OBV_LOOKBACK-period OBV change
                    recent_obv = [
                        obv_series[j]["value"]
                        for j in range(i - OBV_LOOKBACK, i + 1)
                        if obv_series[j]["value"] is not None
                    ]
                    if len(recent_obv) >= OBV_LOOKBACK:
                        df_idx = i + offset
                        if df_idx < 0 or df_idx >= len(df):
                            continue
                        price = float(df.iloc[df_idx]["close"])

                        # Check for trend reversal
                        prev_trend = recent_obv[-2] - recent_obv[0]
                        curr_trend = recent_obv[-1] - recent_obv[1]

                        # OBV turning bullish (from down to up)
                        if prev_trend < 0 and curr_trend > 0:
                            signals.append(
                                {
                                    "time": obv_series[i]["time"],
                                    "type": "OBV đảo chiều tăng",
                                    "price": price,
                                    "direction": "up",
                                }
                            )
                        # OBV turning bearish (from up to down)
                        elif prev_trend > 0 and curr_trend < 0:
                            signals.append(
                                {
                                    "time": obv_series[i]["time"],
                                    "type": "OBV đảo chiều giảm",
                                    "price": price,
                                    "direction": "down",
                                }
                            )

            # CMF zero-line crossings
            if cmf_series and len(cmf_series) >= 2:
                offset = len(df) - len(cmf_series)
                for i in range(1, len(cmf_series)):
                    curr_cmf = cmf_series[i]["value"]
                    prev_cmf = cmf_series[i - 1]["value"]
                    if curr_cmf is None or prev_cmf is None:
                        continue
                    df_idx = i + offset
                    if df_idx < 0 or df_idx >= len(df):
                        continue
                    price = float(df.iloc[df_idx]["close"])

                    # CMF crosses above 0 (money flowing in)
                    if prev_cmf <= 0 and curr_cmf > 0:
                        signals.append(
                            {
                                "time": cmf_series[i]["time"],
                                "type": "CMF > 0 (Tích lũy)",
                                "price": price,
                                "direction": "up",
                            }
                        )
                    # CMF crosses below 0 (money flowing out)
                    elif prev_cmf >= 0 and curr_cmf < 0:
                        signals.append(
                            {
                                "time": cmf_series[i]["time"],
                                "type": "CMF < 0 (Phân phối)",
                                "price": price,
                                "direction": "down",
                            }
                        )

    except Exception as e:
        print(f"Error generating signal points for {method_id}: {e}")

    return signals


# =============================================================================
# TRADING STRATEGIES
# =============================================================================


def _eval_rsi(indicators: dict, timeframe_label: str) -> dict:
    """Evaluate RSI indicator."""
    rsi_data = indicators.get("rsi", {})
    rsi = rsi_data.get("value")
    if rsi is None:
        return None

    if rsi < 30:
        evaluation = (
            f"RSI = {rsi:.1f}, trong vùng quá bán (<30). Có thể là cơ hội mua vào."
        )
        signal = "Bullish"
        confidence = "High"
    elif rsi > 70:
        evaluation = (
            f"RSI = {rsi:.1f}, trong vùng quá mua (>70). Có thể cân nhắc chốt lời."
        )
        signal = "Bearish"
        confidence = "High"
    elif rsi < 40:
        evaluation = f"RSI = {rsi:.1f}, gần vùng quá bán. Theo dõi cơ hội mua."
        signal = "Neutral"
        confidence = "Medium"
    elif rsi > 60:
        evaluation = f"RSI = {rsi:.1f}, gần vùng quá mua. Theo dõi cơ hội chốt lời."
        signal = "Neutral"
        confidence = "Medium"
    else:
        evaluation = (
            f"RSI = {rsi:.1f}, trong vùng trung tính (30-70). Chưa có tín hiệu rõ ràng."
        )
        signal = "Neutral"
        confidence = "Low"

    return {
        "id": "rsi",
        "name": "RSI Analysis",
        "category": "Momentum",
        "description": (
            f"RSI (Relative Strength Index) đo lường tốc độ và mức độ thay đổi giá. "
            f"RSI < 30 = quá bán (mua), RSI > 70 = quá mua (bán)."
            + (f" Phân tích cho khung {timeframe_label}." if timeframe_label else "")
        ),
        "evaluation": evaluation,
        "signal": signal,
        "confidence": confidence,
        "value": round(rsi, 2),
    }


def _eval_macd(indicators: dict, timeframe_label: str) -> dict:
    """Evaluate MACD indicator."""
    macd = indicators.get("macd", {})
    macd_line = macd.get("line")
    macd_signal = macd.get("signal")
    macd_hist = macd.get("histogram")

    if macd_line is None or macd_signal is None:
        return None

    if macd_line > macd_signal and macd_hist > 0:
        evaluation = f"MACD ({macd_line:.2f}) > Signal ({macd_signal:.2f}), Histogram dương. Xu hướng tăng."
        signal = "Bullish"
        confidence = "High" if macd_hist > abs(macd_line * 0.1) else "Medium"
    elif macd_line < macd_signal and macd_hist < 0:
        evaluation = f"MACD ({macd_line:.2f}) < Signal ({macd_signal:.2f}), Histogram âm. Xu hướng giảm."
        signal = "Bearish"
        confidence = "High" if abs(macd_hist) > abs(macd_line * 0.1) else "Medium"
    else:
        evaluation = f"MACD = {macd_line:.2f}, Signal = {macd_signal:.2f}. Chờ xác nhận xu hướng."
        signal = "Neutral"
        confidence = "Low"

    return {
        "id": "macd",
        "name": "MACD Analysis",
        "category": "Trend",
        "description": (
            f"MACD (Moving Average Convergence Divergence) xác định xu hướng và momentum. "
            f"MACD cắt lên Signal = mua, cắt xuống = bán. "
            f"Histogram dương/âm cho thấy momentum tăng/giảm."
            + (f" Phân tích cho khung {timeframe_label}." if timeframe_label else "")
        ),
        "evaluation": evaluation,
        "signal": signal,
        "confidence": confidence,
        "value": {"line": round(macd_line, 2), "signal": round(macd_signal, 2)},
    }


def _eval_moving_average(indicators: dict, timeframe_label: str) -> dict:
    """Evaluate Moving Average positions."""
    current_price = indicators.get("current_price")
    sma20 = indicators.get("sma20")
    sma50 = indicators.get("sma50")
    sma200 = indicators.get("sma200")

    if not (current_price and sma20 and sma50):
        return None

    above_sma20 = current_price > sma20
    above_sma50 = current_price > sma50
    above_sma200 = current_price > sma200 if sma200 else None

    if above_sma20 and above_sma50 and above_sma200:
        evaluation = (
            f"Giá ({current_price:,.0f}) > SMA20, SMA50, SMA200. Xu hướng tăng mạnh."
        )
        signal = "Bullish"
        confidence = "High"
    elif above_sma20 and above_sma50:
        evaluation = f"Giá ({current_price:,.0f}) > SMA20 ({sma20:,.0f}) > SMA50 ({sma50:,.0f}). Xu hướng tăng."
        signal = "Bullish"
        confidence = "Medium"
    elif not above_sma20 and not above_sma50:
        evaluation = f"Giá ({current_price:,.0f}) < SMA20 ({sma20:,.0f}) < SMA50 ({sma50:,.0f}). Xu hướng giảm."
        signal = "Bearish"
        confidence = "Medium"
    else:
        evaluation = (
            f"Giá ({current_price:,.0f}) đang ở giữa các đường MA. Vùng tích lũy."
        )
        signal = "Neutral"
        confidence = "Low"

    return {
        "id": "moving_average",
        "name": "Moving Average Analysis",
        "category": "Trend",
        "description": (
            f"Phân tích vị trí giá so với các đường MA ngắn, trung và dài hạn. "
            f"Giá > MA = xu hướng tăng, giá < MA = xu hướng giảm."
            + (f" Phân tích cho khung {timeframe_label}." if timeframe_label else "")
        ),
        "evaluation": evaluation,
        "signal": signal,
        "confidence": confidence,
        "value": {"sma20": sma20, "sma50": sma50, "sma200": sma200},
    }


def _eval_bollinger_bands(indicators: dict, timeframe_label: str) -> dict:
    """Evaluate Bollinger Bands indicator."""
    current_price = indicators.get("current_price")
    bb = indicators.get("bollinger_bands", {})
    bb_upper = bb.get("upper")
    bb_lower = bb.get("lower")

    if not (bb_upper and bb_lower and current_price):
        return None

    if current_price > bb_upper:
        evaluation = f"Giá ({current_price:,.0f}) > BB Upper ({bb_upper:,.0f}). Có thể quá mua, cẩn thận breakout giả."
        signal = "Bearish"
        confidence = "Medium"
    elif current_price < bb_lower:
        evaluation = f"Giá ({current_price:,.0f}) < BB Lower ({bb_lower:,.0f}). Có thể quá bán, theo dõi hỗ trợ."
        signal = "Bullish"
        confidence = "Medium"
    else:
        evaluation = f"Giá nằm trong biên BB ({bb_lower:,.0f} - {bb_upper:,.0f}). Biến động bình thường."
        signal = "Neutral"
        confidence = "Low"

    return {
        "id": "bollinger_bands",
        "name": "Bollinger Bands Analysis",
        "category": "Volatility",
        "description": (
            f"Bollinger Bands đo lường biến động giá. "
            f"Giá chạm upper band = quá mua, chạm lower band = quá bán."
            + (f" Phân tích cho khung {timeframe_label}." if timeframe_label else "")
        ),
        "evaluation": evaluation,
        "signal": signal,
        "confidence": confidence,
        "value": {"upper": bb_upper, "lower": bb_lower},
    }


def _eval_stochastic(indicators: dict, timeframe_label: str) -> dict:
    """Evaluate Stochastic Oscillator."""
    stoch = indicators.get("stochastic", {})
    stoch_k = stoch.get("k")
    stoch_d = stoch.get("d")

    if stoch_k is None:
        return None

    if stoch_k < 20:
        evaluation = (
            f"%K = {stoch_k:.1f}, trong vùng quá bán (<20). Tín hiệu mua tiềm năng."
        )
        signal = "Bullish"
        confidence = "High" if stoch_d and stoch_k > stoch_d else "Medium"
    elif stoch_k > 80:
        evaluation = (
            f"%K = {stoch_k:.1f}, trong vùng quá mua (>80). Tín hiệu bán tiềm năng."
        )
        signal = "Bearish"
        confidence = "High" if stoch_d and stoch_k < stoch_d else "Medium"
    else:
        evaluation = f"%K = {stoch_k:.1f}, %D = {stoch_d:.1f}. Trong vùng trung tính."
        signal = "Neutral"
        confidence = "Low"

    return {
        "id": "stochastic",
        "name": "Stochastic Oscillator",
        "category": "Momentum",
        "description": (
            f"Stochastic so sánh giá đóng cửa với phạm vi giá trong kỳ. "
            f"K < 20 = quá bán, K > 80 = quá mua. "
            f"K cắt lên D = mua, K cắt xuống D = bán."
            + (f" Phân tích cho khung {timeframe_label}." if timeframe_label else "")
        ),
        "evaluation": evaluation,
        "signal": signal,
        "confidence": confidence,
        "value": {"k": stoch_k, "d": stoch_d},
    }


def _eval_adx(indicators: dict, timeframe_label: str) -> dict:
    """Evaluate ADX trend strength."""
    adx_data = indicators.get("adx", {})
    adx_val = adx_data.get("adx")
    dmp = adx_data.get("dmp")
    dmn = adx_data.get("dmn")

    if adx_val is None:
        return None

    if adx_val > 25:
        if dmp and dmn and dmp > dmn:
            evaluation = f"ADX = {adx_val:.1f} (>25), +DI > -DI. Xu hướng tăng mạnh."
            signal = "Bullish"
            confidence = "High" if adx_val > 40 else "Medium"
        elif dmp and dmn and dmp < dmn:
            evaluation = f"ADX = {adx_val:.1f} (>25), -DI > +DI. Xu hướng giảm mạnh."
            signal = "Bearish"
            confidence = "High" if adx_val > 40 else "Medium"
        else:
            evaluation = (
                f"ADX = {adx_val:.1f} (>25). Xu hướng mạnh nhưng chưa rõ hướng."
            )
            signal = "Neutral"
            confidence = "Medium"
    else:
        evaluation = f"ADX = {adx_val:.1f} (<25). Thị trường đi ngang, không có xu hướng rõ ràng."
        signal = "Neutral"
        confidence = "Low"

    return {
        "id": "adx",
        "name": "ADX Trend Strength",
        "category": "Trend",
        "description": (
            f"ADX đo sức mạnh xu hướng (không phân biệt hướng). "
            f"ADX > 25 = xu hướng mạnh, < 25 = đi ngang. "
            f"+DI > -DI = xu hướng tăng, ngược lại = giảm."
            + (f" Phân tích cho khung {timeframe_label}." if timeframe_label else "")
        ),
        "evaluation": evaluation,
        "signal": signal,
        "confidence": confidence,
        "value": adx_val,
    }


def _eval_volume(indicators: dict, timeframe_label: str) -> dict:
    """Evaluate Volume indicators (OBV, CMF)."""
    obv_trend = indicators.get("obv_trend")
    cmf = indicators.get("cmf")

    if not obv_trend:
        return None

    if obv_trend == "increasing" and cmf and cmf > 0:
        evaluation = f"OBV tăng, CMF = {cmf:.3f} (>0). Dòng tiền vào tích cực, hỗ trợ xu hướng tăng."
        signal = "Bullish"
        confidence = "High" if cmf > 0.1 else "Medium"
    elif obv_trend == "decreasing" and cmf and cmf < 0:
        evaluation = (
            f"OBV giảm, CMF = {cmf:.3f} (<0). Dòng tiền rút ra, cảnh báo xu hướng giảm."
        )
        signal = "Bearish"
        confidence = "High" if cmf < -0.1 else "Medium"
    else:
        cmf_str = f"{cmf:.3f}" if cmf is not None else "N/A"
        evaluation = f"OBV {obv_trend}, CMF = {cmf_str}. Khối lượng trung tính."
        signal = "Neutral"
        confidence = "Low"

    return {
        "id": "volume",
        "name": "Volume Analysis",
        "category": "Volume",
        "description": (
            f"OBV (On Balance Volume) và CMF (Chaikin Money Flow) đo dòng tiền. "
            f"OBV tăng + CMF > 0 = tích lũy, OBV giảm + CMF < 0 = phân phối."
            + (f" Phân tích cho khung {timeframe_label}." if timeframe_label else "")
        ),
        "evaluation": evaluation,
        "signal": signal,
        "confidence": confidence,
        "value": {"obv_trend": obv_trend, "cmf": cmf},
    }


def _eval_support_resistance(indicators: dict, timeframe_label: str) -> dict:
    """Evaluate Support/Resistance levels."""
    current_price = indicators.get("current_price")
    pivot = indicators.get("pivot_points", {})
    fib = indicators.get("fibonacci", {})

    if not (pivot and current_price):
        return None

    pivot_val = pivot.get("pivot")
    r1 = pivot.get("r1")
    s1 = pivot.get("s1")

    if not pivot_val:
        return None

    if current_price > pivot_val:
        evaluation = f"Giá ({current_price:,.0f}) > Pivot ({pivot_val:,.0f}). Kháng cự gần nhất: R1 = {r1:,.0f}."
        signal = "Bullish"
        confidence = "Medium"
    else:
        evaluation = f"Giá ({current_price:,.0f}) < Pivot ({pivot_val:,.0f}). Hỗ trợ gần nhất: S1 = {s1:,.0f}."
        signal = "Bearish"
        confidence = "Medium"

    return {
        "id": "support_resistance",
        "name": "Support/Resistance Analysis",
        "category": "Price Levels",
        "description": (
            f"Pivot Points và Fibonacci xác định vùng hỗ trợ/kháng cự. "
            f"Giá > Pivot = khuynh hướng tăng, < Pivot = khuynh hướng giảm."
            + (f" Phân tích cho khung {timeframe_label}." if timeframe_label else "")
        ),
        "evaluation": evaluation,
        "signal": signal,
        "confidence": confidence,
        "value": {"pivot": pivot_val, "fibonacci_618": fib.get("level_618")},
    }


def _eval_golden_death_cross(indicators: dict, timeframe_label: str) -> dict:
    """
    Strategy 1: Golden Cross / Death Cross
    Golden Cross: SMA50 crosses above SMA200 (bullish)
    Death Cross: SMA50 crosses below SMA200 (bearish)
    """
    sma50 = indicators.get("sma50")
    sma200 = indicators.get("sma200")

    if not (sma50 and sma200):
        return None

    cross_distance_pct = abs(sma50 - sma200) / sma200 * 100

    if sma50 > sma200:
        evaluation = f"SMA50 ({sma50:,.0f}) > SMA200 ({sma200:,.0f}). Golden Cross - Xu hướng tăng dài hạn."
        signal = "Bullish"
        confidence = "High" if cross_distance_pct > 5 else "Medium"
    else:
        evaluation = f"SMA50 ({sma50:,.0f}) < SMA200 ({sma200:,.0f}). Death Cross - Xu hướng giảm dài hạn."
        signal = "Bearish"
        confidence = "High" if cross_distance_pct > 5 else "Medium"

    return {
        "id": "golden_death_cross",
        "name": "Golden Cross / Death Cross",
        "category": "Trend",
        "description": (
            f"Golden Cross (SMA50 cắt lên SMA200) báo hiệu xu hướng tăng dài hạn, "
            f"thường được các tổ chức theo dõi. Death Cross ngược lại báo hiệu giảm. "
            f"Đây là chiến lược trend-following phổ biến nhất cho cổ phiếu."
        ),
        "evaluation": evaluation,
        "signal": signal,
        "confidence": confidence,
        "value": {
            "sma50": sma50,
            "sma200": sma200,
            "distance_pct": round(cross_distance_pct, 2),
        },
    }


def _eval_rsi_divergence(indicators: dict, timeframe_label: str) -> dict:
    """
    Strategy 2: RSI Divergence Detection
    Bullish divergence: Price lower low, RSI higher low
    Bearish divergence: Price higher high, RSI lower high
    """
    rsi_data = indicators.get("rsi", {})
    rsi_series = rsi_data.get("series", [])
    close_series = indicators.get("close_series", [])

    if len(rsi_series) < 5 or len(close_series) < 5:
        return None

    # Extract RSI values from series
    rsi_values = [item.get("value") for item in rsi_series[-5:] if item.get("value")]
    if len(rsi_values) < 3:
        return None

    # Compare first half vs second half for divergence
    price_start = close_series[0]
    price_end = close_series[-1]
    rsi_start = rsi_values[0]
    rsi_end = rsi_values[-1]

    # Bullish divergence: price falling but RSI rising
    if price_end < price_start and rsi_end > rsi_start:
        pct_diff = (rsi_end - rsi_start) / rsi_start * 100
        evaluation = f"Phân kỳ tăng: Giá giảm nhưng RSI tăng ({rsi_start:.1f} → {rsi_end:.1f}). Tín hiệu đảo chiều tăng."
        signal = "Bullish"
        confidence = "High" if pct_diff > 10 else "Medium"
    # Bearish divergence: price rising but RSI falling
    elif price_end > price_start and rsi_end < rsi_start:
        pct_diff = (rsi_start - rsi_end) / rsi_start * 100
        evaluation = f"Phân kỳ giảm: Giá tăng nhưng RSI giảm ({rsi_start:.1f} → {rsi_end:.1f}). Tín hiệu đảo chiều giảm."
        signal = "Bearish"
        confidence = "High" if pct_diff > 10 else "Medium"
    else:
        evaluation = (
            f"Không phát hiện phân kỳ RSI. RSI: {rsi_start:.1f} → {rsi_end:.1f}."
        )
        signal = "Neutral"
        confidence = "Low"

    return {
        "id": "rsi_divergence",
        "name": "RSI Divergence",
        "category": "Momentum",
        "description": (
            f"Phân kỳ RSI là tín hiệu đảo chiều mạnh. "
            f"Phân kỳ tăng (giá giảm, RSI tăng) = mua. "
            f"Phân kỳ giảm (giá tăng, RSI giảm) = bán. "
            f"Chiến lược có độ chính xác cao trong thị trường cổ phiếu."
        ),
        "evaluation": evaluation,
        "signal": signal,
        "confidence": confidence,
        "value": {"rsi_start": round(rsi_start, 2), "rsi_end": round(rsi_end, 2)},
    }


def _eval_volume_breakout(indicators: dict, timeframe_label: str) -> dict:
    """
    Strategy 3: Volume Breakout Confirmation
    High volume (>1.5x SMA) with price movement confirms breakout.
    """
    current_volume = indicators.get("current_volume")
    volume_sma = indicators.get("volume_sma20")
    price_change = indicators.get("price_change")
    price_change_pct = indicators.get("price_change_pct")

    if not (current_volume and volume_sma and volume_sma > 0):
        return None

    volume_ratio = current_volume / volume_sma

    if volume_ratio > 2.0:
        if price_change > 0:
            evaluation = f"Khối lượng ({current_volume:,.0f}) = {volume_ratio:.1f}x SMA20. Breakout tăng mạnh (+{price_change_pct:.1f}%)."
            signal = "Bullish"
            confidence = "High"
        else:
            evaluation = f"Khối lượng ({current_volume:,.0f}) = {volume_ratio:.1f}x SMA20. Breakout giảm mạnh ({price_change_pct:.1f}%)."
            signal = "Bearish"
            confidence = "High"
    elif volume_ratio > 1.5:
        if price_change > 0:
            evaluation = f"Khối lượng ({current_volume:,.0f}) = {volume_ratio:.1f}x SMA20. Tín hiệu tăng có xác nhận."
            signal = "Bullish"
            confidence = "Medium"
        else:
            evaluation = f"Khối lượng ({current_volume:,.0f}) = {volume_ratio:.1f}x SMA20. Tín hiệu giảm có xác nhận."
            signal = "Bearish"
            confidence = "Medium"
    else:
        evaluation = f"Khối lượng ({current_volume:,.0f}) = {volume_ratio:.1f}x SMA20. Không có breakout."
        signal = "Neutral"
        confidence = "Low"

    return {
        "id": "volume_breakout",
        "name": "Volume Breakout",
        "category": "Volume",
        "description": (
            f"Khối lượng giao dịch cao (>1.5x trung bình) xác nhận breakout. "
            f"Volume spike + giá tăng = mua mạnh. "
            f"Volume spike + giá giảm = bán mạnh. "
            f"Khối lượng thấp = chưa có đánh giá rõ ràng."
        ),
        "evaluation": evaluation,
        "signal": signal,
        "confidence": confidence,
        "value": {
            "volume_ratio": round(volume_ratio, 2),
            "change_pct": round(price_change_pct, 2),
        },
    }


def _eval_macd_rsi_confluence(indicators: dict, timeframe_label: str) -> dict:
    """
    Strategy 4: MACD + RSI Confluence
    Strong signal when both indicators align.
    """
    macd = indicators.get("macd", {})
    macd_line = macd.get("line")
    macd_signal_line = macd.get("signal")
    rsi_data = indicators.get("rsi", {})
    rsi = rsi_data.get("value")

    if macd_line is None or macd_signal_line is None or rsi is None:
        return None

    macd_bullish = macd_line > macd_signal_line
    rsi_bullish = rsi < 50
    rsi_bearish = rsi > 50

    if macd_bullish and rsi < 40:
        evaluation = f"MACD tăng + RSI = {rsi:.1f} (<40). Tín hiệu mua mạnh, momentum đang tích lũy."
        signal = "Bullish"
        confidence = "High"
    elif not macd_bullish and rsi > 60:
        evaluation = f"MACD giảm + RSI = {rsi:.1f} (>60). Tín hiệu bán mạnh, momentum đang suy yếu."
        signal = "Bearish"
        confidence = "High"
    elif macd_bullish and rsi_bullish:
        evaluation = (
            f"MACD tăng + RSI = {rsi:.1f} (<50). Tín hiệu mua, cần theo dõi thêm."
        )
        signal = "Bullish"
        confidence = "Medium"
    elif not macd_bullish and rsi_bearish:
        evaluation = (
            f"MACD giảm + RSI = {rsi:.1f} (>50). Tín hiệu bán, cần theo dõi thêm."
        )
        signal = "Bearish"
        confidence = "Medium"
    else:
        evaluation = f"MACD và RSI không đồng thuận. MACD {'tăng' if macd_bullish else 'giảm'}, RSI = {rsi:.1f}."
        signal = "Neutral"
        confidence = "Low"

    return {
        "id": "macd_rsi_confluence",
        "name": "MACD + RSI Confluence",
        "category": "Multi-Indicator",
        "description": (
            f"Kết hợp MACD (xu hướng) và RSI (momentum) cho tín hiệu mạnh hơn. "
            f"MACD tăng + RSI thấp = mua mạnh. "
            f"MACD giảm + RSI cao = bán mạnh. "
            f"Giảm false signals so với dùng từng indicator riêng lẻ."
        ),
        "evaluation": evaluation,
        "signal": signal,
        "confidence": confidence,
        "value": {"macd_bullish": macd_bullish, "rsi": round(rsi, 2)},
    }


def _eval_bb_squeeze(indicators: dict, timeframe_label: str) -> dict:
    """
    Strategy 5: Bollinger Band Squeeze
    Low bandwidth indicates consolidation before breakout.
    """
    bb = indicators.get("bollinger_bands", {})
    bb_bandwidth = bb.get("bandwidth")
    atr = indicators.get("atr")
    current_price = indicators.get("current_price")

    if bb_bandwidth is None:
        return None

    # Squeeze is when bandwidth is very low (< 10%)
    if bb_bandwidth < 0.05:
        evaluation = f"BB Bandwidth = {bb_bandwidth:.1%}. Squeeze cực mạnh - Chuẩn bị breakout lớn!"
        signal = "Neutral"  # Direction unknown, just volatility signal
        confidence = "High"
    elif bb_bandwidth < 0.10:
        evaluation = f"BB Bandwidth = {bb_bandwidth:.1%}. Squeeze - Biến động thấp, chuẩn bị breakout."
        signal = "Neutral"
        confidence = "Medium"
    elif bb_bandwidth > 0.25:
        evaluation = (
            f"BB Bandwidth = {bb_bandwidth:.1%}. Biến động cao, có thể sắp thu hẹp."
        )
        signal = "Neutral"
        confidence = "Low"
    else:
        evaluation = f"BB Bandwidth = {bb_bandwidth:.1%}. Biến động bình thường."
        signal = "Neutral"
        confidence = "Low"

    return {
        "id": "bb_squeeze",
        "name": "Bollinger Band Squeeze",
        "category": "Volatility",
        "description": (
            f"BB Squeeze xảy ra khi bandwidth thu hẹp (<10%), báo hiệu breakout sắp xảy ra. "
            f"Không cho biết hướng breakout, cần kết hợp với các indicator khác. "
            f"Thường xảy ra trước các đợt biến động lớn về giá."
        ),
        "evaluation": evaluation,
        "signal": signal,
        "confidence": confidence,
        "value": {"bandwidth": round(bb_bandwidth, 4)},
    }


def _eval_vwap(indicators: dict, timeframe_label: str) -> dict:
    """
    Strategy 8: VWAP Strategy
    Price above VWAP = bullish intraday, below = bearish.
    """
    vwap = indicators.get("vwap")
    current_price = indicators.get("current_price")

    if not (vwap and current_price):
        return None

    distance_pct = (current_price - vwap) / vwap * 100

    if current_price > vwap:
        if distance_pct > 3:
            evaluation = f"Giá ({current_price:,.0f}) > VWAP ({vwap:,.0f}) +{distance_pct:.1f}%. Xu hướng tăng mạnh trong phiên."
            confidence = "High"
        else:
            evaluation = f"Giá ({current_price:,.0f}) > VWAP ({vwap:,.0f}). Xu hướng tăng trong phiên."
            confidence = "Medium"
        signal = "Bullish"
    else:
        if distance_pct < -3:
            evaluation = f"Giá ({current_price:,.0f}) < VWAP ({vwap:,.0f}) {distance_pct:.1f}%. Xu hướng giảm mạnh trong phiên."
            confidence = "High"
        else:
            evaluation = f"Giá ({current_price:,.0f}) < VWAP ({vwap:,.0f}). Xu hướng giảm trong phiên."
            confidence = "Medium"
        signal = "Bearish"

    return {
        "id": "vwap",
        "name": "VWAP Strategy",
        "category": "Volume",
        "description": (
            f"VWAP (Volume Weighted Average Price) là giá trung bình có trọng số khối lượng. "
            f"Giá > VWAP = bên mua đang kiểm soát. "
            f"Giá < VWAP = bên bán đang kiểm soát. "
            f"Traders tổ chức thường dùng VWAP làm benchmark."
        ),
        "evaluation": evaluation,
        "signal": signal,
        "confidence": confidence,
        "value": {"vwap": vwap, "distance_pct": round(distance_pct, 2)},
    }


def _eval_52_week_proximity(indicators: dict, ticker: str) -> dict:
    """
    Strategy 6: 52-Week High/Low Proximity
    Price near 52W high = momentum, near 52W low = potential reversal.
    """
    current_price = indicators.get("current_price")
    if not current_price or not ticker:
        return None

    try:
        company_info = get_company_info(ticker)
        if "error" in company_info:
            return None

        high_52w = company_info.get("highestPrice1Year")
        low_52w = company_info.get("lowestPrice1Year")

        if not (high_52w and low_52w):
            return None

        proximity_to_high = (high_52w - current_price) / high_52w * 100
        proximity_to_low = (current_price - low_52w) / low_52w * 100
        range_position = (current_price - low_52w) / (high_52w - low_52w) * 100

        if proximity_to_high < 5:
            evaluation = f"Giá ({current_price:,.0f}) gần 52W High ({high_52w:,.0f}), cách {proximity_to_high:.1f}%. Momentum mạnh!"
            signal = "Bullish"
            confidence = "High"
        elif proximity_to_high < 10:
            evaluation = f"Giá ({current_price:,.0f}) ở vùng cao 52W ({range_position:.0f}% range). Xu hướng tích cực."
            signal = "Bullish"
            confidence = "Medium"
        elif proximity_to_low < 10:
            evaluation = f"Giá ({current_price:,.0f}) gần 52W Low ({low_52w:,.0f}), cách +{proximity_to_low:.1f}%. Có thể đảo chiều hoặc tiếp tục giảm."
            signal = "Bearish"
            confidence = "Medium"
        else:
            evaluation = f"Giá ở {range_position:.0f}% phạm vi 52W ({low_52w:,.0f} - {high_52w:,.0f}). Vùng trung tính."
            signal = "Neutral"
            confidence = "Low"

        return {
            "id": "52_week_proximity",
            "name": "52-Week High/Low Proximity",
            "category": "Price Levels",
            "description": (
                f"Phân tích vị trí giá trong phạm vi 52 tuần. "
                f"Giá gần 52W High = momentum tăng, breakout tiềm năng. "
                f"Giá gần 52W Low = có thể reversal hoặc tiếp tục giảm. "
                f"Chiến lược momentum phổ biến cho cổ phiếu."
            ),
            "evaluation": evaluation,
            "signal": signal,
            "confidence": confidence,
            "value": {
                "high_52w": high_52w,
                "low_52w": low_52w,
                "range_position_pct": round(range_position, 2),
            },
        }
    except Exception:
        return None


def _eval_relative_strength_vnindex(ticker: str) -> dict:
    """
    Strategy 7: Relative Strength vs VN-Index
    Compare stock performance to index for alpha.
    """
    if not ticker:
        return None

    try:
        annual_return = get_annual_return(ticker, length_report=1)
        if "error" in annual_return or not annual_return.get("returns"):
            return None

        returns = annual_return.get("returns", [])
        if not returns:
            return None

        latest = returns[0]
        stock_return = latest.get("stockReturn")
        vnindex_return = latest.get("vnIndex")
        outperformance = latest.get("outperformance")

        if stock_return is None or vnindex_return is None:
            return None

        if outperformance and outperformance > 10:
            evaluation = f"Cổ phiếu +{stock_return:.1f}% vs VN-Index +{vnindex_return:.1f}%. Alpha = +{outperformance:.1f}%. Vượt trội mạnh!"
            signal = "Bullish"
            confidence = "High"
        elif outperformance and outperformance > 0:
            evaluation = f"Cổ phiếu +{stock_return:.1f}% vs VN-Index +{vnindex_return:.1f}%. Alpha = +{outperformance:.1f}%. Vượt trội."
            signal = "Bullish"
            confidence = "Medium"
        elif outperformance and outperformance < -10:
            evaluation = f"Cổ phiếu {stock_return:.1f}% vs VN-Index {vnindex_return:.1f}%. Alpha = {outperformance:.1f}%. Kém hơn nhiều!"
            signal = "Bearish"
            confidence = "High"
        elif outperformance and outperformance < 0:
            evaluation = f"Cổ phiếu {stock_return:.1f}% vs VN-Index {vnindex_return:.1f}%. Alpha = {outperformance:.1f}%. Kém hơn."
            signal = "Bearish"
            confidence = "Medium"
        else:
            evaluation = f"Cổ phiếu {stock_return:.1f}% vs VN-Index {vnindex_return:.1f}%. Tương đương thị trường."
            signal = "Neutral"
            confidence = "Low"

        return {
            "id": "relative_strength_vnindex",
            "name": "Relative Strength vs VN-Index",
            "category": "Performance",
            "description": (
                f"So sánh hiệu suất cổ phiếu với VN-Index để đánh giá alpha. "
                f"Alpha dương = cổ phiếu vượt trội thị trường. "
                f"Alpha âm = kém hơn thị trường. "
                f"Chiến lược quan trọng cho sector rotation và stock picking."
            ),
            "evaluation": evaluation,
            "signal": signal,
            "confidence": confidence,
            "value": {
                "stock_return": stock_return,
                "vnindex_return": vnindex_return,
                "outperformance": outperformance,
            },
        }
    except Exception:
        return None
