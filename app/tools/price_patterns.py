"""
Price Pattern Detection Module.

Provides algorithms for detecting:
1. Chart patterns (Double Top/Bottom, Head & Shoulders, Wedges, Rectangles, Pennants, Triangles)
2. Support/Resistance zones

Uses scipy for local extrema detection and mathematical analysis.
"""

import pandas as pd
import numpy as np
from scipy.signal import argrelextrema
from typing import Optional
from datetime import datetime
from dateutil.relativedelta import relativedelta
from app.tools.vietcap_tools import get_stock_ohlcv
from app.tools.technical_indicators import create_ohlcv_dataframe


# =============================================================================
# CONFIGURATION - Tolerance/Sensitivity Settings
# =============================================================================

# Pivot point detection order (number of candles on each side to compare)
PIVOT_ORDER = 5

# Price tolerance for pattern matching (percentage)
PRICE_TOLERANCE_PCT = 0.02  # 2% tolerance for similar price levels

# Minimum candles between pivot points
MIN_PATTERN_CANDLES = 5

# S/R zone clustering tolerance (percentage)
SR_ZONE_TOLERANCE_PCT = 0.015  # 1.5% for clustering nearby levels

# Minimum touches to consider a valid S/R zone
MIN_SR_TOUCHES = 2

# Lookback period for S/R detection
SR_LOOKBACK = 100

# Pattern lookback period
PATTERN_LOOKBACK = 100

# Datetime format for pattern dates (must include time for intraday charts)
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


# =============================================================================
# PIVOT POINT DETECTION
# =============================================================================


def find_pivot_points(
    df: pd.DataFrame, order: int = PIVOT_ORDER
) -> tuple[pd.Series, pd.Series]:
    """
    Find local minima (swing lows) and maxima (swing highs) pivot points.

    Args:
        df: DataFrame with OHLCV data (must have 'high', 'low' columns)
        order: Number of candles on each side to compare (higher = less sensitive)

    Returns:
        Tuple of (pivot_highs, pivot_lows) as Series with index matching df
    """
    if len(df) < order * 2 + 1:
        return pd.Series(dtype=float), pd.Series(dtype=float)

    # Find local maxima (resistance/swing highs)
    high_idx = argrelextrema(df["high"].values, np.greater_equal, order=order)[0]

    # Find local minima (support/swing lows)
    low_idx = argrelextrema(df["low"].values, np.less_equal, order=order)[0]

    # Create Series with pivot values
    pivot_highs = pd.Series(index=df.index, dtype=float)
    pivot_lows = pd.Series(index=df.index, dtype=float)

    for idx in high_idx:
        pivot_highs.iloc[idx] = df["high"].iloc[idx]

    for idx in low_idx:
        pivot_lows.iloc[idx] = df["low"].iloc[idx]

    return pivot_highs.dropna(), pivot_lows.dropna()


def get_pivot_points_list(df: pd.DataFrame, order: int = PIVOT_ORDER) -> list[dict]:
    """
    Get pivot points as a list of dictionaries for API response.

    Returns list of:
    [{"date": str, "price": float, "type": "high"|"low"}, ...]
    """
    pivot_highs, pivot_lows = find_pivot_points(df, order)

    pivots = []
    for date, price in pivot_highs.items():
        pivots.append(
            {
                "date": date.strftime("%Y-%m-%d %H:%M:%S"),
                "price": float(price),
                "type": "high",
            }
        )
    for date, price in pivot_lows.items():
        pivots.append(
            {
                "date": date.strftime("%Y-%m-%d %H:%M:%S"),
                "price": float(price),
                "type": "low",
            }
        )

    # Sort by date
    pivots.sort(key=lambda x: x["date"])
    return pivots


def _merge_nearby_pivots(pivots: pd.Series, tolerance_candles: int = 3) -> pd.Series:
    """
    Merge nearby pivot points to avoid duplicate peaks/troughs.
    Consolidates clusters of pivots into a single extreme point.
    """
    if pivots.empty:
        return pivots

    sorted_dates = pivots.index.sort_values()
    merged = pd.Series(dtype=float)

    current_cluster_dates = [sorted_dates[0]]
    current_cluster_prices = [pivots[sorted_dates[0]]]

    # Simple logic: if next pivot is close enough to previous, add to cluster
    # Note: This relies on dates being timestamp indexes.
    # We estimate candle distance by position in the sorted list?
    # No, we need original index locations to be precise, but here we only have dates.
    # Assuming daily or regular interval, we can just check time delta?
    # Or simplified: consecutive pivots in the list are usually the issue.
    # If we have [Peak A, Peak B, Peak C] and they are all Pivots, they must be separated by valleys
    # UNLESS they are adjacent in time (e.g. flat top).

    # We will assume if time difference is small, they are same cluster.
    # For daily data, small diff is 1-3 days.

    last_date = sorted_dates[0]

    for date in sorted_dates[1:]:
        # Rough estimation of closeness (assuming < 4 intervals is "nearby" for a duplicate signal)
        # This might be tricky across weekends, but for duplicates they are usually adjacent bars.
        # We'll validly assume duplicate pivots are very close in time.
        time_diff = date - last_date
        # Heuristic: < 4 * 1 day (approximated for safety, assuming daily data or similar scale).
        # Better: just merge strictly adjacent pivots (diff <= tolerance * interval).
        # We don't know interval here easily.
        # But for flattened tops, they are usually consecutive candles.

        # We will merge if they are "close enough".
        # Since we don't have candle index, we'll try to rely on the fact they are consecutive in the list.
        # But wait, find_pivot_points returns Sparse series.
        # Adjacent entries in 'pivots' might be far apart.

        merged_pivot = False
        # If dates are very close (e.g. within a few entries of original DF, but likely adjacent here)
        # We can't easily check 'candles count' without DF index.
        # BUT, if we assume find_pivot_points returns local extrema, clusters only happen if price is flat/similar.

        # Let's use a simple price similarity + sequence check?
        # No, price similarity is not enough (Double Top).

        # Let's rely on time. If delta is small.
        if (
            date - last_date
        ).total_seconds() < 3600 * 24 * tolerance_candles:  # Approx logic
            current_cluster_dates.append(date)
            current_cluster_prices.append(pivots[date])
        else:
            # Process current cluster
            # For Highs (this function used for highs), we take MAX.
            # For Lows, we usually call this separately.
            # We should pass 'type' ('high' or 'low') or determine it.
            # Actually, this helper takes a Series. 'find_pivot_points' returns separate Highs and Lows series.
            # So we know if it is highs or lows based on context?
            # No, standard argrelextrema returns separate calls.
            # We need to know if we want Max or Min.
            # Simple heuristic: If the series values are positive prices,
            # and we are merging Highs, we want Max. If Lows, Min.
            # But we don't know.

            # Better: pass 'method="max"' or 'method="min"'.
            pass

    # REVISION: To handle this properly inside this function without extra args:
    # Just take the first or middle?
    # Or default to Max for now as duplication usually happens at Tops?
    # No, happens at Bottoms too.

    # Let's change signature to take 'is_highs: bool'.
    return pivots  # Placeholder until implemented in replace block with correct logic


