"""
Indicator Calculation Module.
Provides unified functions to calculate technical indicators with optional series data.
"""

import pandas as pd
import pandas_ta as ta
from typing import Optional, List, Dict, Any
from functools import partial
from app.tools.indicator_config import IndicatorConfig, DEFAULT_CONFIG, DEFAULT_STYLING


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def _safe_calc(func, *args, **kwargs):
    """Safely calculate an indicator, returning None on error."""
    try:
        result = func(*args, **kwargs)
        return result
    except Exception:
        return None


def _get_last_value(series: Optional[pd.Series]) -> Optional[float]:
    """Get the last non-null value from a pandas Series."""
    if series is None or (hasattr(series, "empty") and series.empty):
        return None
    if isinstance(series, pd.DataFrame):
        return None
    try:
        last_val = series.dropna().iloc[-1] if not series.dropna().empty else None
        return round(float(last_val), 4) if last_val is not None else None
    except Exception:
        return None


def _get_last_dict(df_result: Optional[pd.DataFrame]) -> Optional[dict]:
    """Get the last row of a DataFrame as a dict."""
    if df_result is None or df_result.empty:
        return None
    try:
        last_row = df_result.dropna().iloc[-1].to_dict()
        return {
            k: round(float(v), 4) if v is not None else None
            for k, v in last_row.items()
        }
    except Exception:
        return None


def _get_col_last_value(df: Optional[pd.DataFrame], col_name: str) -> Optional[float]:
    """Get the last non-null value from a specific DataFrame column."""
    if df is None or df.empty or col_name not in df.columns:
        return None
    return _get_last_value(df[col_name])


def _series_to_list(
    series: Optional[pd.Series], timestamps: pd.DatetimeIndex
) -> List[Dict[str, Any]]:
    """Convert pandas Series to chart-compatible format with Unix timestamps."""
    if series is None or series.empty:
        return []

    result = []
    for i, (idx, val) in enumerate(series.items()):
        if pd.notna(val):
            time_val = (
                int(idx.timestamp())
                if hasattr(idx, "timestamp")
                else int(timestamps[i].timestamp())
            ) - 7 * 60 * 60  # Index has no timezone -> timestamp() treats it as UTC -> convert to time will be shifted 7h (UTC+7), need to subtract again
            result.append({"time": time_val, "value": round(float(val), 4)})
    return result


def _df_column_to_list(
    df: Optional[pd.DataFrame], col_name: str, timestamps: pd.DatetimeIndex
) -> List[Dict[str, Any]]:
    """Extract a column from DataFrame and convert to list format."""
    if df is None or df.empty or col_name not in df.columns:
        return []
    return _series_to_list(df[col_name], timestamps)


# =============================================================================
# INDICATOR REGISTRY
# =============================================================================

INDICATOR_REGISTRY = {}


def register_indicator(
    key: str,
    label: str,
    description: str = None,
    category: str = "Khác",
    order: int = 0,
):
    """Decorator to register an indicator calculation function.

    Args:
        key: Unique identifier for the indicator
        label: Display label with parameters (e.g., 'SMA(20)')
        description: Description of the indicator (e.g., 'Simple Moving Average')
        category: Category for grouping on FE (Overlap, Momentum, Volatility, Volume, Trend, Statistics, Cycle, Performance)
    """

    def decorator(func):
        INDICATOR_REGISTRY[key] = {
            "func": func,
            "label": label,
            "description": description or label,
            "category": category,
            "order": order,
        }
        return func

    return decorator


# =============================================================================
# MOVING AVERAGES (Overlay - Pane 0)
# =============================================================================