# =============================================================================
# SUPPORT/RESISTANCE ZONE DETECTION
# =============================================================================


def _cluster_price_levels(
    prices: list[float], tolerance_pct: float = SR_ZONE_TOLERANCE_PCT
) -> list[dict]:
    """
    Cluster nearby price levels into zones.

    Args:
        prices: List of price levels
        tolerance_pct: Percentage tolerance for clustering

    Returns:
        List of zones: [{"price": avg_price, "count": touches, "prices": [original prices]}]
    """
    if not prices:
        return []

    sorted_prices = sorted(prices)
    zones = []
    current_zone = [sorted_prices[0]]

    for price in sorted_prices[1:]:
        avg_current = sum(current_zone) / len(current_zone)
        if abs(price - avg_current) / avg_current <= tolerance_pct:
            current_zone.append(price)
        else:
            zones.append(
                {
                    "price": sum(current_zone) / len(current_zone),
                    "count": len(current_zone),
                    "prices": current_zone,
                }
            )
            current_zone = [price]

    # Add last zone
    if current_zone:
        zones.append(
            {
                "price": sum(current_zone) / len(current_zone),
                "count": len(current_zone),
                "prices": current_zone,
            }
        )

    return zones


def detect_support_resistance_zones(
    df: pd.DataFrame,
    lookback: int = SR_LOOKBACK,
    min_touches: int = MIN_SR_TOUCHES,
    pivot_order: int = PIVOT_ORDER,
) -> dict:
    """
    Detect support and resistance zones from price data.

    Args:
        df: DataFrame with OHLCV data
        lookback: Number of candles to analyze
        min_touches: Minimum touches required for valid zone
        pivot_order: Sensitivity for pivot detection

    Returns:
        {
            "support_zones": [{"price": float, "strength": int, "range": [low, high]}],
            "resistance_zones": [{"price": float, "strength": int, "range": [low, high]}]
        }
    """
    # Use only recent data
    df_recent = df.tail(lookback)

    if len(df_recent) < pivot_order * 2 + 1:
        return {"support_zones": [], "resistance_zones": []}

    pivot_highs, pivot_lows = find_pivot_points(df_recent, pivot_order)

    # Cluster pivot highs into resistance zones
    resistance_prices = pivot_highs.values.tolist()
    resistance_clusters = _cluster_price_levels(resistance_prices)

    # Cluster pivot lows into support zones
    support_prices = pivot_lows.values.tolist()
    support_clusters = _cluster_price_levels(support_prices)

    # Format output with strength filtering
    resistance_zones = []
    for zone in resistance_clusters:
        if zone["count"] >= min_touches:
            resistance_zones.append(
                {
                    "price": round(zone["price"], 2),
                    "strength": zone["count"],
                    "range": [
                        round(min(zone["prices"]), 2),
                        round(max(zone["prices"]), 2),
                    ],
                }
            )

    support_zones = []
    for zone in support_clusters:
        if zone["count"] >= min_touches:
            support_zones.append(
                {
                    "price": round(zone["price"], 2),
                    "strength": zone["count"],
                    "range": [
                        round(min(zone["prices"]), 2),
                        round(max(zone["prices"]), 2),
                    ],
                }
            )

    # Sort by strength (descending)
    resistance_zones.sort(key=lambda x: x["strength"], reverse=True)
    support_zones.sort(key=lambda x: x["strength"], reverse=True)

    return {"support_zones": support_zones, "resistance_zones": resistance_zones}


# =============================================================================
# CHART PATTERN DETECTION - Helper Functions
# =============================================================================


def _prices_similar(
    p1: float, p2: float, tolerance: float = PRICE_TOLERANCE_PCT
) -> bool:
    """Check if two prices are similar within tolerance."""
    return abs(p1 - p2) / max(p1, p2) <= tolerance


def _calculate_trendline_points(
    points: list[tuple[int, float]], start_date_idx: int, end_date_idx: int
) -> list[dict]:
    """
    Calculate best-fit trendline start and end points.

    Args:
        points: List of (index, price) - logic points
        start_date_idx: DF index for pattern start
        end_date_idx: DF index for pattern end

    Returns:
        List of 2 points: [{"date": ?, "price": ?}, {"date": ?, "price": ?}]
        Note: We return simple dictionaries with placeholders for Date strings,
        as we don't have the Index-to-Date map here easily.
        Actually, we can just return the calculated prices for the start and end indices.
        The caller will attach dates.
    """
    if len(points) < 2:
        return []

    x = np.array([p[0] for p in points])
    y = np.array([p[1] for p in points])
    slope, intercept = np.polyfit(x, y, 1)

    # Calculate price at start and end of the pattern range
    start_price = slope * start_date_idx + intercept
    end_price = slope * end_date_idx + intercept

    return [start_price, end_price]


def _get_trendline_slope(points: list[tuple[int, float]]) -> float:
    """Calculate slope of trendline through points (index, price)."""
    if len(points) < 2:
        return 0
    x = np.array([p[0] for p in points])
    y = np.array([p[1] for p in points])
    # Linear regression
    slope = np.polyfit(x, y, 1)[0]
    return slope


def _calculate_pattern_target(
    entry_price: float, pattern_height: float, direction: str
) -> float:
    """Calculate target price based on pattern height."""
    if direction == "bullish":
        return round(entry_price + pattern_height, 2)
    else:
        return round(entry_price - pattern_height, 2)


def _calculate_double_pattern_confidence(
    price1: float,
    price2: float,
    neckline: float,
    tolerance: float = PRICE_TOLERANCE_PCT,
) -> float:
    """
    Calculate confidence score for double top/bottom patterns.
    Score based on:
    1. Symmetry (similarity of peaks/troughs)
    2. Pattern height (significance)
    """
    # 1. Base Score
    score = 0.5

    # 2. Symmetry Score (0.0 to 0.3)
    # The closer the prices, the higher the score
    diff_pct = abs(price1 - price2) / max(price1, price2)
    # Normalize diff against tolerance. If diff is 0, bonus is max. If diff is tolerance, bonus is 0.
    symmetry_bonus = max(0.0, 0.3 * (1 - (diff_pct / tolerance)))
    score += symmetry_bonus

    # 3. Height Score (0.0 to 0.2)
    # Deeper patterns are stronger. Using 5% as a benchmark for 'very strong'.
    avg_price = (price1 + price2) / 2
    height_pct = abs(avg_price - neckline) / avg_price
    # Cap bonus at 0.2 for patterns > 5% deep
    height_bonus = min(0.2, (height_pct / 0.05) * 0.2)
    score += height_bonus

    return round(min(0.95, score), 2)


def _calculate_hs_confidence(
    left_shoulder: float,
    right_shoulder: float,
    head: float,
    left_neckline: float,
    right_neckline: float,
    pattern_type: str = "standard",
) -> float:
    """
    Calculate confidence score for Head and Shoulders patterns.
    Score based on:
    1. Shoulder Symmetry (0.0 to 0.2)
    2. Pattern Height/Significance (0.0 to 0.15)
    3. Head Prominence vs Shoulders (0.0 to 0.1)
    4. Neckline Slope (Penalty up to -0.1)
    """
    score = 0.5

    # 1. Shoulder Symmetry
    # Compare price levels of shoulders
    shoulder_diff_pct = abs(left_shoulder - right_shoulder) / max(
        left_shoulder, right_shoulder
    )
    # Bonus decays as difference likely increases. Using 5% as tolerance baseline.
    symmetry_bonus = max(0.0, 0.2 * (1 - (shoulder_diff_pct / 0.05)))
    score += symmetry_bonus

    # 2. Pattern Height (Significance)
    avg_neckline = (left_neckline + right_neckline) / 2
    height = abs(head - avg_neckline)
    height_pct = height / avg_neckline
    # 5% move considered significant enough for full bonus
    height_bonus = min(0.15, (height_pct / 0.05) * 0.15)
    score += height_bonus

    # 3. Head Prominence
    if pattern_type == "standard":
        # Head higher than max shoulder
        prominence = head - max(left_shoulder, right_shoulder)
    else:
        # Head lower than min shoulder (Inverse)
        prominence = min(left_shoulder, right_shoulder) - head

    prominence_pct = prominence / avg_neckline
    # 2% prominence gets full bonus
    prominence_bonus = min(0.1, (prominence_pct / 0.02) * 0.1)
    score += prominence_bonus

    # 4. Neckline Slope Penalty
    slope_diff_pct = abs(left_neckline - right_neckline) / max(
        left_neckline, right_neckline
    )
    # Penalty scales with slope. 5% slope = max penalty 0.1
    slope_penalty = min(0.1, (slope_diff_pct / 0.05) * 0.1)
    score -= slope_penalty

    return round(max(0.0, min(0.95, score)), 2)


def _calculate_triangle_confidence(
    high_points: list[tuple[int, float]],
    low_points: list[tuple[int, float]],
    high_slope_norm: float,
    low_slope_norm: float,
    pattern_type: str,
) -> float:
    """
    Calculate confidence score for Triangle patterns.
    Score based on:
    1. Linearity/Fit (Residuals of points to trendlines) (0.0 to 0.4)
    2. Boundary Quality (Compliance with ideal slopes) (0.0 to 0.4)
    3. Pattern Duration/Count (Bonus for more points) (0.0 to 0.15)
    """
    score = 0.2

    # 1. Linearity (Fit)
    # Calculate how far points are from the regression line
    def _calculate_residuals(points):
        if len(points) < 2:
            return 1.0  # Max penalty
        x = np.array([p[0] for p in points])
        y = np.array([p[1] for p in points])
        slope, intercept = np.polyfit(x, y, 1)
        # Normalized residuals
        residuals = np.abs(y - (slope * x + intercept)) / y
        return np.mean(residuals)

    high_residuals = _calculate_residuals(high_points)
    low_residuals = _calculate_residuals(low_points)
    avg_residuals = (high_residuals + low_residuals) / 2

    # Lower residuals = better. 0.5% error is acceptable baseline.
    linearity_bonus = max(0.0, 0.4 * (1 - (avg_residuals / 0.005)))
    score += linearity_bonus

    # 2. Boundary Quality & Symmetry
    boundary_score = 0.0

    if pattern_type == "ascending_triangle":
        # Resistance should be flat (slope ~ 0)
        # Rising support should be significant (> 0.05)
        res_quality = max(
            0, 1 - (abs(high_slope_norm) / 0.1)
        )  # 0.1 threshold from detection
        supp_quality = min(1, low_slope_norm / 0.05)
        boundary_score = (res_quality + supp_quality) / 2 * 0.4

    elif pattern_type == "descending_triangle":
        # Support should be flat
        # Falling highs significant
        supp_quality = max(0, 1 - (abs(low_slope_norm) / 0.1))
        res_quality = min(1, abs(high_slope_norm) / 0.05)
        boundary_score = (res_quality + supp_quality) / 2 * 0.4

    elif pattern_type == "symmetrical_triangle":
        # Slopes should be opposite and roughly equal magnitude
        # Symmetrical means abs(high_slope) ~ abs(low_slope)
        slope_diff_pct = abs(abs(high_slope_norm) - abs(low_slope_norm)) / max(
            abs(high_slope_norm), abs(low_slope_norm)
        )
        symmetry = max(0, 1 - (slope_diff_pct / 0.5))  # Allow some variance
        boundary_score = symmetry * 0.4

    score += boundary_score

    # 3. Point Count / Duration
    # More points = more reliable
    total_points = len(high_points) + len(low_points)
    # 4 points is min (2 highs, 2 lows). 8 points is great.
    count_bonus = min(0.15, (total_points - 4) * 0.04)
    score += count_bonus

    return round(max(0.0, min(0.95, score)), 2)