def calc_ma(
    df: pd.DataFrame,
    config: IndicatorConfig,
    series_included: bool,
    length: int = None,
) -> Dict[str, Any]:
    """Calculate Simple Moving Average."""
    if length is None:
        length = config.ma_lengths[2] if len(config.ma_lengths) > 2 else 20
    series = _safe_calc(ta.sma, df["close"], length=length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_ema(
    df: pd.DataFrame,
    config: IndicatorConfig,
    series_included: bool,
    length: int = None,
) -> Dict[str, Any]:
    """Calculate Exponential Moving Average."""
    if length is None:
        length = config.ma_lengths[1] if len(config.ma_lengths) > 1 else 10
    series = _safe_calc(ta.ema, df["close"], length=length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_wma(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Weighted Moving Average."""
    series = _safe_calc(ta.wma, df["close"], length=config.wma_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_vwap(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Volume Weighted Average Price."""
    series = _safe_calc(ta.vwap, df["high"], df["low"], df["close"], df["volume"])
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


# =============================================================================
# BANDS/CHANNELS (Overlay - Pane 0, Multi-series)
# =============================================================================


def calc_dema(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Double Exponential Moving Average."""
    series = _safe_calc(ta.dema, df["close"], length=config.dema_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_tema(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Triple Exponential Moving Average."""
    series = _safe_calc(ta.tema, df["close"], length=config.tema_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_hma(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Hull Moving Average."""
    series = _safe_calc(ta.hma, df["close"], length=config.hma_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_kama(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Kaufman's Adaptive Moving Average."""
    series = _safe_calc(ta.kama, df["close"], length=config.kama_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_zlma(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Zero Lag Moving Average."""
    series = _safe_calc(ta.zlma, df["close"], length=config.zlma_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_t3(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate T3 Moving Average."""
    series = _safe_calc(ta.t3, df["close"], length=config.t3_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_trima(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Triangular Moving Average."""
    series = _safe_calc(ta.trima, df["close"], length=config.trima_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_vidya(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Variable Index Dynamic Average."""
    series = _safe_calc(ta.vidya, df["close"], length=config.vidya_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_fwma(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Fibonacci Weighted Moving Average."""
    series = _safe_calc(ta.fwma, df["close"], length=config.fwma_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_pwma(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Pascal Weighted Moving Average."""
    series = _safe_calc(ta.pwma, df["close"], length=config.pwma_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_swma(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Symmetric Weighted Moving Average."""
    series = _safe_calc(ta.swma, df["close"], length=config.swma_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_sinwma(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Sine Weighted Moving Average."""
    series = _safe_calc(ta.sinwma, df["close"], length=config.sinwma_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_alma(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Arnaud Legoux Moving Average."""
    series = _safe_calc(ta.alma, df["close"], length=config.alma_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_mcgd(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate McGinley Dynamic."""
    series = _safe_calc(ta.mcgd, df["close"], length=config.mcgd_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_jma(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Jurik Moving Average."""
    series = _safe_calc(ta.jma, df["close"], length=config.jma_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_hl2(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Average of High and Low."""
    series = _safe_calc(ta.hl2, df["high"], df["low"])
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_hlc3(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Average of High, Low, and Close."""
    series = _safe_calc(ta.hlc3, df["high"], df["low"], df["close"])
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_ohlc4(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Average of Open, High, Low, and Close."""
    series = _safe_calc(ta.ohlc4, df["open"], df["high"], df["low"], df["close"])
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_wcp(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Weighted Close Price."""
    series = _safe_calc(ta.wcp, df["high"], df["low"], df["close"])
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_midpoint(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Midpoint."""
    series = _safe_calc(ta.midpoint, df["close"], length=config.midpoint_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_midprice(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Midprice."""
    series = _safe_calc(
        ta.midprice, df["high"], df["low"], length=config.midprice_length
    )
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_supertrend(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Supertrend."""
    result = _safe_calc(
        ta.supertrend,
        df["high"],
        df["low"],
        df["close"],
        length=config.supertrend_length,
        multiplier=config.supertrend_multiplier,
    )
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    # Usually: SUPERT_7_3.0, SUPERTd_7_3.0, SUPERTl_7_3.0, SUPERTs_7_3.0
    # We want the trend line (first column) and direction
    trend_col = cols[0]

    series_data = None
    if series_included:
        series_data = {
            "value": _df_column_to_list(result, trend_col, df.index),
        }

    return {
        "series": series_data if series_included else None,
        "lastValue": _get_col_last_value(result, trend_col),
    }


def calc_ichimoku(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Ichimoku Kinko Hyo."""
    ichi = _safe_calc(
        ta.ichimoku,
        df["high"],
        df["low"],
        df["close"],
        tenkan=config.ichimoku_tenkan,
        kijun=config.ichimoku_kijun,
        senkou=config.ichimoku_senkou,
    )

    if ichi is None or not isinstance(ichi, tuple) or len(ichi) < 2:
        return {"series": None, "lastValue": None}

    # ichimoku returns (result_df, span_df) in pandas_ta
    result = ichi[0]
    span = ichi[1]

    # Combined for easier handling
    combined = pd.concat([result, span], axis=1)
    cols = combined.columns.tolist()

    # Identifying columns (Tenkan, Kijun, Chikou, Span A, Span B)
    tenkan_col = next((c for c in cols if c.startswith("ITS_")), cols[0])
    kijun_col = next((c for c in cols if c.startswith("IKS_")), cols[1])
    chikou_col = next((c for c in cols if c.startswith("ICS_")), cols[2])
    span_a_col = next((c for c in cols if c.startswith("ISA_")), cols[3])
    span_b_col = next((c for c in cols if c.startswith("ISB_")), cols[4])

    last_value = {
        "conversion": _get_col_last_value(combined, tenkan_col),
        "base": _get_col_last_value(combined, kijun_col),
        "lagging": _get_col_last_value(combined, chikou_col),
        "spanA": _get_col_last_value(combined, span_a_col),
        "spanB": _get_col_last_value(combined, span_b_col),
    }

    series_data = None
    if series_included:
        series_data = {
            "conversion": _df_column_to_list(combined, tenkan_col, df.index),
            "base": _df_column_to_list(combined, kijun_col, df.index),
            "lagging": _df_column_to_list(combined, chikou_col, df.index),
            "spanA": _df_column_to_list(combined, span_a_col, df.index),
            "spanB": _df_column_to_list(combined, span_b_col, df.index),
        }

    return {"series": series_data, "lastValue": last_value}


def calc_hilo(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Gann HiLo."""
    result = _safe_calc(
        ta.hilo,
        df["high"],
        df["low"],
        df["close"],
        high_length=config.hilo_high_length,
        low_length=config.hilo_low_length,
    )
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    # HILO_13_21, HILOl_13_21, HILOs_13_21
    hilo_col = cols[0]

    series_data = None
    if series_included:
        series_data = {
            "value": _df_column_to_list(result, hilo_col, df.index),
        }
    return {
        "series": series_data if series_included else None,
        "lastValue": _get_col_last_value(result, hilo_col),
    }


def calc_alligator(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Bill Williams Alligator."""
    result = _safe_calc(ta.alligator, df["high"], df["low"])
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    jaw_col = next((c for c in cols if c.startswith("AG_J")), cols[0])
    teeth_col = next((c for c in cols if c.startswith("AG_T")), cols[1])
    lips_col = next((c for c in cols if c.startswith("AG_L")), cols[2])

    last_value = {
        "jaw": _get_col_last_value(result, jaw_col),
        "teeth": _get_col_last_value(result, teeth_col),
        "lips": _get_col_last_value(result, lips_col),
    }

    series_data = None
    if series_included:
        series_data = {
            "jaw": _df_column_to_list(result, jaw_col, df.index),
            "teeth": _df_column_to_list(result, teeth_col, df.index),
            "lips": _df_column_to_list(result, lips_col, df.index),
        }
    return {"series": series_data, "lastValue": last_value}


def calc_linreg(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Linear Regression."""
    series = _safe_calc(ta.linreg, df["close"], length=config.linreg_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_ht_trendline(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Hilbert Transform Trendline."""
    series = _safe_calc(ta.ht_trendline, df["close"])
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_mama(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate MESA Adaptive Moving Average."""
    result = _safe_calc(ta.mama, df["close"])
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    mama_col = cols[0]
    fama_col = cols[1]

    last_value = {
        "mama": _get_col_last_value(result, mama_col),
        "fama": _get_col_last_value(result, fama_col),
    }

    series_data = None
    if series_included:
        series_data = {
            "mama": _df_column_to_list(result, mama_col, df.index),
            "fama": _df_column_to_list(result, fama_col, df.index),
        }
    return {"series": series_data, "lastValue": last_value}


def calc_bb(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Bollinger Bands (upper, middle, lower)."""
    result = _safe_calc(
        ta.bbands, df["close"], length=config.bbands_length, std=config.bbands_std
    )
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    lower_col = next((c for c in cols if c.startswith("BBL_")), cols[0])
    mid_col = next(
        (c for c in cols if c.startswith("BBM_")), cols[1] if len(cols) > 1 else cols[0]
    )
    upper_col = next(
        (c for c in cols if c.startswith("BBU_")), cols[2] if len(cols) > 2 else cols[0]
    )
    bandwidth_col = next(
        (c for c in cols if c.startswith("BBB_")), cols[3] if len(cols) > 3 else cols[0]
    )
    percentage_col = next(
        (c for c in cols if c.startswith("BBP_")), cols[4] if len(cols) > 4 else cols[0]
    )

    last_value = {
        "upper": _get_col_last_value(result, upper_col),
        "middle": _get_col_last_value(result, mid_col),
        "lower": _get_col_last_value(result, lower_col),
        "bandwidth": _get_col_last_value(result, bandwidth_col),
        "percentage": _get_col_last_value(result, percentage_col),
    }

    series_data = None
    if series_included:
        series_data = {
            "upper": _df_column_to_list(result, upper_col, df.index),
            "middle": _df_column_to_list(result, mid_col, df.index),
            "lower": _df_column_to_list(result, lower_col, df.index),
            "bandwidth": _df_column_to_list(result, bandwidth_col, df.index),
            "percentage": _df_column_to_list(result, percentage_col, df.index),
        }

    return {"series": series_data, "lastValue": last_value}


def calc_atr(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Average True Range."""
    series = _safe_calc(
        ta.atr, df["high"], df["low"], df["close"], length=config.atr_length
    )
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


# =============================================================================
# MOMENTUM OSCILLATORS (Pane 0)
# =============================================================================


def calc_donchian(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Donchian Channels."""
    result = _safe_calc(
        ta.donchian,
        df["high"],
        df["low"],
        lower_length=config.donchian_lower_length,
        upper_length=config.donchian_upper_length,
    )
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    lower_col = next((c for c in cols if c.startswith("DCL_")), cols[0])
    mid_col = next((c for c in cols if c.startswith("DCM_")), cols[1])
    upper_col = next((c for c in cols if c.startswith("DCU_")), cols[2])

    last_value = {
        "lower": _get_col_last_value(result, lower_col),
        "middle": _get_col_last_value(result, mid_col),
        "upper": _get_col_last_value(result, upper_col),
    }

    series_data = None
    if series_included:
        series_data = {
            "lower": _df_column_to_list(result, lower_col, df.index),
            "middle": _df_column_to_list(result, mid_col, df.index),
            "upper": _df_column_to_list(result, upper_col, df.index),
        }
    return {"series": series_data, "lastValue": last_value}


def calc_kc(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Keltner Channels."""
    result = _safe_calc(
        ta.kc,
        df["high"],
        df["low"],
        df["close"],
        length=config.kc_length,
        scalar=config.kc_scalar,
        mamode=config.kc_mamode,
    )
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    lower_col = next((c for c in cols if c.startswith("KCL")), cols[0])
    mid_col = next((c for c in cols if c.startswith("KCB")), cols[1])
    upper_col = next((c for c in cols if c.startswith("KCU")), cols[2])

    last_value = {
        "lower": _get_col_last_value(result, lower_col),
        "middle": _get_col_last_value(result, mid_col),
        "upper": _get_col_last_value(result, upper_col),
    }

    series_data = None
    if series_included:
        series_data = {
            "lower": _df_column_to_list(result, lower_col, df.index),
            "middle": _df_column_to_list(result, mid_col, df.index),
            "upper": _df_column_to_list(result, upper_col, df.index),
        }
    return {"series": series_data, "lastValue": last_value}


def calc_massi(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Mass Index."""
    series = _safe_calc(
        ta.massi,
        df["high"],
        df["low"],
        fast=config.massi_fast,
        slow=config.massi_slow,
    )
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_natr(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Normalized Average True Range."""
    series = _safe_calc(
        ta.natr,
        df["high"],
        df["low"],
        df["close"],
        length=config.natr_length,
    )
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_pdist(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Price Distance."""
    series = _safe_calc(ta.pdist, df["open"], df["high"], df["low"], df["close"])
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_rvi(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Relative Volatility Index."""
    series = _safe_calc(
        ta.rvi,
        df["close"],
        df["high"],
        df["low"],
        length=config.rvi_length,
    )
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_thermo(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Thermo."""
    result = _safe_calc(
        ta.thermo,
        df["high"],
        df["low"],
        length=config.thermo_length,
        long=config.thermo_long,
        short=config.thermo_short,
    )
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    thermo_col = next((c for c in cols if c.startswith("THERMO_")), cols[0])
    ma_col = next((c for c in cols if c.startswith("THERMOma_")), cols[1])
    long_col = next((c for c in cols if c.startswith("THERMOl_")), cols[2])
    short_col = next((c for c in cols if c.startswith("THERMOS_")), cols[3])

    last_value = {
        "thermo": _get_col_last_value(result, thermo_col),
        "ma": _get_col_last_value(result, ma_col),
        "long": _get_col_last_value(result, long_col),
        "short": _get_col_last_value(result, short_col),
    }

    series_data = None
    if series_included:
        series_data = {
            "thermo": _df_column_to_list(result, thermo_col, df.index),
            "ma": _df_column_to_list(result, ma_col, df.index),
            "long": _df_column_to_list(result, long_col, df.index),
            "short": _df_column_to_list(result, short_col, df.index),
        }
    return {"series": series_data, "lastValue": last_value}


def calc_true_range(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate True Range."""
    series = _safe_calc(ta.true_range, df["high"], df["low"], df["close"])
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_ui(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Ulcer Index."""
    series = _safe_calc(ta.ui, df["close"], length=config.ui_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_aberration(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Aberration."""
    result = _safe_calc(
        ta.aberration,
        df["high"],
        df["low"],
        df["close"],
        length=config.aberration_length,
        zg=config.aberration_zg,
        sg=config.aberration_sg,
        xg=config.aberration_xg,
    )
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    zg_col = next((c for c in cols if c.startswith("ABER_ZG")), cols[0])
    sg_col = next((c for c in cols if c.startswith("ABER_SG")), cols[1])
    xg_col = next((c for c in cols if c.startswith("ABER_XG")), cols[2])
    atr_col = next((c for c in cols if c.startswith("ABER_ATR")), cols[3])

    last_value = {
        "zg": _get_col_last_value(result, zg_col),
        "sg": _get_col_last_value(result, sg_col),
        "xg": _get_col_last_value(result, xg_col),
        "atr": _get_col_last_value(result, atr_col),
    }

    series_data = None
    if series_included:
        series_data = {
            "zg": _df_column_to_list(result, zg_col, df.index),
            "sg": _df_column_to_list(result, sg_col, df.index),
            "xg": _df_column_to_list(result, xg_col, df.index),
            "atr": _df_column_to_list(result, atr_col, df.index),
        }
    return {"series": series_data, "lastValue": last_value}


def calc_accbands(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Acceleration Bands."""
    result = _safe_calc(
        ta.accbands,
        df["high"],
        df["low"],
        df["close"],
        length=config.accbands_length,
        c=config.accbands_c,
    )
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    lower_col = next((c for c in cols if c.startswith("ACCBL")), cols[0])
    mid_col = next((c for c in cols if c.startswith("ACCBM")), cols[1])
    upper_col = next((c for c in cols if c.startswith("ACCBU")), cols[2])

    last_value = {
        "lower": _get_col_last_value(result, lower_col),
        "middle": _get_col_last_value(result, mid_col),
        "upper": _get_col_last_value(result, upper_col),
    }

    series_data = None
    if series_included:
        series_data = {
            "lower": _df_column_to_list(result, lower_col, df.index),
            "middle": _df_column_to_list(result, mid_col, df.index),
            "upper": _df_column_to_list(result, upper_col, df.index),
        }
    return {"series": series_data, "lastValue": last_value}


# =============================================================================
# MOMENTUM OSCILLATORS (Pane 0)
# =============================================================================


def calc_rsi(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Relative Strength Index."""
    series = _safe_calc(ta.rsi, df["close"], length=config.rsi_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_rsi_fast(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Fast Relative Strength Index."""
    series = _safe_calc(ta.rsi, df["close"], length=config.rsi_fast_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_stochrsi(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Stochastic RSI."""
    result = _safe_calc(
        ta.stochrsi,
        df["close"],
        length=config.stochrsi_length,
        rsi_length=config.stochrsi_rsi_length,
        k=config.stochrsi_k,
        d=config.stochrsi_d,
    )
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    k_col = cols[0]
    d_col = cols[1] if len(cols) > 1 else cols[0]

    last_value = {
        "k": _get_col_last_value(result, k_col),
        "d": _get_col_last_value(result, d_col),
    }

    series_data = None
    if series_included:
        series_data = {
            "k": _df_column_to_list(result, k_col, df.index),
            "d": _df_column_to_list(result, d_col, df.index),
        }
    return {"series": series_data, "lastValue": last_value}


def calc_mom(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Momentum."""
    series = _safe_calc(ta.mom, df["close"], length=config.mom_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_ao(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Awesome Oscillator."""
    series = _safe_calc(
        ta.ao, df["high"], df["low"], fast=config.ao_fast, slow=config.ao_slow
    )
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_apo(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Absolute Price Oscillator."""
    series = _safe_calc(ta.apo, df["close"], fast=config.apo_fast, slow=config.apo_slow)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_ppo(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Percentage Price Oscillator."""
    result = _safe_calc(
        ta.ppo,
        df["close"],
        fast=config.ppo_fast,
        slow=config.ppo_slow,
        signal=config.ppo_signal,
    )
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    ppo_col = cols[0]
    hist_col = cols[1]
    signal_col = cols[2]

    last_value = {
        "ppo": _get_col_last_value(result, ppo_col),
        "signal": _get_col_last_value(result, signal_col),
        "histogram": _get_col_last_value(result, hist_col),
    }

    series_data = None
    if series_included:
        series_data = {
            "ppo": _df_column_to_list(result, ppo_col, df.index),
            "signal": _df_column_to_list(result, signal_col, df.index),
            "histogram": _df_column_to_list(result, hist_col, df.index),
        }
    return {"series": series_data, "lastValue": last_value}


def calc_bias(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Bias."""
    series = _safe_calc(ta.bias, df["close"], length=config.bias_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_bop(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Balance of Power."""
    series = _safe_calc(ta.bop, df["open"], df["high"], df["low"], df["close"])
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_brar(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate BRAR."""
    result = _safe_calc(
        ta.brar,
        df["open"],
        df["high"],
        df["low"],
        df["close"],
        length=config.brar_length,
    )
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    ar_col = cols[0]
    br_col = cols[1]

    last_value = {
        "ar": _get_col_last_value(result, ar_col),
        "br": _get_col_last_value(result, br_col),
    }

    series_data = None
    if series_included:
        series_data = {
            "ar": _df_column_to_list(result, ar_col, df.index),
            "br": _df_column_to_list(result, br_col, df.index),
        }
    return {"series": series_data, "lastValue": last_value}


def calc_cfo(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Chande Forecast Oscillator."""
    series = _safe_calc(ta.cfo, df["close"], length=config.cfo_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_cg(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Center of Gravity."""
    series = _safe_calc(ta.cg, df["close"], length=config.cg_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_cmo(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Chande Momentum Oscillator."""
    series = _safe_calc(ta.cmo, df["close"], length=config.cmo_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_coppock(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Coppock Curve."""
    series = _safe_calc(
        ta.coppock,
        df["close"],
        length=config.coppock_length,
        fast=config.coppock_fast,
        slow=config.coppock_slow,
    )
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_cti(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Correlation Trend Indicator."""
    series = _safe_calc(ta.cti, df["close"], length=config.cti_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_er(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Efficiency Ratio."""
    series = _safe_calc(ta.er, df["close"], length=config.er_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_eri(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Elder Ray Index."""
    result = _safe_calc(
        ta.eri, df["high"], df["low"], df["close"], length=config.eri_length
    )
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    bull_col = next((c for c in cols if c.startswith("BULL_")), cols[0])
    bear_col = next((c for c in cols if c.startswith("BEAR_")), cols[1])

    last_value = {
        "bull": _get_col_last_value(result, bull_col),
        "bear": _get_col_last_value(result, bear_col),
    }

    series_data = None
    if series_included:
        series_data = {
            "bull": _df_column_to_list(result, bull_col, df.index),
            "bear": _df_column_to_list(result, bear_col, df.index),
        }
    return {"series": series_data, "lastValue": last_value}


def calc_fisher(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Fisher Transform."""
    result = _safe_calc(ta.fisher, df["high"], df["low"], length=config.fisher_length)
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    fisher_col = next((c for c in cols if c.startswith("FISHERT_")), cols[0])
    signal_col = next((c for c in cols if c.startswith("FISHERTs_")), cols[1])

    last_value = {
        "fisher": _get_col_last_value(result, fisher_col),
        "signal": _get_col_last_value(result, signal_col),
    }

    series_data = None
    if series_included:
        series_data = {
            "fisher": _df_column_to_list(result, fisher_col, df.index),
            "signal": _df_column_to_list(result, signal_col, df.index),
        }
    return {"series": series_data, "lastValue": last_value}


def calc_inertia(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Inertia."""
    series = _safe_calc(
        ta.inertia,
        df["high"],
        df["low"],
        df["close"],
        length=config.inertia_length,
        rvi_length=config.inertia_rvi_length,
    )
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_kdj(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate KDJ."""
    result = _safe_calc(
        ta.kdj,
        df["high"],
        df["low"],
        df["close"],
        length=config.kdj_length,
        signal=config.kdj_signal,
    )
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    # K, D, J
    k_col = cols[0]
    d_col = cols[1]
    j_col = cols[2]

    last_value = {
        "k": _get_col_last_value(result, k_col),
        "d": _get_col_last_value(result, d_col),
        "j": _get_col_last_value(result, j_col),
    }

    series_data = None
    if series_included:
        series_data = {
            "k": _df_column_to_list(result, k_col, df.index),
            "d": _df_column_to_list(result, d_col, df.index),
            "j": _df_column_to_list(result, j_col, df.index),
        }
    return {"series": series_data, "lastValue": last_value}


def calc_kst(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Know Sure Thing."""
    result = _safe_calc(
        ta.kst,
        df["close"],
        roc1=config.kst_roc1,
        roc2=config.kst_roc2,
        roc3=config.kst_roc3,
        roc4=config.kst_roc4,
        sma1=config.kst_sma1,
        sma2=config.kst_sma2,
        sma3=config.kst_sma3,
        sma4=config.kst_sma4,
        signal=config.kst_signal,
    )
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    kst_col = cols[0]
    signal_col = cols[1]

    last_value = {
        "kst": _get_col_last_value(result, kst_col),
        "signal": _get_col_last_value(result, signal_col),
    }

    series_data = None
    if series_included:
        series_data = {
            "kst": _df_column_to_list(result, kst_col, df.index),
            "signal": _df_column_to_list(result, signal_col, df.index),
        }
    return {"series": series_data, "lastValue": last_value}


def calc_pgo(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Pretty Good Oscillator."""
    series = _safe_calc(
        ta.pgo, df["high"], df["low"], df["close"], length=config.pgo_length
    )
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_psl(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Psychological Line."""
    series = _safe_calc(ta.psl, df["close"], df["open"], length=config.psl_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_qqe(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Quantitative Qualitative Estimation."""
    result = _safe_calc(
        ta.qqe,
        df["close"],
        length=config.qqe_length,
        smooth=config.qqe_smooth,
        factor=config.qqe_factor,
    )
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    # QQE_14_5_4.236, QQE_14_5_4.236_RSIMA, QQE_14_5_4.236_LR
    qqe_col = cols[0]
    long_col = cols[1] if len(cols) > 1 else cols[0]
    short_col = cols[2] if len(cols) > 2 else cols[0]

    last_value = {
        "qqe": _get_col_last_value(result, qqe_col),
        "long": _get_col_last_value(result, long_col),
        "short": _get_col_last_value(result, short_col),
    }

    series_data = None
    if series_included:
        series_data = {
            "qqe": _df_column_to_list(result, qqe_col, df.index),
            "long": _df_column_to_list(result, long_col, df.index),
            "short": _df_column_to_list(result, short_col, df.index),
        }
    return {"series": series_data, "lastValue": last_value}


def calc_rvgi(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Relative Vigor Index."""
    result = _safe_calc(
        ta.rvgi,
        df["open"],
        df["high"],
        df["low"],
        df["close"],
        length=config.rvgi_length,
        swma_length=config.rvgi_swma_length,
    )
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    rvgi_col = cols[0]
    signal_col = cols[1]

    last_value = {
        "rvgi": _get_col_last_value(result, rvgi_col),
        "signal": _get_col_last_value(result, signal_col),
    }

    series_data = None
    if series_included:
        series_data = {
            "rvgi": _df_column_to_list(result, rvgi_col, df.index),
            "signal": _df_column_to_list(result, signal_col, df.index),
        }
    return {"series": series_data, "lastValue": last_value}


def calc_slope(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Slope."""
    series = _safe_calc(ta.slope, df["close"], length=config.slope_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_smi(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Stochastic Momentum Index."""
    result = _safe_calc(
        ta.smi,
        df["close"],
        fast=config.smi_fast,
        slow=config.smi_slow,
        signal=config.smi_signal,
    )
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    smi_col = cols[0]
    signal_col = cols[1]
    osc_col = cols[2]

    last_value = {
        "smi": _get_col_last_value(result, smi_col),
        "signal": _get_col_last_value(result, signal_col),
        "oscillator": _get_col_last_value(result, osc_col),
    }

    series_data = None
    if series_included:
        series_data = {
            "smi": _df_column_to_list(result, smi_col, df.index),
            "signal": _df_column_to_list(result, signal_col, df.index),
            "oscillator": _df_column_to_list(result, osc_col, df.index),
        }
    return {"series": series_data, "lastValue": last_value}


def calc_squeeze(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Squeeze."""
    result = _safe_calc(
        ta.squeeze,
        df["high"],
        df["low"],
        df["close"],
        bb_length=config.squeeze_bb_length,
        bb_std=config.squeeze_bb_std,
        kc_length=config.squeeze_kc_length,
        kc_scalar=config.squeeze_kc_scalar,
        mom_length=config.squeeze_mom_length,
        mom_smooth=config.squeeze_mom_smooth,
    )
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    sqz_col = cols[0]

    series_data = None
    if series_included:
        series_data = {
            "value": _df_column_to_list(result, sqz_col, df.index),
        }
    return {
        "series": series_data if series_included else None,
        "lastValue": _get_col_last_value(result, sqz_col),
    }


def calc_squeeze_pro(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Squeeze Pro."""
    result = _safe_calc(
        ta.squeeze_pro,
        df["high"],
        df["low"],
        df["close"],
        bb_length=config.squeeze_bb_length,
        bb_std=config.squeeze_bb_std,
        kc_length=config.squeeze_kc_length,
        kc_scalar_wide=config.squeeze_kc_scalar,  # Reusing simple squeeze scalar/length or default
    )
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    sqz_col = cols[0]

    series_data = None
    if series_included:
        series_data = {
            "value": _df_column_to_list(result, sqz_col, df.index),
        }
    return {
        "series": series_data if series_included else None,
        "lastValue": _get_col_last_value(result, sqz_col),
    }


def calc_stc(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Schaff Trend Cycle."""
    result = _safe_calc(
        ta.stc,
        df["close"],
        tclength=config.stc_tclength,
        fast=config.stc_fast,
        slow=config.stc_slow,
        factor=config.stc_factor,
    )
    if result is None or result.empty:
        # STC sometimes returns Series if only one column (default), but can be DataFrame
        return {"series": None, "lastValue": None}

    if isinstance(result, pd.Series):
        return {
            "series": (
                {"value": _series_to_list(result, df.index)}
                if series_included
                else None
            ),
            "lastValue": _get_last_value(result),
        }

    cols = result.columns.tolist()
    stc_col = cols[0]

    series_data = None
    if series_included:
        series_data = {
            "value": _df_column_to_list(result, stc_col, df.index),
        }
    return {
        "series": series_data if series_included else None,
        "lastValue": _get_col_last_value(result, stc_col),
    }


def calc_trix(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate TRIX."""
    result = _safe_calc(
        ta.trix, df["close"], length=config.trix_length, signal=config.trix_signal
    )
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    trix_col = cols[0]
    signal_col = cols[1]

    last_value = {
        "trix": _get_col_last_value(result, trix_col),
        "signal": _get_col_last_value(result, signal_col),
    }

    series_data = None
    if series_included:
        series_data = {
            "trix": _df_column_to_list(result, trix_col, df.index),
            "signal": _df_column_to_list(result, signal_col, df.index),
        }
    return {"series": series_data, "lastValue": last_value}


def calc_tsi(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate True Strength Index."""
    result = _safe_calc(
        ta.tsi,
        df["close"],
        fast=config.tsi_fast,
        slow=config.tsi_slow,
        signal=config.tsi_signal,
    )
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    tsi_col = cols[0]
    signal_col = cols[1] if len(cols) > 1 else cols[0]

    last_value = {
        "tsi": _get_col_last_value(result, tsi_col),
        "signal": _get_col_last_value(result, signal_col),
    }

    series_data = None
    if series_included:
        series_data = {
            "tsi": _df_column_to_list(result, tsi_col, df.index),
            "signal": _df_column_to_list(result, signal_col, df.index),
        }
    return {"series": series_data, "lastValue": last_value}


def calc_uo(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Ultimate Oscillator."""
    series = _safe_calc(
        ta.uo,
        df["high"],
        df["low"],
        df["close"],
        fast=config.uo_fast,
        medium=config.uo_medium,
        slow=config.uo_slow,
    )
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_crsi(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Connors RSI."""
    series = _safe_calc(
        ta.crsi,
        df["close"],
        rsi=config.crsi_rsi,
        streak=config.crsi_streak,
        lookback=config.crsi_lookback,
    )
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_rsx(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Relative Strength Xtra."""
    series = _safe_calc(ta.rsx, df["close"], length=config.rsx_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_tmo(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate True Momentum Oscillator."""
    result = _safe_calc(
        ta.tmo,
        df["close"],
        calc_length=config.tmo_length,
        smooth_length=config.tmo_smooth,
    )
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    main_col = cols[0]
    signal_col = cols[1] if len(cols) > 1 else cols[0]

    last_value = {
        "main": _get_col_last_value(result, main_col),
        "signal": _get_col_last_value(result, signal_col),
    }

    series_data = None
    if series_included:
        series_data = {
            "main": _df_column_to_list(result, main_col, df.index),
            "signal": _df_column_to_list(result, signal_col, df.index),
        }
    return {"series": series_data, "lastValue": last_value}


def calc_stochf(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Stochastic Fast."""
    result = _safe_calc(
        ta.stoch,
        df["high"],
        df["low"],
        df["close"],
        k=config.stoch_k,
        d=config.stoch_d,
        smooth_k=1,  # Fast stochastic has smooth_k=1
    )
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    k_col = cols[0]
    d_col = cols[1] if len(cols) > 1 else cols[0]

    last_value = {
        "k": _get_col_last_value(result, k_col),
        "d": _get_col_last_value(result, d_col),
    }

    series_data = None
    if series_included:
        series_data = {
            "k": _df_column_to_list(result, k_col, df.index),
            "d": _df_column_to_list(result, d_col, df.index),
        }
    return {"series": series_data, "lastValue": last_value}


def calc_macd(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate MACD (line, signal, histogram)."""
    result = _safe_calc(
        ta.macd,
        df["close"],
        fast=config.macd_fast,
        slow=config.macd_slow,
        signal=config.macd_signal,
    )
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    macd_col = cols[0]
    hist_col = cols[1] if len(cols) > 1 else cols[0]
    signal_col = cols[2] if len(cols) > 2 else cols[1] if len(cols) > 1 else cols[0]

    last_value = {
        "line": _get_col_last_value(result, macd_col),
        "signal": _get_col_last_value(result, signal_col),
        "histogram": _get_col_last_value(result, hist_col),
    }

    series_data = None
    if series_included:
        series_data = {
            "line": _df_column_to_list(result, macd_col, df.index),
            "signal": _df_column_to_list(result, signal_col, df.index),
            "histogram": _df_column_to_list(result, hist_col, df.index),
        }

    return {"series": series_data, "lastValue": last_value}


def calc_stoch(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Stochastic Oscillator (%K, %D)."""
    result = _safe_calc(
        ta.stoch,
        df["high"],
        df["low"],
        df["close"],
        k=config.stoch_k,
        d=config.stoch_d,
        smooth_k=config.stoch_smooth_k,
    )
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    k_col = cols[0]
    d_col = cols[1] if len(cols) > 1 else cols[0]

    last_value = {
        "k": _get_col_last_value(result, k_col),
        "d": _get_col_last_value(result, d_col),
    }

    series_data = None
    if series_included:
        series_data = {
            "k": _df_column_to_list(result, k_col, df.index),
            "d": _df_column_to_list(result, d_col, df.index),
        }

    return {"series": series_data, "lastValue": last_value}


def calc_williams(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Williams %R."""
    series = _safe_calc(
        ta.willr, df["high"], df["low"], df["close"], length=config.willr_length
    )
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_cci(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Commodity Channel Index."""
    series = _safe_calc(
        ta.cci, df["high"], df["low"], df["close"], length=config.cci_length
    )
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_roc(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Rate of Change."""
    series = _safe_calc(ta.roc, df["close"], length=config.roc_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


# =============================================================================
# TREND INDICATORS (Pane 0)
# =============================================================================


def calc_adx(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Average Directional Index with +DI and -DI."""
    result = _safe_calc(
        ta.adx, df["high"], df["low"], df["close"], length=config.adx_length
    )
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    adx_col = next((c for c in cols if c.startswith("ADX_")), cols[0])
    dmp_col = next(
        (c for c in cols if c.startswith("DMP_")), cols[1] if len(cols) > 1 else cols[0]
    )
    dmn_col = next(
        (c for c in cols if c.startswith("DMN_")), cols[2] if len(cols) > 2 else cols[0]
    )

    last_value = {
        "adx": _get_col_last_value(result, adx_col),
        "plusDI": _get_col_last_value(result, dmp_col),
        "minusDI": _get_col_last_value(result, dmn_col),
    }

    series_data = None
    if series_included:
        series_data = {
            "adx": _df_column_to_list(result, adx_col, df.index),
            "plusDI": _df_column_to_list(result, dmp_col, df.index),
            "minusDI": _df_column_to_list(result, dmn_col, df.index),
        }

    return {"series": series_data, "lastValue": last_value}


def calc_aroon(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Aroon."""
    result = _safe_calc(ta.aroon, df["high"], df["low"], length=config.aroon_length)
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    down_col = next((c for c in cols if c.startswith("AROOND_")), cols[0])
    up_col = next((c for c in cols if c.startswith("AROONU_")), cols[1])

    last_value = {
        "down": _get_col_last_value(result, down_col),
        "up": _get_col_last_value(result, up_col),
    }

    series_data = None
    if series_included:
        series_data = {
            "down": _df_column_to_list(result, down_col, df.index),
            "up": _df_column_to_list(result, up_col, df.index),
        }
    return {"series": series_data, "lastValue": last_value}


def calc_decay(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Decay."""
    series = _safe_calc(
        ta.decay, df["close"], length=config.decay_length, mode=config.decay_mode
    )
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_dpo(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Detrended Price Oscillator."""
    series = _safe_calc(
        ta.dpo, df["close"], length=config.dpo_length, centered=config.dpo_centered
    )
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_cksp(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Chande Kroll Stop."""
    result = _safe_calc(
        ta.cksp,
        df["high"],
        df["low"],
        df["close"],
        p=config.cksp_p,
        x=config.cksp_x,
        q=config.cksp_q,
    )
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    long_col = next((c for c in cols if c.startswith("CKSPl_")), cols[0])
    short_col = next((c for c in cols if c.startswith("CKSPs_")), cols[1])

    last_value = {
        "long": _get_col_last_value(result, long_col),
        "short": _get_col_last_value(result, short_col),
    }

    series_data = None
    if series_included:
        series_data = {
            "long": _df_column_to_list(result, long_col, df.index),
            "short": _df_column_to_list(result, short_col, df.index),
        }
    return {"series": series_data, "lastValue": last_value}


def calc_psar(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Parabolic SAR."""
    result = _safe_calc(
        ta.psar,
        df["high"],
        df["low"],
        df["close"],
        af0=config.psar_af0,
        af=config.psar_af,
        max_af=config.psar_max_af,
    )
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    # PSARl (long), PSARs (short). Combine them into one series for charting potentially.
    # But let's return them as is, and maybe a combined one if easier.
    long_col = next((c for c in cols if c.startswith("PSARl_")), cols[0])
    short_col = next((c for c in cols if c.startswith("PSARs_")), cols[1])

    # Combined series: take long, if nan take short.
    combined_series = result[long_col].fillna(result[short_col])

    last_value = {
        "psar": _get_last_value(combined_series),
        "long": _get_col_last_value(result, long_col),
        "short": _get_col_last_value(result, short_col),
    }

    series_data = None
    if series_included:
        series_data = {
            "psar": _series_to_list(combined_series, df.index),
            "long": _df_column_to_list(result, long_col, df.index),
            "short": _df_column_to_list(result, short_col, df.index),
        }
    return {"series": series_data, "lastValue": last_value}


def calc_qstick(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate QStick."""
    series = _safe_calc(ta.qstick, df["open"], df["close"], length=config.qstick_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_ttm_trend(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate TTM Trend."""
    series = _safe_calc(
        ta.ttm_trend, df["high"], df["low"], df["close"], length=config.ttm_trend_length
    )
    # Returns a Series of integers/booleans usually.
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_vortex(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Vortex."""
    result = _safe_calc(
        ta.vortex,
        df["high"],
        df["low"],
        df["close"],
        length=config.vortex_length,
    )
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    # VTXP_14, VTXM_14
    pos_col = next((c for c in cols if c.startswith("VTXP_")), cols[0])
    neg_col = next((c for c in cols if c.startswith("VTXM_")), cols[1])

    last_value = {
        "pos": _get_col_last_value(result, pos_col),
        "neg": _get_col_last_value(result, neg_col),
    }

    series_data = None
    if series_included:
        series_data = {
            "pos": _df_column_to_list(result, pos_col, df.index),
            "neg": _df_column_to_list(result, neg_col, df.index),
        }
    return {"series": series_data, "lastValue": last_value}


def calc_alphatrend(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate AlphaTrend."""
    result = _safe_calc(
        ta.alphatrend,
        df["high"],
        df["low"],
        df["close"],
        length=config.alphatrend_length,
    )
    if result is None or (hasattr(result, "empty") and result.empty):
        return {"series": None, "lastValue": None}

    if isinstance(result, pd.DataFrame):
        cols = result.columns.tolist()
        main_col = cols[0]
        series = result[main_col]
    else:
        series = result

    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_amat(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Archer Moving Averages Trends."""
    result = _safe_calc(
        ta.amat,
        df["close"],
        fast=config.amat_fast,
        slow=config.amat_slow,
    )
    if result is None or (hasattr(result, "empty") and result.empty):
        return {"series": None, "lastValue": None}

    if isinstance(result, pd.DataFrame):
        cols = result.columns.tolist()
        trend_col = cols[0]
        series = result[trend_col]
    else:
        series = result

    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_chop(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Choppiness Index."""
    series = _safe_calc(
        ta.chop,
        df["high"],
        df["low"],
        df["close"],
        length=config.chop_length,
    )
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_vhf(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Vertical Horizontal Filter."""
    series = _safe_calc(ta.vhf, df["close"], length=config.vhf_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_ad(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Accumulation/Distribution."""
    series = _safe_calc(ta.ad, df["high"], df["low"], df["close"], df["volume"])
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_adosc(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Accumulation/Distribution Oscillator."""
    series = _safe_calc(
        ta.adosc,
        df["high"],
        df["low"],
        df["close"],
        df["volume"],
        fast=config.adosc_fast,
        slow=config.adosc_slow,
    )
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


# =============================================================================
# VOLUME INDICATORS (Pane 1)
# =============================================================================


def calc_aobv(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Archer On Balance Volume."""
    result = _safe_calc(
        ta.aobv,
        df["close"],
        df["volume"],
        fast=config.aobv_fast,
        slow=config.aobv_slow,
        max_lookback=config.aobv_max_lookback,
        min_lookback=config.aobv_min_lookback,
        mamode=config.aobv_mamode,
    )
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    obv_col = next((c for c in cols if c.startswith("OBV")), cols[0])
    # AOBV returns many columns, we focus on main ones
    min_col = next(
        (c for c in cols if c.startswith("OBV_min")),
        cols[1] if len(cols) > 1 else cols[0],
    )
    max_col = next(
        (c for c in cols if c.startswith("OBV_max")),
        cols[2] if len(cols) > 2 else cols[0],
    )
    ema_col = next(
        (c for c in cols if c.startswith("OBV_EMA")),
        cols[3] if len(cols) > 3 else cols[0],
    )

    last_value = {
        "obv": _get_col_last_value(result, obv_col),
        "min": _get_col_last_value(result, min_col),
        "max": _get_col_last_value(result, max_col),
        "ema": _get_col_last_value(result, ema_col),
    }

    series_data = None
    if series_included:
        series_data = {
            "obv": _df_column_to_list(result, obv_col, df.index),
            "min": _df_column_to_list(result, min_col, df.index),
            "max": _df_column_to_list(result, max_col, df.index),
            "ema": _df_column_to_list(result, ema_col, df.index),
        }
    return {"series": series_data, "lastValue": last_value}


def calc_efi(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Elder's Force Index."""
    series = _safe_calc(ta.efi, df["close"], df["volume"], length=config.efi_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_eom(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Ease of Movement."""
    series = _safe_calc(
        ta.eom,
        df["high"],
        df["low"],
        df["close"],
        df["volume"],
        length=config.eom_length,
    )
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_kvo(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Klinger Volume Oscillator."""
    result = _safe_calc(
        ta.kvo,
        df["high"],
        df["low"],
        df["close"],
        df["volume"],
        fast=config.kvo_fast,
        slow=config.kvo_slow,
        signal=config.kvo_signal,
    )
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    kvo_col = cols[0]
    signal_col = cols[1]

    last_value = {
        "kvo": _get_col_last_value(result, kvo_col),
        "signal": _get_col_last_value(result, signal_col),
    }

    series_data = None
    if series_included:
        series_data = {
            "kvo": _df_column_to_list(result, kvo_col, df.index),
            "signalLine": _df_column_to_list(result, signal_col, df.index),
        }
    return {"series": series_data, "lastValue": last_value}


def calc_nvi(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Negative Volume Index."""
    series = _safe_calc(ta.nvi, df["close"], df["volume"], length=config.nvi_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_pvi(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Positive Volume Index."""
    series = _safe_calc(ta.pvi, df["close"], df["volume"], length=config.pvi_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_pvol(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Price-Volume."""
    series = _safe_calc(ta.pvol, df["close"], df["volume"])
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_pvr(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Price Volume Rank."""
    series = _safe_calc(ta.pvr, df["close"], df["volume"])
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_pvt(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Price Volume Trend."""
    series = _safe_calc(ta.pvt, df["close"], df["volume"])
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_vol_sma(
    df: pd.DataFrame,
    config: IndicatorConfig,
    series_included: bool,
    length: int = None,
) -> Dict[str, Any]:
    """Calculate Volume Simple Moving Average."""
    if length is None:
        length = config.ma_lengths[2] if len(config.ma_lengths) > 2 else 20
    series = _safe_calc(ta.sma, df["volume"], length=length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_obv(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate On Balance Volume."""
    series = _safe_calc(ta.obv, df["close"], df["volume"])
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_mfi(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Money Flow Index."""
    series = _safe_calc(
        ta.mfi,
        df["high"],
        df["low"],
        df["close"],
        df["volume"],
        length=config.mfi_length,
    )
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_cmf(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Chaikin Money Flow."""
    series = _safe_calc(
        ta.cmf,
        df["high"],
        df["low"],
        df["close"],
        df["volume"],
        length=config.cmf_length,
    )
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_tsv(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Time Segmented Value."""
    series = _safe_calc(
        ta.tsv,
        df["close"],
        df["volume"],
        length=config.tsv_length,
    )
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_vwma(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Volume Weighted Moving Average."""
    series = _safe_calc(
        ta.vwma,
        df["close"],
        df["volume"],
        length=config.vwma_length,
    )
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


# =============================================================================
# STATISTICS INDICATORS (Pane 1 or 2)
# =============================================================================


def calc_kurtosis(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Kurtosis."""
    series = _safe_calc(ta.kurtosis, df["close"], length=config.kurtosis_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_mad(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Mean Absolute Deviation."""
    series = _safe_calc(ta.mad, df["close"], length=config.mad_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_median(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Median."""
    series = _safe_calc(ta.median, df["close"], length=config.median_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_quantile(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Quantile."""
    series = _safe_calc(
        ta.quantile, df["close"], length=config.quantile_length, q=config.quantile_q
    )
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_skew(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Skew."""
    series = _safe_calc(ta.skew, df["close"], length=config.skew_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_stdev(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Standard Deviation."""
    series = _safe_calc(ta.stdev, df["close"], length=config.stdev_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_variance(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Variance."""
    series = _safe_calc(ta.variance, df["close"], length=config.variance_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_zscore(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Z-Score."""
    series = _safe_calc(ta.zscore, df["close"], length=config.zscore_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_entropy(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Entropy."""
    series = _safe_calc(ta.entropy, df["close"], length=config.entropy_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_tos_stdevall(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate TOS Standard Deviation All."""
    result = _safe_calc(ta.tos_stdevall, df["close"], length=config.tos_stdevall_length)
    if result is None or result.empty:
        return {"series": None, "lastValue": None}

    cols = result.columns.tolist()
    lr_col = next((c for c in cols if c.startswith("TOS_STDEVALL_LR_")), cols[0])
    upper_col = next(
        (c for c in cols if "_U_" in c or "UPPER" in c.upper()),
        cols[1] if len(cols) > 1 else cols[0],
    )
    lower_col = next(
        (c for c in cols if "_L_" in c or "LOWER" in c.upper()),
        cols[2] if len(cols) > 2 else cols[0],
    )

    last_value = {
        "lr": _get_col_last_value(result, lr_col),
        "upper": _get_col_last_value(result, upper_col),
        "lower": _get_col_last_value(result, lower_col),
    }

    series_data = None
    if series_included:
        series_data = {
            "lr": _df_column_to_list(result, lr_col, df.index),
            "upper": _df_column_to_list(result, upper_col, df.index),
            "lower": _df_column_to_list(result, lower_col, df.index),
        }
    return {"series": series_data, "lastValue": last_value}


# =============================================================================
# CYCLE INDICATORS (Pane 2)
# =============================================================================


def calc_ebsw(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Even Better Sine Wave."""
    series = _safe_calc(
        ta.ebsw, df["close"], length=config.ebsw_length, bars=config.ebsw_bars
    )
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_reflex(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Reflex Indicator."""
    series = _safe_calc(ta.reflex, df["close"], length=config.reflex_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_trendflex(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Trendflex Indicator."""
    series = _safe_calc(ta.trendflex, df["close"], length=config.trendflex_length)
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


# =============================================================================
# PERFORMANCE INDICATORS (Pane 2)
# =============================================================================


def calc_log_return(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Log Return."""
    series = _safe_calc(
        ta.log_return,
        df["close"],
        length=config.log_return_length,
        cumulative=config.log_return_cumulative,
    )
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


def calc_percent_return(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Percent Return."""
    series = _safe_calc(
        ta.percent_return,
        df["close"],
        length=config.percent_return_length,
        cumulative=config.percent_return_cumulative,
    )
    return {
        "series": (
            {"value": _series_to_list(series, df.index)} if series_included else None
        ),
        "lastValue": _get_last_value(series),
    }


# =============================================================================
# SUPPORT/RESISTANCE (Pane 0 - Price Lines)
# =============================================================================


def calc_pivot(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Classic Pivot Points."""
    high = _get_last_value(df["high"])
    low = _get_last_value(df["low"])
    close = _get_last_value(df["close"])

    if high is None or low is None or close is None:
        return {"series": None, "lastValue": None}

    pivot = (high + low + close) / 3
    r1 = 2 * pivot - low
    s1 = 2 * pivot - high
    r2 = pivot + (high - low)
    s2 = pivot - (high - low)
    r3 = high + 2 * (pivot - low)
    s3 = low - 2 * (high - pivot)

    last_value = {
        "pivot": round(pivot, 2),
        "r1": round(r1, 2),
        "r2": round(r2, 2),
        "r3": round(r3, 2),
        "s1": round(s1, 2),
        "s2": round(s2, 2),
        "s3": round(s3, 2),
    }

    return {
        "series": (last_value if series_included else None),
        "lastValue": last_value,
    }


def calc_fib(
    df: pd.DataFrame, config: IndicatorConfig, series_included: bool
) -> Dict[str, Any]:
    """Calculate Fibonacci Retracement Levels."""
    if df.empty:
        return {"series": None, "lastValue": None}

    lookback = config.fib_lookback_short
    # Ensure we have enough data
    if len(df) < 1:
        return {"series": None, "lastValue": None}

    high = float(df["high"].tail(lookback).max())
    low = float(df["low"].tail(lookback).min())
    diff = high - low

    last_value = {
        "level_0": round(high, 2),
        "level_236": round(high - diff * 0.236, 2),
        "level_382": round(high - diff * 0.382, 2),
        "level_500": round(high - diff * 0.5, 2),
        "level_618": round(high - diff * 0.618, 2),
        "level_786": round(high - diff * 0.786, 2),
        "level_100": round(low, 2),
    }

    return {
        "series": (last_value if series_included else None),
        "lastValue": last_value,
    }


# =============================================================================
# MAIN API FUNCTIONS
# =============================================================================


def calculate_indicator(
    df: pd.DataFrame,
    indicator_key: str,
    config: IndicatorConfig = None,
    series_included: bool = True,
) -> Dict[str, Any]:
    """
    Calculate a single indicator with optional series data.

    Args:
        df: DataFrame with OHLCV data (columns: open, high, low, close, volume)
        indicator_key: Indicator key to calculate (e.g., "rsi", "macd")
        config: Optional IndicatorConfig instance
        series_included: If True, include series data; if False, only lastValue

    Returns:
        Dictionary with:
        - series: { values: [] } for single-series, { upper: [], lower: [], ... } for multi-series, or None
        - lastValue: { ... } or single value
        - colors: { ... }
    """
    if config is None:
        config = DEFAULT_CONFIG

    if df.empty:
        return {"series": None, "lastValue": None, "error": "No data available"}

    if indicator_key not in INDICATOR_REGISTRY:
        return {
            "series": None,
            "lastValue": None,
            "error": f"Unknown indicator: {indicator_key}",
        }

    try:
        ind_info = INDICATOR_REGISTRY[indicator_key]
        ind_data = ind_info["func"](df, config, series_included)
        # Get styling from DEFAULT_STYLING - use base key (e.g. 'ma' from 'ma_20', 'vol_sma' from 'vol_sma_20')
        base_key = "_".join(indicator_key.split("_")[:-1])
        styling = (
            DEFAULT_STYLING.get(indicator_key) or DEFAULT_STYLING.get(base_key) or {}
        )
        return {
            **ind_data,
            "label": ind_info["label"],
            "description": ind_info["description"],
            "category": ind_info["category"],
            "order": ind_info["order"],
            "pane": styling.get("pane", 0),
            "colors": styling.get("colors", {}),
            "lineStyles": styling.get("lineStyles", {}),
            "priceLines": styling.get("priceLines", {}),
        }
    except Exception as e:
        return {"series": None, "lastValue": None, "error": str(e)}


def calculate_indicators(
    df: pd.DataFrame,
    indicators: List[str],
    config: IndicatorConfig = None,
    series_included: bool = True,
) -> Dict[str, Any]:
    """
    Calculate multiple indicators with optional series data.

    Args:
        df: DataFrame with OHLCV data (columns: open, high, low, close, volume)
        indicators: List of indicator keys to calculate (e.g., ["ma", "rsi", "macd"])
        config: Optional IndicatorConfig instance
        series_included: If True, include series data; if False, only lastValue

    Returns:
        Dictionary with calculated indicator data:
        {
            "indicator_key": {
                "series": { ... } | None,
                "lastValue": { ... },
                "label": str,
                "category": str,
                "pane": int,
                "colors": dict,
                "priceLines": dict,
            },
            ...
        }
    """
    if config is None:
        config = DEFAULT_CONFIG

    if df.empty:
        return {"error": "No data available"}

    result = {}

    for ind_key in indicators:
        result[ind_key] = calculate_indicator(df, ind_key, config, series_included)

    return result


def get_available_indicators() -> List[Dict[str, Any]]:
    """Return list of available indicators with their metadata."""
    result = []
    for key, info in INDICATOR_REGISTRY.items():
        # Get styling from DEFAULT_STYLING - use base key (e.g. 'ma' from 'ma_20', 'vol_sma' from 'vol_sma_20')
        base_key = "_".join(key.split("_")[:-1])
        styling = DEFAULT_STYLING.get(key) or DEFAULT_STYLING.get(base_key) or {}
        result.append(
            {
                "key": key,
                "label": info["label"],
                "description": info["description"],
                "category": info["category"],
                "order": info["order"],
                "pane": styling.get("pane", 0),
                "colors": styling.get("colors", {}),
                "lineStyles": styling.get("lineStyles", {}),
                "priceLines": styling.get("priceLines", {}),
            }
        )
    return result


def init_indicators():
    """
    Initialize and register all indicators depending on configuration.
    This replaces static decorators to allow dynamic configuration.
    """
    # Moving Averages (With multiple lengths) - Most popular indicators first
    for idx, length in enumerate(DEFAULT_CONFIG.ma_lengths):
        register_indicator(
            f"ma_{length}",
            f"SMA({length})",
            f"Đường trung bình động đơn giản {length} phiên",
            "Đường trung bình",
            order=1 + idx,
        )(partial(calc_ma, length=length))
        register_indicator(
            f"ema_{length}",
            f"EMA({length})",
            f"Đường trung bình động hàm mũ {length} phiên",
            "Đường trung bình",
            order=10 + idx,
        )(partial(calc_ema, length=length))
        register_indicator(
            f"vol_sma_{length}",
            f"Vol SMA({length})",
            f"Trung bình động khối lượng {length} phiên",
            "Khối lượng",
            order=455 + idx,
        )(partial(calc_vol_sma, length=length))

    # Other Moving Average Indicators
    register_indicator(
        "vwap",
        "VWAP",
        "Giá trung bình theo khối lượng giao dịch",
        "Đường trung bình",
        order=20,
    )(calc_vwap)
    register_indicator(
        "bb",
        f"Bollinger Bands({DEFAULT_CONFIG.bbands_length},{DEFAULT_CONFIG.bbands_std})",
        "Dải băng Bollinger đo độ biến động giá",
        "Biến động",
        order=21,
    )(calc_bb)
    register_indicator(
        "wma",
        f"WMA({DEFAULT_CONFIG.wma_length})",
        "Đường trung bình có trọng số",
        "Đường trung bình",
        order=30,
    )(calc_wma)
    register_indicator(
        "dema",
        f"DEMA({DEFAULT_CONFIG.dema_length})",
        "Đường trung bình hàm mũ kép",
        "Đường trung bình",
        order=31,
    )(calc_dema)
    register_indicator(
        "tema",
        f"TEMA({DEFAULT_CONFIG.tema_length})",
        "Đường trung bình hàm mũ ba",
        "Đường trung bình",
        order=32,
    )(calc_tema)
    register_indicator(
        "hma",
        f"HMA({DEFAULT_CONFIG.hma_length})",
        "Đường trung bình Hull",
        "Đường trung bình",
        order=33,
    )(calc_hma)
    register_indicator(
        "kama",
        f"KAMA({DEFAULT_CONFIG.kama_length})",
        "Đường trung bình thích ứng Kaufman",
        "Đường trung bình",
        order=34,
    )(calc_kama)
    register_indicator(
        "zlma",
        f"ZLMA({DEFAULT_CONFIG.zlma_length})",
        "Đường trung bình không độ trễ",
        "Đường trung bình",
        order=35,
    )(calc_zlma)
    register_indicator(
        "t3",
        f"T3({DEFAULT_CONFIG.t3_length})",
        "Đường trung bình T3 Tillson",
        "Đường trung bình",
        order=36,
    )(calc_t3)
    register_indicator(
        "trima",
        f"TRIMA({DEFAULT_CONFIG.trima_length})",
        "Đường trung bình tam giác",
        "Đường trung bình",
        order=37,
    )(calc_trima)
    register_indicator(
        "vidya",
        f"VIDYA({DEFAULT_CONFIG.vidya_length})",
        "Đường trung bình động biến đổi",
        "Đường trung bình",
        order=38,
    )(calc_vidya)
    register_indicator(
        "fwma",
        f"FWMA({DEFAULT_CONFIG.fwma_length})",
        "Đường trung bình Fibonacci",
        "Đường trung bình",
        order=39,
    )(calc_fwma)
    register_indicator(
        "pwma",
        f"PWMA({DEFAULT_CONFIG.pwma_length})",
        "Đường trung bình Pascal",
        "Đường trung bình",
        order=40,
    )(calc_pwma)
    register_indicator(
        "swma",
        f"SWMA({DEFAULT_CONFIG.swma_length})",
        "Đường trung bình đối xứng",
        "Đường trung bình",
        order=41,
    )(calc_swma)
    register_indicator(
        "sinwma",
        f"SINWMA({DEFAULT_CONFIG.sinwma_length})",
        "Đường trung bình sin",
        "Đường trung bình",
        order=42,
    )(calc_sinwma)
    register_indicator(
        "alma",
        f"ALMA({DEFAULT_CONFIG.alma_length})",
        "Đường trung bình Arnaud Legoux",
        "Đường trung bình",
        order=43,
    )(calc_alma)
    register_indicator(
        "mcgd",
        f"MCGD({DEFAULT_CONFIG.mcgd_length})",
        "Đường trung bình McGinley",
        "Đường trung bình",
        order=44,
    )(calc_mcgd)
    register_indicator(
        "jma",
        f"JMA({DEFAULT_CONFIG.jma_length})",
        "Đường trung bình Jurik",
        "Đường trung bình",
        order=45,
    )(calc_jma)
    register_indicator(
        "hl2",
        "HL2",
        "Trung bình giá cao và thấp",
        "Đường trung bình",
        order=50,
    )(calc_hl2)
    register_indicator(
        "hlc3",
        "HLC3",
        "Giá điển hình (trung bình cao, thấp, đóng)",
        "Đường trung bình",
        order=51,
    )(calc_hlc3)
    register_indicator(
        "ohlc4",
        "OHLC4",
        "Trung bình giá mở, cao, thấp, đóng",
        "Đường trung bình",
        order=52,
    )(calc_ohlc4)
    register_indicator(
        "wcp",
        "WCP",
        "Giá đóng cửa có trọng số",
        "Đường trung bình",
        order=53,
    )(calc_wcp)
    register_indicator(
        "midpoint",
        f"Midpoint({DEFAULT_CONFIG.midpoint_length})",
        "Điểm giữa của giá",
        "Đường trung bình",
        order=54,
    )(calc_midpoint)
    register_indicator(
        "midprice",
        f"Midprice({DEFAULT_CONFIG.midprice_length})",
        "Giá trung bình của cao và thấp",
        "Đường trung bình",
        order=55,
    )(calc_midprice)
    register_indicator(
        "hilo",
        f"HiLo({DEFAULT_CONFIG.hilo_high_length},{DEFAULT_CONFIG.hilo_low_length})",
        "Kênh giá cao thấp",
        "Xu hướng",
        order=56,
    )(calc_hilo)
    register_indicator(
        "alligator",
        "Alligator",
        "Chỉ báo cá sấu Williams",
        "Xu hướng",
        order=57,
    )(calc_alligator)
    register_indicator(
        "linreg",
        f"Linear Regression({DEFAULT_CONFIG.linreg_length})",
        "Đường hồi quy tuyến tính",
        "Đường trung bình",
        order=58,
    )(calc_linreg)
    register_indicator(
        "ht_trendline",
        "HT Trendline",
        "Đường xu hướng Hilbert Transform",
        "Đường trung bình",
        order=59,
    )(calc_ht_trendline)
    register_indicator(
        "mama",
        "MAMA",
        "Đường trung bình MESA thích ứng",
        "Đường trung bình",
        order=60,
    )(calc_mama)

    # Volatility Indicators
    register_indicator(
        "donchian",
        f"Donchian({DEFAULT_CONFIG.donchian_lower_length},{DEFAULT_CONFIG.donchian_upper_length})",
        "Kênh Donchian",
        "Biến động",
        order=100,
    )(calc_donchian)
    register_indicator(
        "kc",
        f"Keltner Channels({DEFAULT_CONFIG.kc_length})",
        "Kênh Keltner",
        "Biến động",
        order=62,
    )(calc_kc)
    register_indicator(
        "atr",
        f"ATR({DEFAULT_CONFIG.atr_length})",
        "Phạm vi thực trung bình đo biến động",
        "Biến động",
        order=101,
    )(calc_atr)
    register_indicator(
        "natr",
        f"NATR({DEFAULT_CONFIG.natr_length})",
        "Phạm vi thực trung bình chuẩn hóa",
        "Biến động",
        order=102,
    )(calc_natr)
    register_indicator(
        "true_range",
        "True Range",
        "Phạm vi thực của giá",
        "Biến động",
        order=103,
    )(calc_true_range)
    register_indicator(
        "pdist",
        "Price Distance",
        "Khoảng cách giá",
        "Biến động",
        order=110,
    )(calc_pdist)
    register_indicator(
        "rvi",
        f"RVI({DEFAULT_CONFIG.rvi_length})",
        "Chỉ số biến động tương đối",
        "Biến động",
        order=111,
    )(calc_rvi)
    register_indicator(
        "thermo",
        f"Thermo({DEFAULT_CONFIG.thermo_length})",
        "Nhiệt kế thị trường Elder",
        "Biến động",
        order=112,
    )(calc_thermo)
    register_indicator(
        "ui",
        f"Ulcer Index({DEFAULT_CONFIG.ui_length})",
        "Chỉ số Ulcer đo rủi ro giảm giá",
        "Biến động",
        order=113,
    )(calc_ui)
    register_indicator(
        "aberration",
        f"Aberration({DEFAULT_CONFIG.aberration_length})",
        "Chỉ báo độ lệch giá",
        "Biến động",
        order=114,
    )(calc_aberration)
    register_indicator(
        "accbands",
        f"Acceleration Bands({DEFAULT_CONFIG.accbands_length})",
        "Dải gia tốc giá",
        "Biến động",
        order=115,
    )(calc_accbands)

    # Momentum Indicators - Most popular first
    register_indicator(
        "rsi",
        f"RSI({DEFAULT_CONFIG.rsi_length})",
        "Chỉ số sức mạnh tương đối",
        "Động lượng",
        order=200,
    )(calc_rsi)
    register_indicator(
        "rsi_fast",
        f"RSI Fast({DEFAULT_CONFIG.rsi_fast_length})",
        "RSI nhanh ngắn hạn",
        "Động lượng",
        order=201,
    )(calc_rsi_fast)
    register_indicator(
        "macd",
        f"MACD({DEFAULT_CONFIG.macd_fast},{DEFAULT_CONFIG.macd_slow},{DEFAULT_CONFIG.macd_signal})",
        "Đường MACD phân kỳ hội tụ trung bình động",
        "Động lượng",
        order=210,
    )(calc_macd)
    register_indicator(
        "stoch",
        f"Stochastic({DEFAULT_CONFIG.stoch_k},{DEFAULT_CONFIG.stoch_d},{DEFAULT_CONFIG.stoch_smooth_k})",
        "Dao động ngẫu nhiên Stochastic",
        "Động lượng",
        order=220,
    )(calc_stoch)
    register_indicator(
        "stochf",
        f"Stoch Fast({DEFAULT_CONFIG.stoch_k},{DEFAULT_CONFIG.stoch_d})",
        "Stochastic nhanh",
        "Động lượng",
        order=221,
    )(calc_stochf)
    register_indicator(
        "stochrsi",
        f"StochRSI({DEFAULT_CONFIG.stochrsi_length},{DEFAULT_CONFIG.stochrsi_k},{DEFAULT_CONFIG.stochrsi_d})",
        "RSI ngẫu nhiên",
        "Động lượng",
        order=222,
    )(calc_stochrsi)
    register_indicator(
        "williams",
        f"Williams %R({DEFAULT_CONFIG.willr_length})",
        "Chỉ số Williams %R",
        "Động lượng",
        order=230,
    )(calc_williams)
    register_indicator(
        "cci",
        f"CCI({DEFAULT_CONFIG.cci_length})",
        "Chỉ số kênh hàng hóa",
        "Động lượng",
        order=231,
    )(calc_cci)
    register_indicator(
        "roc",
        f"ROC({DEFAULT_CONFIG.roc_length})",
        "Tỷ lệ thay đổi giá",
        "Động lượng",
        order=232,
    )(calc_roc)
    register_indicator(
        "mom",
        f"Momentum({DEFAULT_CONFIG.mom_length})",
        "Động lượng giá",
        "Động lượng",
        order=233,
    )(calc_mom)
    register_indicator(
        "ao",
        f"Awesome Oscillator({DEFAULT_CONFIG.ao_fast},{DEFAULT_CONFIG.ao_slow})",
        "Dao động tuyệt vời Bill Williams",
        "Động lượng",
        order=240,
    )(calc_ao)
    register_indicator(
        "apo",
        f"APO({DEFAULT_CONFIG.apo_fast},{DEFAULT_CONFIG.apo_slow})",
        "Dao động giá tuyệt đối",
        "Động lượng",
        order=241,
    )(calc_apo)
    register_indicator(
        "ppo",
        f"PPO({DEFAULT_CONFIG.ppo_fast},{DEFAULT_CONFIG.ppo_slow},{DEFAULT_CONFIG.ppo_signal})",
        "Dao động giá phần trăm",
        "Động lượng",
        order=242,
    )(calc_ppo)
    register_indicator(
        "bias",
        f"Bias({DEFAULT_CONFIG.bias_length})",
        "Độ lệch so với trung bình động",
        "Động lượng",
        order=250,
    )(calc_bias)
    register_indicator(
        "bop",
        "BOP",
        "Cán cân sức mạnh mua bán",
        "Động lượng",
        order=251,
    )(calc_bop)
    register_indicator(
        "brar",
        f"BRAR({DEFAULT_CONFIG.brar_length})",
        "Chỉ số sức mạnh BR AR",
        "Động lượng",
        order=252,
    )(calc_brar)
    register_indicator(
        "cfo",
        f"CFO({DEFAULT_CONFIG.cfo_length})",
        "Dao động Chande Forecast",
        "Động lượng",
        order=260,
    )(calc_cfo)
    register_indicator(
        "cg",
        f"CG({DEFAULT_CONFIG.cg_length})",
        "Chỉ số trọng tâm giá",
        "Động lượng",
        order=261,
    )(calc_cg)
    register_indicator(
        "cmo",
        f"CMO({DEFAULT_CONFIG.cmo_length})",
        "Dao động Chande Momentum",
        "Động lượng",
        order=262,
    )(calc_cmo)
    register_indicator(
        "coppock",
        f"Coppock({DEFAULT_CONFIG.coppock_length},{DEFAULT_CONFIG.coppock_fast},{DEFAULT_CONFIG.coppock_slow})",
        "Đường cong Coppock",
        "Động lượng",
        order=263,
    )(calc_coppock)
    register_indicator(
        "cti",
        f"CTI({DEFAULT_CONFIG.cti_length})",
        "Chỉ số xu hướng tương quan",
        "Động lượng",
        order=264,
    )(calc_cti)
    register_indicator(
        "er",
        f"Efficiency Ratio({DEFAULT_CONFIG.er_length})",
        "Tỷ lệ hiệu quả Kaufman",
        "Động lượng",
        order=265,
    )(calc_er)
    register_indicator(
        "eri",
        f"ERI({DEFAULT_CONFIG.eri_length})",
        "Chỉ số Elder Ray",
        "Động lượng",
        order=266,
    )(calc_eri)
    register_indicator(
        "fisher",
        f"Fisher Transform({DEFAULT_CONFIG.fisher_length})",
        "Biến đổi Fisher",
        "Động lượng",
        order=267,
    )(calc_fisher)
    register_indicator(
        "inertia",
        f"Inertia({DEFAULT_CONFIG.inertia_length})",
        "Chỉ số quán tính",
        "Động lượng",
        order=268,
    )(calc_inertia)
    register_indicator(
        "kdj",
        f"KDJ({DEFAULT_CONFIG.kdj_length},{DEFAULT_CONFIG.kdj_signal})",
        "Chỉ số KDJ",
        "Động lượng",
        order=269,
    )(calc_kdj)
    register_indicator(
        "kst",
        "KST",
        "Chỉ số Know Sure Thing",
        "Động lượng",
        order=270,
    )(calc_kst)
    register_indicator(
        "pgo",
        f"PGO({DEFAULT_CONFIG.pgo_length})",
        "Dao động Pretty Good",
        "Động lượng",
        order=271,
    )(calc_pgo)
    register_indicator(
        "psl",
        f"PSL({DEFAULT_CONFIG.psl_length})",
        "Đường tâm lý thị trường",
        "Động lượng",
        order=272,
    )(calc_psl)
    register_indicator(
        "qqe",
        f"QQE({DEFAULT_CONFIG.qqe_length})",
        "Ước lượng định lượng nhanh",
        "Động lượng",
        order=273,
    )(calc_qqe)
    register_indicator(
        "rvgi",
        f"RVGI({DEFAULT_CONFIG.rvgi_length})",
        "Chỉ số sức sống tương đối",
        "Động lượng",
        order=274,
    )(calc_rvgi)
    register_indicator(
        "slope",
        f"Slope({DEFAULT_CONFIG.slope_length})",
        "Độ dốc của đường hồi quy",
        "Động lượng",
        order=275,
    )(calc_slope)
    register_indicator(
        "smi",
        f"SMI({DEFAULT_CONFIG.smi_fast},{DEFAULT_CONFIG.smi_slow},{DEFAULT_CONFIG.smi_signal})",
        "Chỉ số động lượng Stochastic",
        "Động lượng",
        order=276,
    )(calc_smi)
    register_indicator(
        "squeeze_pro",
        f"Squeeze Pro({DEFAULT_CONFIG.squeeze_bb_length},{DEFAULT_CONFIG.squeeze_kc_length})",
        "Squeeze Pro nâng cao",
        "Động lượng",
        order=277,
    )(calc_squeeze_pro)
    register_indicator(
        "stc",
        f"STC({DEFAULT_CONFIG.stc_fast},{DEFAULT_CONFIG.stc_slow})",
        "Đường chuyển đổi Schaff",
        "Động lượng",
        order=278,
    )(calc_stc)
    register_indicator(
        "trix",
        f"TRIX({DEFAULT_CONFIG.trix_length})",
        "TRIX ba lần làm mịn hàm mũ",
        "Động lượng",
        order=279,
    )(calc_trix)
    register_indicator(
        "tsi",
        f"TSI({DEFAULT_CONFIG.tsi_fast},{DEFAULT_CONFIG.tsi_slow})",
        "Chỉ số sức mạnh thực sự",
        "Động lượng",
        order=280,
    )(calc_tsi)
    register_indicator(
        "uo",
        "UO",
        "Dao động Ultimate",
        "Động lượng",
        order=281,
    )(calc_uo)
    register_indicator(
        "crsi",
        f"CRSI({DEFAULT_CONFIG.crsi_rsi_length},{DEFAULT_CONFIG.crsi_streak_length},{DEFAULT_CONFIG.crsi_rank_length})",
        "RSI Connors",
        "Động lượng",
        order=282,
    )(calc_crsi)
    register_indicator(
        "rsx",
        f"RSX({DEFAULT_CONFIG.rsx_length})",
        "RSX làm mịn",
        "Động lượng",
        order=283,
    )(calc_rsx)
    register_indicator(
        "tmo",
        f"TMO({DEFAULT_CONFIG.tmo_length})",
        "Dao động True Momentum",
        "Động lượng",
        order=284,
    )(calc_tmo)

    # Trend Indicators
    register_indicator(
        "supertrend",
        f"Supertrend({DEFAULT_CONFIG.supertrend_length},{DEFAULT_CONFIG.supertrend_multiplier})",
        "Chỉ báo xu hướng siêu mạnh",
        "Xu hướng",
        order=300,
    )(calc_supertrend)
    register_indicator(
        "ichimoku",
        f"Ichimoku({DEFAULT_CONFIG.ichimoku_tenkan},{DEFAULT_CONFIG.ichimoku_kijun},{DEFAULT_CONFIG.ichimoku_senkou})",
        "Hệ thống Ichimoku Kinko Hyo phân tích xu hướng",
        "Xu hướng",
        order=301,
    )(calc_ichimoku)
    register_indicator(
        "adx",
        f"ADX({DEFAULT_CONFIG.adx_length})",
        "Chỉ số hướng trung bình đo sức mạnh xu hướng",
        "Xu hướng",
        order=302,
    )(calc_adx)
    register_indicator(
        "psar",
        "Parabolic SAR",
        "Điểm dừng và đảo chiều Parabolic",
        "Xu hướng",
        order=303,
    )(calc_psar)
    register_indicator(
        "aroon",
        f"Aroon({DEFAULT_CONFIG.aroon_length})",
        "Chỉ số Aroon xác định xu hướng",
        "Xu hướng",
        order=310,
    )(calc_aroon)
    register_indicator(
        "vortex",
        f"Vortex({DEFAULT_CONFIG.vortex_length})",
        "Chỉ số xoáy Vortex",
        "Xu hướng",
        order=311,
    )(calc_vortex)
    register_indicator(
        "alphatrend",
        f"AlphaTrend({DEFAULT_CONFIG.alphatrend_length})",
        "Chỉ báo xu hướng Alpha",
        "Xu hướng",
        order=312,
    )(calc_alphatrend)
    register_indicator(
        "decay",
        f"Decay({DEFAULT_CONFIG.decay_length})",
        "Chỉ số phân rã xu hướng",
        "Xu hướng",
        order=320,
    )(calc_decay)
    register_indicator(
        "dpo",
        f"DPO({DEFAULT_CONFIG.dpo_length})",
        "Dao động giá loại bỏ xu hướng",
        "Xu hướng",
        order=321,
    )(calc_dpo)
    register_indicator(
        "cksp",
        "Chande Kroll Stop",
        "Điểm dừng lỗ Chande Kroll",
        "Xu hướng",
        order=322,
    )(calc_cksp)
    register_indicator(
        "qstick",
        f"QStick({DEFAULT_CONFIG.qstick_length})",
        "Chỉ số QStick",
        "Xu hướng",
        order=323,
    )(calc_qstick)
    register_indicator(
        "ttm_trend",
        "TTM Trend",
        "Xu hướng TTM",
        "Xu hướng",
        order=324,
    )(calc_ttm_trend)
    register_indicator(
        "amat",
        f"AMAT({DEFAULT_CONFIG.amat_fast},{DEFAULT_CONFIG.amat_slow})",
        "Xu hướng trung bình động Archer",
        "Xu hướng",
        order=325,
    )(calc_amat)
    register_indicator(
        "chop",
        f"CHOP({DEFAULT_CONFIG.chop_length})",
        "Chỉ số Choppiness đo tích lũy",
        "Xu hướng",
        order=326,
    )(calc_chop)
    register_indicator(
        "vhf",
        f"VHF({DEFAULT_CONFIG.vhf_length})",
        "Bộ lọc ngang dọc",
        "Xu hướng",
        order=327,
    )(calc_vhf)

    # Volume Indicators
    register_indicator(
        "obv",
        "OBV",
        "Khối lượng cân bằng",
        "Khối lượng",
        order=400,
    )(calc_obv)
    register_indicator(
        "mfi",
        f"MFI({DEFAULT_CONFIG.mfi_length})",
        "Chỉ số dòng tiền",
        "Khối lượng",
        order=401,
    )(calc_mfi)
    register_indicator(
        "cmf",
        f"CMF({DEFAULT_CONFIG.cmf_length})",
        "Dòng tiền Chaikin",
        "Khối lượng",
        order=402,
    )(calc_cmf)
    register_indicator(
        "ad",
        "A/D",
        "Đường tích lũy/phân phối",
        "Khối lượng",
        order=410,
    )(calc_ad)
    register_indicator(
        "adosc",
        f"A/D Oscillator({DEFAULT_CONFIG.adosc_fast},{DEFAULT_CONFIG.adosc_slow})",
        "Dao động tích lũy/phân phối",
        "Khối lượng",
        order=411,
    )(calc_adosc)
    register_indicator(
        "aobv",
        f"Archer OBV({DEFAULT_CONFIG.aobv_fast},{DEFAULT_CONFIG.aobv_slow})",
        "OBV Archer",
        "Khối lượng",
        order=412,
    )(calc_aobv)
    register_indicator(
        "efi",
        f"EFI({DEFAULT_CONFIG.efi_length})",
        "Chỉ số lực Elder",
        "Khối lượng",
        order=420,
    )(calc_efi)
    register_indicator(
        "eom",
        f"EOM({DEFAULT_CONFIG.eom_length})",
        "Độ dễ di chuyển",
        "Khối lượng",
        order=421,
    )(calc_eom)
    register_indicator(
        "kvo",
        "KVO",
        "Dao động khối lượng Klinger",
        "Khối lượng",
        order=422,
    )(calc_kvo)
    register_indicator(
        "nvi",
        "NVI",
        "Chỉ số khối lượng âm",
        "Khối lượng",
        order=430,
    )(calc_nvi)
    register_indicator(
        "pvi",
        "PVI",
        "Chỉ số khối lượng dương",
        "Khối lượng",
        order=431,
    )(calc_pvi)
    register_indicator(
        "pvol",
        "PVOL",
        "Khối lượng giá",
        "Khối lượng",
        order=432,
    )(calc_pvol)
    register_indicator(
        "pvr",
        "PVR",
        "Tỷ lệ khối lượng giá",
        "Khối lượng",
        order=433,
    )(calc_pvr)
    register_indicator(
        "pvt",
        "PVT",
        "Xu hướng khối lượng giá",
        "Khối lượng",
        order=434,
    )(calc_pvt)
    register_indicator(
        "tsv",
        f"TSV({DEFAULT_CONFIG.tsv_length})",
        "Khối lượng phân đoạn thời gian",
        "Khối lượng",
        order=455,
    )(calc_tsv)
    register_indicator(
        "vwma",
        f"VWMA({DEFAULT_CONFIG.vwma_length})",
        "Trung bình động theo khối lượng",
        "Khối lượng",
        order=456,
    )(calc_vwma)

    # Statistics Indicators
    register_indicator(
        "stdev",
        f"Standard Deviation({DEFAULT_CONFIG.stdev_length})",
        "Độ lệch chuẩn",
        "Thống kê",
        order=500,
    )(calc_stdev)
    register_indicator(
        "variance",
        f"Variance({DEFAULT_CONFIG.variance_length})",
        "Phương sai",
        "Thống kê",
        order=501,
    )(calc_variance)
    register_indicator(
        "zscore",
        f"Z-Score({DEFAULT_CONFIG.zscore_length})",
        "Điểm Z chuẩn hóa",
        "Thống kê",
        order=502,
    )(calc_zscore)
    register_indicator(
        "kurtosis",
        f"Kurtosis({DEFAULT_CONFIG.kurtosis_length})",
        "Độ nhọn phân phối",
        "Thống kê",
        order=510,
    )(calc_kurtosis)
    register_indicator(
        "skew",
        f"Skew({DEFAULT_CONFIG.skew_length})",
        "Độ lệch phân phối",
        "Thống kê",
        order=511,
    )(calc_skew)
    register_indicator(
        "mad",
        f"MAD({DEFAULT_CONFIG.mad_length})",
        "Độ lệch tuyệt đối trung bình",
        "Thống kê",
        order=520,
    )(calc_mad)
    register_indicator(
        "median",
        f"Median({DEFAULT_CONFIG.median_length})",
        "Giá trị trung vị",
        "Thống kê",
        order=521,
    )(calc_median)
    register_indicator(
        "quantile",
        f"Quantile({DEFAULT_CONFIG.quantile_length})",
        "Phân vị",
        "Thống kê",
        order=522,
    )(calc_quantile)
    register_indicator(
        "entropy",
        f"Entropy({DEFAULT_CONFIG.entropy_length})",
        "Entropy thông tin",
        "Thống kê",
        order=523,
    )(calc_entropy)
    register_indicator(
        "tos_stdevall",
        f"TOS StdevAll({DEFAULT_CONFIG.tos_stdevall_length})",
        "Độ lệch chuẩn TOS",
        "Thống kê",
        order=524,
    )(calc_tos_stdevall)

    # Cycle Indicators
    register_indicator(
        "ebsw",
        f"EBSW({DEFAULT_CONFIG.ebsw_length})",
        "Sóng sin tốt hơn",
        "Chu kỳ",
        order=600,
    )(calc_ebsw)
    register_indicator(
        "reflex",
        f"Reflex({DEFAULT_CONFIG.reflex_length})",
        "Chỉ số phản xạ",
        "Chu kỳ",
        order=601,
    )(calc_reflex)
    register_indicator(
        "trendflex",
        f"Trendflex({DEFAULT_CONFIG.trendflex_length})",
        "Chỉ số xu hướng linh hoạt",
        "Chu kỳ",
        order=602,
    )(calc_trendflex)

    # Performance Indicators
    register_indicator(
        "log_return",
        "Log Return",
        "Lợi nhuận logarit",
        "Hiệu suất",
        order=700,
    )(calc_log_return)
    register_indicator(
        "percent_return",
        "Percent Return",
        "Lợi nhuận phần trăm",
        "Hiệu suất",
        order=701,
    )(calc_percent_return)

    # Support/Resistance Indicators
    register_indicator(
        "pivot",
        "Pivot Points",
        "Điểm xoay hỗ trợ kháng cự",
        "Hỗ trợ/Kháng cự",
        order=800,
    )(calc_pivot)
    register_indicator(
        "fib",
        "Fibonacci",
        "Mức thoái lui Fibonacci",
        "Hỗ trợ/Kháng cự",
        order=801,
    )(calc_fib)


# Initialize indicators
init_indicators()