def _calculate_wedge_confidence(
    high_points: list[tuple[int, float]],
    low_points: list[tuple[int, float]],
    high_slope_norm: float,
    low_slope_norm: float,
    pattern_type: str,
) -> float:
    """
    Calculate confidence score for Wedge patterns.
    Score based on:
    1. Linearity/Fit (0.0 to 0.4)
    2. Convergence Quality (0.0 to 0.4)
    3. Point Count (0.0 to 0.15)
    """
    score = 0.2

    # 1. Linearity (Fit) -- reused logic concepts from triangle
    # We can't easily reuse internal function of triangle confidence unless we make it shared or duplicate
    # Duplicating small logic is safer than complex refactor for now
    def _calculate_residuals(points):
        if len(points) < 2:
            return 1.0
        x = np.array([p[0] for p in points])
        y = np.array([p[1] for p in points])
        slope, intercept = np.polyfit(x, y, 1)
        residuals = np.abs(y - (slope * x + intercept)) / y
        return np.mean(residuals)

    high_residuals = _calculate_residuals(high_points)
    low_residuals = _calculate_residuals(low_points)
    avg_residuals = (high_residuals + low_residuals) / 2

    # 0.5% error per point is good
    linearity_bonus = max(0.0, 0.4 * (1 - (avg_residuals / 0.005)))
    score += linearity_bonus

    # 2. Convergence Quality
    # We want clear convergence.
    # Rising Wedge: Low Slope > High Slope. Difference should be clear.
    # Falling Wedge: Low Slope > High Slope (Less negative > More negative).

    slope_diff = low_slope_norm - high_slope_norm
    # If slope_diff is close to 0, it's a channel. If negative, it's broadening.
    # We detected it because slope_diff > 0.

    # Normalize by max absolute slope to get a ratio
    max_slope_abs = max(abs(high_slope_norm), abs(low_slope_norm))
    convergence_ratio = slope_diff / max_slope_abs if max_slope_abs > 0 else 0

    # Ideal convergence: not too parallel (ratio > 0.1), not too abrupt (ratio < 0.8?)
    # We give points for clear convergence.
    convergence_bonus = min(
        0.4, max(0.0, convergence_ratio * 2)
    )  # 0.2 ratio gives full 0.4 bonus? maybe too finding.
    # Let's say ratio 0.1 -> 0.1 bonus. ratio 0.4 -> 0.4 bonus.
    score += convergence_bonus

    # 3. Point Count
    total_points = len(high_points) + len(low_points)
    count_bonus = min(0.15, (total_points - 4) * 0.04)
    score += count_bonus

    return round(max(0.0, min(0.95, score)), 2)


# =============================================================================
# CHART PATTERN DETECTION - Individual Patterns
# =============================================================================


def _detect_double_top(
    df: pd.DataFrame, pivot_highs: pd.Series, pivot_lows: pd.Series
) -> list[dict]:
    """
    Detect Double Top pattern.
    Characteristics:
    - Two peaks at roughly same price level
    - Valley (neckline) between them
    - Bearish reversal pattern
    """
    patterns = []
    highs_list = list(pivot_highs.items())

    for i in range(len(highs_list) - 1):
        date1, price1 = highs_list[i]
        date2, price2 = highs_list[i + 1]

        # Check if peaks are similar
        if not _prices_similar(price1, price2):
            continue

        # Check if there is a detected pivot low (valley) between the peaks
        # This ensures the structure is significant enough
        lows_between = pivot_lows[
            (pivot_lows.index > date1) & (pivot_lows.index < date2)
        ]
        if lows_between.empty:
            continue

        # Find neckline (lowest valid pivot between peaks)
        neckline = lows_between.min()
        neckline_date = lows_between.idxmin()

        idx1 = df.index.get_loc(date1)
        idx2 = df.index.get_loc(date2)

        if idx2 - idx1 < MIN_PATTERN_CANDLES:
            continue

        # Pattern height
        pattern_height = ((price1 + price2) / 2) - neckline

        patterns.append(
            {
                "type": "double_top",
                "category": "reversal",
                "signal": "bearish",
                "start_date": date1.strftime(DATETIME_FORMAT),
                "end_date": date2.strftime(DATETIME_FORMAT),
                "neckline": round(neckline, 2),
                "peaks": [round(price1, 2), round(price2, 2)],
                "target": _calculate_pattern_target(
                    neckline, pattern_height, "bearish"
                ),
                "stop": round(max(price1, price2) * 1.02, 2),
                "entry": round(neckline, 2),
                "key_points": [],
                "confidence": _calculate_double_pattern_confidence(
                    price1, price2, neckline
                ),
            }
        )

        # Build key points with legs
        # Start Point: Low before Peak 1
        lows_before = pivot_lows[pivot_lows.index < date1]
        if not lows_before.empty:
            start_date = lows_before.index[-1]
            start_price = lows_before.iloc[-1]
            patterns[-1]["key_points"].append(
                {
                    "date": start_date.strftime(DATETIME_FORMAT),
                    "price": round(start_price, 2),
                    "label": "Start",
                }
            )

        # Peak 1
        patterns[-1]["key_points"].append(
            {
                "date": date1.strftime(DATETIME_FORMAT),
                "price": round(price1, 2),
                "label": "Peak 1",
            }
        )

        # Neckline
        patterns[-1]["key_points"].append(
            {
                "date": neckline_date.strftime(DATETIME_FORMAT),
                "price": round(neckline, 2),
                "label": "Neckline",
            }
        )

        # Peak 2
        patterns[-1]["key_points"].append(
            {
                "date": date2.strftime(DATETIME_FORMAT),
                "price": round(price2, 2),
                "label": "Peak 2",
            }
        )

        # End Point: Low after Peak 2
        lows_after = pivot_lows[pivot_lows.index > date2]
        if not lows_after.empty:
            end_date = lows_after.index[0]
            end_price = lows_after.iloc[0]
            patterns[-1]["key_points"].append(
                {
                    "date": end_date.strftime(DATETIME_FORMAT),
                    "price": round(end_price, 2),
                    "label": "End",
                }
            )

    return patterns


def _detect_double_bottom(
    df: pd.DataFrame, pivot_highs: pd.Series, pivot_lows: pd.Series
) -> list[dict]:
    """
    Detect Double Bottom pattern.
    Characteristics:
    - Two troughs at roughly same price level
    - Peak (neckline) between them
    - Bullish reversal pattern
    """
    patterns = []
    lows_list = list(pivot_lows.items())

    for i in range(len(lows_list) - 1):
        date1, price1 = lows_list[i]
        date2, price2 = lows_list[i + 1]

        # Check if troughs are similar
        if not _prices_similar(price1, price2):
            continue

        # Check if there is a detected pivot high (peak) between the troughs
        highs_between = pivot_highs[
            (pivot_highs.index > date1) & (pivot_highs.index < date2)
        ]
        if highs_between.empty:
            continue

        # Find neckline (highest valid pivot between troughs)
        neckline = highs_between.max()
        neckline_date = highs_between.idxmax()

        idx1 = df.index.get_loc(date1)
        idx2 = df.index.get_loc(date2)

        if idx2 - idx1 < MIN_PATTERN_CANDLES:
            continue

        # Pattern height
        pattern_height = neckline - ((price1 + price2) / 2)

        patterns.append(
            {
                "type": "double_bottom",
                "category": "reversal",
                "signal": "bullish",
                "start_date": date1.strftime(DATETIME_FORMAT),
                "end_date": date2.strftime(DATETIME_FORMAT),
                "neckline": round(neckline, 2),
                "troughs": [round(price1, 2), round(price2, 2)],
                "target": _calculate_pattern_target(
                    neckline, pattern_height, "bullish"
                ),
                "stop": round(min(price1, price2) * 0.98, 2),
                "entry": round(neckline, 2),
                "key_points": [],
                "confidence": _calculate_double_pattern_confidence(
                    price1, price2, neckline
                ),
            }
        )

        # Build key points with legs
        # Start Point: High before Trough 1
        highs_before = pivot_highs[pivot_highs.index < date1]
        if not highs_before.empty:
            start_date = highs_before.index[-1]
            start_price = highs_before.iloc[-1]
            patterns[-1]["key_points"].append(
                {
                    "date": start_date.strftime(DATETIME_FORMAT),
                    "price": round(start_price, 2),
                    "label": "Start",
                }
            )

        # Trough 1
        patterns[-1]["key_points"].append(
            {
                "date": date1.strftime(DATETIME_FORMAT),
                "price": round(price1, 2),
                "label": "Trough 1",
            }
        )

        # Neckline
        patterns[-1]["key_points"].append(
            {
                "date": neckline_date.strftime(DATETIME_FORMAT),
                "price": round(neckline, 2),
                "label": "Neckline",
            }
        )

        # Trough 2
        patterns[-1]["key_points"].append(
            {
                "date": date2.strftime(DATETIME_FORMAT),
                "price": round(price2, 2),
                "label": "Trough 2",
            }
        )

        # End Point: High after Trough 2
        highs_after = pivot_highs[pivot_highs.index > date2]
        if not highs_after.empty:
            end_date = highs_after.index[0]
            end_price = highs_after.iloc[0]
            patterns[-1]["key_points"].append(
                {
                    "date": end_date.strftime(DATETIME_FORMAT),
                    "price": round(end_price, 2),
                    "label": "End",
                }
            )

    return patterns


def _detect_head_and_shoulders(
    df: pd.DataFrame, pivot_highs: pd.Series, pivot_lows: pd.Series
) -> list[dict]:
    """
    Detect Head and Shoulders pattern.
    Characteristics:
    - Three peaks: left shoulder, head (highest), right shoulder
    - Shoulders at similar levels
    - Neckline connecting troughs
    - Bearish reversal pattern
    """
    patterns = []
    highs_list = list(pivot_highs.items())

    for i in range(len(highs_list) - 2):
        date1, left_shoulder = highs_list[i]
        date2, head = highs_list[i + 1]
        date3, right_shoulder = highs_list[i + 2]

        # Head must be higher than both shoulders
        if head <= left_shoulder or head <= right_shoulder:
            continue

        # Shoulders should be similar
        if not _prices_similar(left_shoulder, right_shoulder, tolerance=0.05):
            continue

        # Find neckline points (lows between peaks)
        idx1 = df.index.get_loc(date1)
        idx2 = df.index.get_loc(date2)
        idx3 = df.index.get_loc(date3)

        if idx2 - idx1 < MIN_PATTERN_CANDLES or idx3 - idx2 < MIN_PATTERN_CANDLES:
            continue

        left_trough_data = df.iloc[idx1 : idx2 + 1]
        right_trough_data = df.iloc[idx2 : idx3 + 1]

        left_neckline = left_trough_data["low"].min()
        left_neckline_date = left_trough_data["low"].idxmin()
        right_neckline = right_trough_data["low"].min()
        right_neckline_date = right_trough_data["low"].idxmin()
        neckline = (left_neckline + right_neckline) / 2

        # Pattern height
        pattern_height = head - neckline

        patterns.append(
            {
                "type": "head_and_shoulders",
                "category": "reversal",
                "signal": "bearish",
                "start_date": date1.strftime(DATETIME_FORMAT),
                "end_date": date3.strftime(DATETIME_FORMAT),
                "neckline": round(neckline, 2),
                "head": round(head, 2),
                "shoulders": [round(left_shoulder, 2), round(right_shoulder, 2)],
                "target": _calculate_pattern_target(
                    neckline, pattern_height, "bearish"
                ),
                "stop": round(head * 1.02, 2),
                "entry": round(neckline, 2),
                "key_points": [
                    {
                        "date": date1.strftime(DATETIME_FORMAT),
                        "price": round(left_shoulder, 2),
                        "label": "Left Shoulder",
                    },
                    {
                        "date": left_neckline_date.strftime(DATETIME_FORMAT),
                        "price": round(left_neckline, 2),
                        "label": "Left Valley",
                    },
                    {
                        "date": date2.strftime(DATETIME_FORMAT),
                        "price": round(head, 2),
                        "label": "Head",
                    },
                    {
                        "date": right_neckline_date.strftime(DATETIME_FORMAT),
                        "price": round(right_neckline, 2),
                        "label": "Right Valley",
                    },
                    {
                        "date": date3.strftime(DATETIME_FORMAT),
                        "price": round(right_shoulder, 2),
                        "label": "Right Shoulder",
                    },
                ],
                "confidence": _calculate_hs_confidence(
                    left_shoulder,
                    right_shoulder,
                    head,
                    left_neckline,
                    right_neckline,
                    pattern_type="standard",
                ),
            }
        )

    return patterns


def _detect_inverse_head_and_shoulders(
    df: pd.DataFrame, pivot_highs: pd.Series, pivot_lows: pd.Series
) -> list[dict]:
    """
    Detect Inverse Head and Shoulders pattern.
    Characteristics:
    - Three troughs: left shoulder, head (lowest), right shoulder
    - Shoulders at similar levels
    - Neckline connecting peaks
    - Bullish reversal pattern
    """
    patterns = []
    lows_list = list(pivot_lows.items())

    for i in range(len(lows_list) - 2):
        date1, left_shoulder = lows_list[i]
        date2, head = lows_list[i + 1]
        date3, right_shoulder = lows_list[i + 2]

        # Head must be lower than both shoulders
        if head >= left_shoulder or head >= right_shoulder:
            continue

        # Shoulders should be similar
        if not _prices_similar(left_shoulder, right_shoulder, tolerance=0.05):
            continue

        # Find neckline points (highs between troughs)
        idx1 = df.index.get_loc(date1)
        idx2 = df.index.get_loc(date2)
        idx3 = df.index.get_loc(date3)

        if idx2 - idx1 < MIN_PATTERN_CANDLES or idx3 - idx2 < MIN_PATTERN_CANDLES:
            continue

        left_peak_data = df.iloc[idx1 : idx2 + 1]
        right_peak_data = df.iloc[idx2 : idx3 + 1]

        left_neckline = left_peak_data["high"].max()
        left_neckline_date = left_peak_data["high"].idxmax()
        right_neckline = right_peak_data["high"].max()
        right_neckline_date = right_peak_data["high"].idxmax()
        neckline = (left_neckline + right_neckline) / 2

        # Pattern height
        pattern_height = neckline - head

        patterns.append(
            {
                "type": "inverse_head_and_shoulders",
                "category": "reversal",
                "signal": "bullish",
                "start_date": date1.strftime(DATETIME_FORMAT),
                "end_date": date3.strftime(DATETIME_FORMAT),
                "neckline": round(neckline, 2),
                "head": round(head, 2),
                "shoulders": [round(left_shoulder, 2), round(right_shoulder, 2)],
                "target": _calculate_pattern_target(
                    neckline, pattern_height, "bullish"
                ),
                "stop": round(head * 0.98, 2),
                "entry": round(neckline, 2),
                "key_points": [
                    {
                        "date": date1.strftime(DATETIME_FORMAT),
                        "price": round(left_shoulder, 2),
                        "label": "Left Shoulder",
                    },
                    {
                        "date": left_neckline_date.strftime(DATETIME_FORMAT),
                        "price": round(left_neckline, 2),
                        "label": "Left Peak",
                    },
                    {
                        "date": date2.strftime(DATETIME_FORMAT),
                        "price": round(head, 2),
                        "label": "Head",
                    },
                    {
                        "date": right_neckline_date.strftime(DATETIME_FORMAT),
                        "price": round(right_neckline, 2),
                        "label": "Right Peak",
                    },
                    {
                        "date": date3.strftime(DATETIME_FORMAT),
                        "price": round(right_shoulder, 2),
                        "label": "Right Shoulder",
                    },
                ],
                "confidence": _calculate_hs_confidence(
                    left_shoulder,
                    right_shoulder,
                    head,
                    left_neckline,
                    right_neckline,
                    pattern_type="inverse",
                ),
            }
        )

    return patterns


def _detect_triangle_patterns(
    df: pd.DataFrame, pivot_highs: pd.Series, pivot_lows: pd.Series
) -> list[dict]:
    """
    Detect Triangle patterns (Ascending, Descending, Symmetrical).

    Ascending: Flat resistance, rising support (bullish)
    Descending: Falling resistance, flat support (bearish)
    Symmetrical: Converging trendlines (bilateral)
    """
    patterns = []

    # Need at least 2 highs and 2 lows
    if len(pivot_highs) < 2 or len(pivot_lows) < 2:
        return patterns

    # Get recent pivots for analysis
    recent_highs = pivot_highs.tail(4)
    recent_lows = pivot_lows.tail(4)

    if len(recent_highs) < 2 or len(recent_lows) < 2:
        return patterns

    # Calculate trendline slopes
    high_points = [(df.index.get_loc(d), p) for d, p in recent_highs.items()]
    low_points = [(df.index.get_loc(d), p) for d, p in recent_lows.items()]

    high_slope = _get_trendline_slope(high_points)
    low_slope = _get_trendline_slope(low_points)

    # Normalize slopes relative to price
    avg_price = (recent_highs.mean() + recent_lows.mean()) / 2
    high_slope_norm = high_slope / avg_price * 100
    low_slope_norm = low_slope / avg_price * 100

    # Classification thresholds
    flat_threshold = 0.1

    start_date = min(recent_highs.index[0], recent_lows.index[0])
    end_date = max(recent_highs.index[-1], recent_lows.index[-1])

    pattern_type = None
    signal = None

    # Ascending Triangle: flat highs, rising lows
    if abs(high_slope_norm) < flat_threshold and low_slope_norm > flat_threshold:
        pattern_type = "ascending_triangle"
        signal = "bullish"

    # Descending Triangle: falling highs, flat lows
    elif high_slope_norm < -flat_threshold and abs(low_slope_norm) < flat_threshold:
        pattern_type = "descending_triangle"
        signal = "bearish"

    # Symmetrical Triangle: converging slopes
    # Lower threshold for symmetrical to catch subtler convergences
    elif high_slope_norm < -0.05 and low_slope_norm > 0.05:
        pattern_type = "symmetrical_triangle"
        signal = "bilateral"

    if pattern_type:
        # Calculate target based on pattern height at start
        pattern_height = recent_highs.iloc[0] - recent_lows.iloc[0]
        current_price = df["close"].iloc[-1]

        patterns.append(
            {
                "type": pattern_type,
                "category": "bilateral" if signal == "bilateral" else "continuation",
                "signal": signal,
                "start_date": start_date.strftime(DATETIME_FORMAT),
                "end_date": end_date.strftime(DATETIME_FORMAT),
                "resistance_slope": round(high_slope_norm, 4),
                "support_slope": round(low_slope_norm, 4),
                "target": round(
                    (
                        current_price + pattern_height
                        if signal == "bullish"
                        else current_price - pattern_height
                    ),
                    2,
                ),
                "trendlines": {
                    "resistance": [
                        {
                            "date": start_date.strftime(DATETIME_FORMAT),
                            "price": round(
                                _calculate_trendline_points(
                                    high_points,
                                    df.index.get_loc(start_date),
                                    df.index.get_loc(end_date),
                                )[0],
                                2,
                            ),
                        },
                        {
                            "date": end_date.strftime(DATETIME_FORMAT),
                            "price": round(
                                _calculate_trendline_points(
                                    high_points,
                                    df.index.get_loc(start_date),
                                    df.index.get_loc(end_date),
                                )[1],
                                2,
                            ),
                        },
                    ],
                    "support": [
                        {
                            "date": start_date.strftime(DATETIME_FORMAT),
                            "price": round(
                                _calculate_trendline_points(
                                    low_points,
                                    df.index.get_loc(start_date),
                                    df.index.get_loc(end_date),
                                )[0],
                                2,
                            ),
                        },
                        {
                            "date": end_date.strftime(DATETIME_FORMAT),
                            "price": round(
                                _calculate_trendline_points(
                                    low_points,
                                    df.index.get_loc(start_date),
                                    df.index.get_loc(end_date),
                                )[1],
                                2,
                            ),
                        },
                    ],
                },
                "confidence": _calculate_triangle_confidence(
                    high_points,
                    low_points,
                    high_slope_norm,
                    low_slope_norm,
                    pattern_type,
                ),
            }
        )

    return patterns


def _detect_wedge_patterns(
    df: pd.DataFrame, pivot_highs: pd.Series, pivot_lows: pd.Series
) -> list[dict]:
    """
    Detect Wedge patterns (Rising, Falling).

    Rising Wedge: Both lines rising, converging (bearish)
    Falling Wedge: Both lines falling, converging (bullish)
    """
    patterns = []

    if len(pivot_highs) < 2 or len(pivot_lows) < 2:
        return patterns

    recent_highs = pivot_highs.tail(4)
    recent_lows = pivot_lows.tail(4)

    if len(recent_highs) < 2 or len(recent_lows) < 2:
        return patterns

    high_points = [(df.index.get_loc(d), p) for d, p in recent_highs.items()]
    low_points = [(df.index.get_loc(d), p) for d, p in recent_lows.items()]

    high_slope = _get_trendline_slope(high_points)
    low_slope = _get_trendline_slope(low_points)

    avg_price = (recent_highs.mean() + recent_lows.mean()) / 2
    high_slope_norm = high_slope / avg_price * 100
    low_slope_norm = low_slope / avg_price * 100

    start_date = min(recent_highs.index[0], recent_lows.index[0])
    end_date = max(recent_highs.index[-1], recent_lows.index[-1])

    pattern_type = None
    signal = None

    # Rising Wedge: both slopes positive, converging (high slope < low slope by at least some margin)
    # Convergence check: Resistance rising slower than Support
    if high_slope_norm > 0.05 and low_slope_norm > 0.05:
        if high_slope_norm < low_slope_norm:
            pattern_type = "rising_wedge"
            signal = "bearish"

    # Falling Wedge: both slopes negative, converging
    # Convergence check: Resistance falling faster (more negative) than Support
    elif high_slope_norm < -0.05 and low_slope_norm < -0.05:
        if high_slope_norm < low_slope_norm:
            pattern_type = "falling_wedge"
            signal = "bullish"

    if pattern_type:
        pattern_height = abs(recent_highs.iloc[-1] - recent_lows.iloc[-1])
        current_price = df["close"].iloc[-1]

        patterns.append(
            {
                "type": pattern_type,
                "category": "reversal",
                "signal": signal,
                "start_date": start_date.strftime(DATETIME_FORMAT),
                "end_date": end_date.strftime(DATETIME_FORMAT),
                "resistance_slope": round(high_slope_norm, 4),
                "support_slope": round(low_slope_norm, 4),
                "target": round(
                    (
                        current_price + pattern_height
                        if signal == "bullish"
                        else current_price - pattern_height
                    ),
                    2,
                ),
                "trendlines": {
                    "resistance": [
                        {
                            "date": start_date.strftime(DATETIME_FORMAT),
                            "price": round(
                                _calculate_trendline_points(
                                    high_points,
                                    df.index.get_loc(start_date),
                                    df.index.get_loc(end_date),
                                )[0],
                                2,
                            ),
                        },
                        {
                            "date": end_date.strftime(DATETIME_FORMAT),
                            "price": round(
                                _calculate_trendline_points(
                                    high_points,
                                    df.index.get_loc(start_date),
                                    df.index.get_loc(end_date),
                                )[1],
                                2,
                            ),
                        },
                    ],
                    "support": [
                        {
                            "date": start_date.strftime(DATETIME_FORMAT),
                            "price": round(
                                _calculate_trendline_points(
                                    low_points,
                                    df.index.get_loc(start_date),
                                    df.index.get_loc(end_date),
                                )[0],
                                2,
                            ),
                        },
                        {
                            "date": end_date.strftime(DATETIME_FORMAT),
                            "price": round(
                                _calculate_trendline_points(
                                    low_points,
                                    df.index.get_loc(start_date),
                                    df.index.get_loc(end_date),
                                )[1],
                                2,
                            ),
                        },
                    ],
                },
                "confidence": _calculate_wedge_confidence(
                    high_points,
                    low_points,
                    high_slope_norm,
                    low_slope_norm,
                    pattern_type,
                ),
            }
        )

    return patterns


def _detect_rectangle_patterns(
    df: pd.DataFrame, pivot_highs: pd.Series, pivot_lows: pd.Series
) -> list[dict]:
    """
    Detect Rectangle patterns (channel/consolidation).

    Bullish Rectangle: Horizontal channel in uptrend
    Bearish Rectangle: Horizontal channel in downtrend
    """
    patterns = []

    if len(pivot_highs) < 2 or len(pivot_lows) < 2:
        return patterns

    recent_highs = pivot_highs.tail(4)
    recent_lows = pivot_lows.tail(4)

    if len(recent_highs) < 2 or len(recent_lows) < 2:
        return patterns

    high_points = [(df.index.get_loc(d), p) for d, p in recent_highs.items()]
    low_points = [(df.index.get_loc(d), p) for d, p in recent_lows.items()]

    high_slope = _get_trendline_slope(high_points)
    low_slope = _get_trendline_slope(low_points)

    avg_price = (recent_highs.mean() + recent_lows.mean()) / 2
    high_slope_norm = high_slope / avg_price * 100
    low_slope_norm = low_slope / avg_price * 100

    flat_threshold = 0.08

    # Rectangle: both lines roughly flat
    if abs(high_slope_norm) < flat_threshold and abs(low_slope_norm) < flat_threshold:
        resistance = recent_highs.mean()
        support = recent_lows.mean()

        # Check variance: All points must be within tolerance of the mean
        # This prevents "zigzag" patterns with flat regression lines from being detected
        tolerance = 0.03  # 3% tolerance
        highs_variance = max(abs(recent_highs - resistance) / resistance)
        lows_variance = max(abs(recent_lows - support) / support)

        if highs_variance > tolerance or lows_variance > tolerance:
            return patterns

        start_date = min(recent_highs.index[0], recent_lows.index[0])
        end_date = max(recent_highs.index[-1], recent_lows.index[-1])

        # Determine trend direction before rectangle
        start_idx = df.index.get_loc(start_date)
        lookback_start = max(0, start_idx - 20)
        prior_data = df.iloc[lookback_start:start_idx]

        if len(prior_data) > 5:
            prior_trend = prior_data["close"].iloc[-1] - prior_data["close"].iloc[0]
            signal = "bullish" if prior_trend > 0 else "bearish"
        else:
            signal = "neutral"

        pattern_height = resistance - support

        patterns.append(
            {
                "type": "rectangle",
                "category": "continuation",
                "signal": signal,
                "start_date": start_date.strftime(DATETIME_FORMAT),
                "end_date": end_date.strftime(DATETIME_FORMAT),
                "resistance": round(resistance, 2),
                "support": round(support, 2),
                "target": round(
                    (
                        resistance + pattern_height
                        if signal == "bullish"
                        else support - pattern_height
                    ),
                    2,
                ),
                "trendlines": {
                    "resistance": [
                        {
                            "date": start_date.strftime(DATETIME_FORMAT),
                            "price": round(resistance, 2),
                        },
                        {
                            "date": end_date.strftime(DATETIME_FORMAT),
                            "price": round(resistance, 2),
                        },
                    ],
                    "support": [
                        {
                            "date": start_date.strftime(DATETIME_FORMAT),
                            "price": round(support, 2),
                        },
                        {
                            "date": end_date.strftime(DATETIME_FORMAT),
                            "price": round(support, 2),
                        },
                    ],
                },
                "confidence": 0.65,
            }
        )

    return patterns


# =============================================================================
# MAIN DETECTION FUNCTIONS
# =============================================================================


def detect_chart_patterns(
    df: pd.DataFrame, pivot_order: int = PIVOT_ORDER
) -> list[dict]:
    """
    Detect all chart patterns in price data.

    Args:
        df: DataFrame with OHLCV data
        pivot_order: Sensitivity for pivot detection

    Returns:
        List of detected patterns with details
    """
    if len(df) < pivot_order * 2 + 1:
        return []

    pivot_highs, pivot_lows = find_pivot_points(df, pivot_order)

    # Merge nearby duplicate pivots
    pivot_highs = _merge_pivots_series(pivot_highs, mode="max")
    pivot_lows = _merge_pivots_series(pivot_lows, mode="min")

    all_patterns = []

    # Detect each pattern type
    all_patterns.extend(_detect_double_top(df, pivot_highs, pivot_lows))
    all_patterns.extend(_detect_double_bottom(df, pivot_highs, pivot_lows))
    all_patterns.extend(_detect_head_and_shoulders(df, pivot_highs, pivot_lows))
    all_patterns.extend(_detect_inverse_head_and_shoulders(df, pivot_highs, pivot_lows))
    all_patterns.extend(_detect_triangle_patterns(df, pivot_highs, pivot_lows))
    all_patterns.extend(_detect_wedge_patterns(df, pivot_highs, pivot_lows))
    all_patterns.extend(_detect_rectangle_patterns(df, pivot_highs, pivot_lows))

    # Filter conflicting patterns (prioritize complex patterns over simple ones)
    all_patterns = _filter_conflicting_patterns(all_patterns)

    # Sort by end date (most recent first)
    all_patterns.sort(key=lambda x: x["end_date"], reverse=True)

    return all_patterns


def _merge_pivots_series(pivots: pd.Series, mode: str = "max") -> pd.Series:
    """Merge clustered pivots."""
    if pivots.empty:
        return pivots

    sorted_dates = pivots.index.sort_values()
    result = {}

    cluster_dates = [sorted_dates[0]]
    cluster_prices = [pivots[sorted_dates[0]]]

    for i in range(1, len(sorted_dates)):
        date = sorted_dates[i]
        prev_date = sorted_dates[i - 1]

        # Check if adjacent (gap of few days/bars).
        # Using a time delta threshold of 4 days roughly covers long weekends + 1 bar
        if (date - prev_date).total_seconds() <= 3600 * 24 * 4:
            cluster_dates.append(date)
            cluster_prices.append(pivots[date])
        else:
            # Resolve cluster
            if mode == "max":
                idx = np.argmax(cluster_prices)
            else:
                idx = np.argmin(cluster_prices)
            result[cluster_dates[idx]] = cluster_prices[idx]

            cluster_dates = [date]
            cluster_prices = [pivots[date]]

    # Last cluster
    if cluster_dates:
        if mode == "max":
            idx = np.argmax(cluster_prices)
        else:
            idx = np.argmin(cluster_prices)
        result[cluster_dates[idx]] = cluster_prices[idx]

    return pd.Series(result).sort_index()


def _filter_conflicting_patterns(patterns: list[dict]) -> list[dict]:
    """
    Remove redundant/conflicting patterns.
    Rules:
    1. If Head and Shoulders exists, remove Double Bottoms contained within it.
    2. If Inverse H&S exists, remove Double Tops contained within it.
    """
    if not patterns:
        return []

    filtered = []
    to_remove_indices = set()

    # Separate patterns by type
    hs_patterns = [
        p for i, p in enumerate(patterns) if p["type"] == "head_and_shoulders"
    ]
    inv_hs_patterns = [
        p for i, p in enumerate(patterns) if p["type"] == "inverse_head_and_shoulders"
    ]
    triangle_patterns = [p for i, p in enumerate(patterns) if "triangle" in p["type"]]

    for i, pat in enumerate(patterns):
        if i in to_remove_indices:
            continue

        is_redundant = False

        # Check Double Bottom
        if pat["type"] == "double_bottom":
            # vs Head and Shoulders
            for hs in hs_patterns:
                if (
                    pat["start_date"] >= hs["start_date"]
                    and pat["end_date"] <= hs["end_date"]
                ):
                    is_redundant = True
                    break
            # vs Triangles (Ascending Triangle rising lows can look like partial DB or vice versa,
            # but usually Triangles are bigger. If DB is fully inside Triangle, prefer Triangle)
            if not is_redundant:
                for tri in triangle_patterns:
                    if (
                        pat["start_date"] >= tri["start_date"]
                        and pat["end_date"] <= tri["end_date"]
                    ):
                        is_redundant = True
                        break

        # Check Double Top
        elif pat["type"] == "double_top":
            # vs Inverse Head and Shoulders
            for inv_hs in inv_hs_patterns:
                if (
                    pat["start_date"] >= inv_hs["start_date"]
                    and pat["end_date"] <= inv_hs["end_date"]
                ):
                    is_redundant = True
                    break
            # vs Triangles
            if not is_redundant:
                for tri in triangle_patterns:
                    if (
                        pat["start_date"] >= tri["start_date"]
                        and pat["end_date"] <= tri["end_date"]
                    ):
                        is_redundant = True
                        break

        if not is_redundant:
            filtered.append(pat)

    return filtered


# =============================================================================
# API WRAPPER FUNCTIONS
# =============================================================================


def get_chart_patterns(
    ticker: str,
    start_date: str,
    end_date: str,
    interval: str = "1D",
) -> dict:
    """
    Detect chart patterns for a given stock.

    Args:
        ticker: Stock ticker symbol
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        interval: 5m, 15m, 30m, 1H, 1D (default), 1W, 1M

    Returns:
        Dictionary with detected patterns
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

        df = create_ohlcv_dataframe(candles)

        patterns = detect_chart_patterns(df)

        return {"ticker": ticker, "patterns": patterns, "count": len(patterns)}

    except Exception as e:
        return {"error": str(e), "ticker": ticker}


def get_support_resistance(
    ticker: str,
    start_date: str,
    end_date: str,
    interval: str = "1D",
) -> dict:
    """
    Detect support/resistance zones for a given stock.

    Args:
        ticker: Stock ticker symbol
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        interval: 5m, 15m, 30m, 1H, 1D (default), 1W, 1M

    Returns:
        Dictionary with S/R zones
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

        df = create_ohlcv_dataframe(candles)

        zones = detect_support_resistance_zones(df)
        zones["ticker"] = ticker
        zones["current_price"] = round(df["close"].iloc[-1], 2)

        return zones

    except Exception as e:
        return {"error": str(e), "ticker": ticker}
