"""
Technical Indicator Configuration Module.
Contains all configurable parameters for pandas_ta indicators.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class IndicatorConfig:
    """Configuration for all technical indicators."""

    # ==========================================================================
    # OVERLAP INDICATORS
    # ==========================================================================

    # Moving Average Lengths
    ma_lengths: list = field(default_factory=lambda: [5, 10, 20, 50, 100, 200])

    # Advanced Moving Averages
    dema_length: int = 20
    tema_length: int = 20
    wma_length: int = 20
    hma_length: int = 20
    kama_length: int = 10
    zlma_length: int = 20
    t3_length: int = 10
    trima_length: int = 20
    vidya_length: int = 14
    fwma_length: int = 10
    pwma_length: int = 10
    swma_length: int = 10
    sinwma_length: int = 14
    alma_length: int = 20
    mcgd_length: int = 10
    jma_length: int = 7

    # Midpoint/Midprice
    midpoint_length: int = 20
    midprice_length: int = 14

    # Supertrend
    supertrend_length: int = 10
    supertrend_multiplier: float = 3.0

    # Ichimoku
    ichimoku_tenkan: int = 9
    ichimoku_kijun: int = 26
    ichimoku_senkou: int = 52

    # Linear Regression
    linreg_length: int = 14

    # HiLo
    hilo_high_length: int = 13
    hilo_low_length: int = 21

    # Hilbert Transform
    ht_trendline_length: int = 14

    # ==========================================================================
    # MOMENTUM INDICATORS
    # ==========================================================================

    # RSI
    rsi_length: int = 14
    rsi_fast_length: int = 7

    # MACD
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9

    # Stochastic
    stoch_k: int = 14
    stoch_d: int = 3
    stoch_smooth_k: int = 3

    # Stochastic RSI
    stochrsi_length: int = 14
    stochrsi_rsi_length: int = 14
    stochrsi_k: int = 3
    stochrsi_d: int = 3

    # Williams %R
    willr_length: int = 14

    # CCI
    cci_length: int = 20
    cci_fast_length: int = 14

    # Momentum
    mom_length: int = 10
    mom_alt_length: int = 14

    # ROC
    roc_length: int = 10
    roc_alt_length: int = 14

    # Awesome Oscillator
    ao_fast: int = 5
    ao_slow: int = 34

    # APO/PPO
    apo_fast: int = 12
    apo_slow: int = 26
    ppo_fast: int = 12
    ppo_slow: int = 26
    ppo_signal: int = 9

    # Bias
    bias_length: int = 26

    # BRAR
    brar_length: int = 26

    # CFO
    cfo_length: int = 9

    # CG (Center of Gravity)
    cg_length: int = 10

    # CMO
    cmo_length: int = 14

    # Coppock
    coppock_length: int = 10
    coppock_fast: int = 11
    coppock_slow: int = 14

    # CTI
    cti_length: int = 12

    # ER (Efficiency Ratio)
    er_length: int = 10

    # ERI (Elder Ray Index)
    eri_length: int = 13

    # Fisher Transform
    fisher_length: int = 9

    # Inertia
    inertia_length: int = 20
    inertia_rvi_length: int = 14

    # KDJ
    kdj_length: int = 9
    kdj_signal: int = 3

    # PGO
    pgo_length: int = 14

    # PSL (Psychological Line)
    psl_length: int = 12

    # QQE
    qqe_length: int = 14
    qqe_smooth: int = 5
    qqe_factor: float = 4.236

    # RVGI
    rvgi_length: int = 14
    rvgi_swma_length: int = 4

    # Slope
    slope_length: int = 14

    # SMI
    smi_fast: int = 5
    smi_slow: int = 20
    smi_signal: int = 5

    # Squeeze
    squeeze_bb_length: int = 20
    squeeze_kc_length: int = 20
    squeeze_bb_std: float = 2.0
    squeeze_kc_scalar: float = 1.5

    # STC
    stc_fast: int = 23
    stc_slow: int = 50
    stc_signal: int = 10

    # TRIX
    trix_length: int = 18
    trix_signal: int = 9

    # TSI
    tsi_fast: int = 13
    tsi_slow: int = 25
    tsi_signal: int = 13

    # RSX
    rsx_length: int = 14

    # TMO
    tmo_length: int = 14
    tmo_smooth: int = 5

    # CRSI
    crsi_rsi_length: int = 3
    crsi_streak_length: int = 2
    crsi_rank_length: int = 100
    # Alternative names used in calc_crsi
    crsi_rsi: int = 3
    crsi_streak: int = 2
    crsi_lookback: int = 100

    # UO (Ultimate Oscillator)
    uo_fast: int = 7
    uo_medium: int = 14
    uo_slow: int = 28

    # KST (Know Sure Thing)
    kst_roc1: int = 10
    kst_roc2: int = 15
    kst_roc3: int = 20
    kst_roc4: int = 30
    kst_sma1: int = 10
    kst_sma2: int = 10
    kst_sma3: int = 10
    kst_sma4: int = 15
    kst_signal: int = 9

    # KVO (Klinger Volume Oscillator)
    kvo_fast: int = 34
    kvo_slow: int = 55
    kvo_signal: int = 13

    # NVI (Negative Volume Index)
    nvi_length: int = 1

    # PVI (Positive Volume Index)
    pvi_length: int = 1

    # ==========================================================================
    # TREND INDICATORS
    # ==========================================================================

    # ADX
    adx_length: int = 14

    # Aroon
    aroon_length: int = 25

    # Choppiness
    chop_length: int = 14

    # Decay
    decay_length: int = 5
    decay_mode: str = "linear"

    # DPO
    dpo_length: int = 20
    dpo_centered: bool = True

    # QStick
    qstick_length: int = 10

    # RWI
    rwi_length: int = 14

    # VHF
    vhf_length: int = 28

    # Vortex
    vortex_length: int = 14

    # AlphaTrend
    alphatrend_length: int = 14

    # AMAT
    amat_fast: int = 8
    amat_slow: int = 21

    # Trendflex
    trendflex_length: int = 20

    # RWI
    rwi_length: int = 14

    # TTM Trend
    ttm_trend_length: int = 5

    # CKSP (Chande Kroll Stop)
    cksp_p: int = 10
    cksp_x: float = 1.0
    cksp_q: int = 9

    # PSAR (Parabolic SAR)
    psar_af0: float = 0.02
    psar_af: float = 0.02
    psar_max_af: float = 0.2

    # ==========================================================================
    # VOLATILITY INDICATORS
    # ==========================================================================

    # ATR
    atr_length: int = 14

    # NATR
    natr_length: int = 14

    # Bollinger Bands
    bbands_length: int = 20
    bbands_std: float = 2.0

    # Keltner Channel
    kc_length: int = 20
    kc_scalar: float = 1.5
    kc_mamode: str = "ema"

    # Donchian Channel
    donchian_lower_length: int = 20
    donchian_upper_length: int = 20

    # Acceleration Bands
    accbands_length: int = 20
    accbands_c: float = 4.0

    # Aberration
    aberration_length: int = 5
    aberration_zg: float = 1
    aberration_sg: float = 3
    aberration_xg: float = 5

    # MASSI
    massi_fast: int = 9
    massi_slow: int = 25

    # RVI
    rvi_length: int = 14

    # Thermo
    thermo_length: int = 20
    thermo_long: int = 2
    thermo_short: int = 0.5

    # UI (Ulcer Index)
    ui_length: int = 14

    # ==========================================================================
    # VOLUME INDICATORS
    # ==========================================================================

    # ADOSC
    adosc_fast: int = 3
    adosc_slow: int = 10

    # CMF
    cmf_length: int = 20

    # EFI
    efi_length: int = 13

    # EOM
    eom_length: int = 14

    # MFI
    mfi_length: int = 14

    # PVO
    pvo_fast: int = 12
    pvo_slow: int = 26
    pvo_signal: int = 9

    # VWMA
    vwma_length: int = 20

    # AOBV
    aobv_fast: int = 4
    aobv_slow: int = 12
    aobv_max_lookback: int = 2
    aobv_min_lookback: int = 2
    aobv_mamode: str = "ema"

    # TSV
    tsv_length: int = 13

    # ==========================================================================
    # STATISTICS INDICATORS
    # ==========================================================================

    # Standard Deviation
    stdev_length: int = 20

    # Variance
    variance_length: int = 20

    # Z-Score
    zscore_length: int = 20

    # Skew
    skew_length: int = 30

    # Kurtosis
    kurtosis_length: int = 30

    # Entropy
    entropy_length: int = 10

    # MAD
    mad_length: int = 20

    # Median
    median_length: int = 20

    # Quantile
    quantile_length: int = 20
    quantile_q: float = 0.5

    # TOS StdevAll
    tos_stdevall_length: int = 20

    # ==========================================================================
    # CYCLE INDICATORS
    # ==========================================================================

    # EBSW
    ebsw_length: int = 40
    ebsw_bars: int = 10

    # Reflex
    reflex_length: int = 20

    # ==========================================================================
    # CHART/ANALYSIS SETTINGS
    # ==========================================================================

    # Fibonacci lookback
    fib_lookback_short: int = 50
    fib_lookback_long: int = 100

    # Series tail length for charts
    chart_series_length: int = 100

    # ==========================================================================
    # PERFORMANCE INDICATORS
    # ==========================================================================

    # Log Return
    log_return_length: int = 1
    log_return_cumulative: bool = False

    # Percent Return
    percent_return_length: int = 1
    percent_return_cumulative: bool = False

    # ==========================================================================
    # STYLING CONFIGURATION
    # ==========================================================================

    # Defaults handled by helper function, but field definition:
    styling: Dict[str, Any] = field(default_factory=lambda: DEFAULT_STYLING)


def _create_default_styling() -> Dict[str, Any]:
    """Create the default styling configuration for all indicators."""

    # Alpha value for transparency (0.7 = 70% opacity)
    ALPHA = "b3"  # Hex for ~0.7 opacity (179/255)

    # ========================================================================
    # PROFESSIONAL CHART COLOR PALETTE
    # ========================================================================
    # Light Mode Colors - Darker shades for visibility on light backgrounds
    # Primary Colors - High visibility, main indicators
    BLUE = "#2563eb"  # Royal Blue - Primary lines, main trends
    RED = "#dc2626"  # Crimson Red - Bearish signals, resistance
    GREEN = "#16a34a"  # Emerald Green - Bullish signals, support

    # Secondary Colors - Supporting indicators
    ORANGE = "#ea580c"  # Vibrant Orange - Signal lines, warnings
    PURPLE = "#9333ea"  # Vivid Purple - Special indicators
    CYAN = "#0891b2"  # Deep Cyan - Oscillators

    # Accent Colors - Additional distinction
    YELLOW = "#ca8a04"  # Golden Yellow - Neutral zones, bands
    PINK = "#db2777"  # Hot Pink - Momentum highlights
    TEAL = "#0d9488"  # Teal - Volume indicators
    LIME = "#65a30d"  # Lime - Alternative positive
    SKY = "#0284c7"  # Sky Blue - Channels
    ROSE = "#e11d48"  # Rose - Divergence signals
    AMBER = "#d97706"  # Amber - Trend alerts
    INDIGO = "#4f46e5"  # Indigo - MACD family
    SLATE = "#64748b"  # Slate Gray - Reference lines

    # ========================================================================
    # DARK MODE COLOR PALETTE - Brighter with transparency for dark backgrounds
    # ========================================================================

    # Primary Colors - Brighter versions for dark mode
    BLUE_DARK = f"#60a5fa{ALPHA}"  # Bright Blue
    RED_DARK = f"#f87171{ALPHA}"  # Bright Red
    GREEN_DARK = f"#4ade80{ALPHA}"  # Bright Green

    # Secondary Colors - Brighter versions
    ORANGE_DARK = f"#fb923c{ALPHA}"  # Bright Orange
    PURPLE_DARK = f"#c084fc{ALPHA}"  # Bright Purple
    CYAN_DARK = f"#22d3ee{ALPHA}"  # Bright Cyan

    # Accent Colors - Brighter versions
    YELLOW_DARK = f"#facc15{ALPHA}"  # Bright Yellow
    PINK_DARK = f"#f472b6{ALPHA}"  # Bright Pink
    TEAL_DARK = f"#2dd4bf{ALPHA}"  # Bright Teal
    LIME_DARK = f"#a3e635{ALPHA}"  # Bright Lime
    SKY_DARK = f"#38bdf8{ALPHA}"  # Bright Sky
    ROSE_DARK = f"#fb7185{ALPHA}"  # Bright Rose
    AMBER_DARK = f"#fbbf24{ALPHA}"  # Bright Amber
    INDIGO_DARK = f"#818cf8{ALPHA}"  # Bright Indigo
    SLATE_DARK = f"#94a3b8{ALPHA}"  # Bright Slate

    # Color mapping for dark/light mode
    COLORS = {
        "blue": (BLUE_DARK, BLUE),
        "red": (RED_DARK, RED),
        "green": (GREEN_DARK, GREEN),
        "orange": (ORANGE_DARK, ORANGE),
        "purple": (PURPLE_DARK, PURPLE),
        "cyan": (CYAN_DARK, CYAN),
        "yellow": (YELLOW_DARK, YELLOW),
        "pink": (PINK_DARK, PINK),
        "teal": (TEAL_DARK, TEAL),
        "lime": (LIME_DARK, LIME),
        "sky": (SKY_DARK, SKY),
        "rose": (ROSE_DARK, ROSE),
        "amber": (AMBER_DARK, AMBER),
        "indigo": (INDIGO_DARK, INDIGO),
        "slate": (SLATE_DARK, SLATE),
    }

    def get_dark_color(light_color: str) -> str:
        """Get the corresponding dark mode color for a light mode color."""
        for _, (dark, light) in COLORS.items():
            if light == light_color:
                return dark
        # If no mapping found, add transparency to the original color
        return f"{light_color}b3"

    # Line styles
    HIDDEN = -1
    SOLID = 0
    DOTTED = 1
    DASHED = 2
    LARGE_DASHED = 3
    SPARSE_DOTTED = 4

    # Value formats
    PRICE = "price"
    NUMBER = "number"
    PERCENTAGE = "percentage"

    # Dark/Light mode helpers
    def single_color(color, field_name="value", pane=0, value_format=PRICE):
        dark_color = get_dark_color(color)
        return {
            "pane": pane,
            "colors": {"dark": {field_name: dark_color}, "light": {field_name: color}},
            "lineStyles": DASHED,
            "valueFormat": value_format,
        }

    # Configuration map
    config = {}

    # ------------------------------------------------------------------
    # OVERLAP (Pane 0)
    # ------------------------------------------------------------------
    # MA with different colors per length
    config["ma"] = single_color(BLUE)  # Default fallback
    config["ma_5"] = single_color(SKY)
    config["ma_10"] = single_color(BLUE)
    config["ma_20"] = single_color(INDIGO)
    config["ma_50"] = single_color(PURPLE)
    config["ma_100"] = single_color(CYAN)
    config["ma_200"] = single_color(TEAL)

    # EMA with different colors per length
    config["ema"] = single_color(ORANGE)  # Default fallback
    config["ema_5"] = single_color(YELLOW)
    config["ema_10"] = single_color(ORANGE)
    config["ema_20"] = single_color(AMBER)
    config["ema_50"] = single_color(ROSE)
    config["ema_100"] = single_color(PINK)
    config["ema_200"] = single_color(RED)
    config["wma"] = single_color(CYAN)
    config["dema"] = single_color(PURPLE)
    config["tema"] = single_color(PINK)
    config["hma"] = single_color(YELLOW)
    config["kama"] = single_color(GREEN)
    config["zlma"] = single_color(RED)
    config["t3"] = single_color(BLUE)
    config["trima"] = single_color(ORANGE)
    config["vidya"] = single_color(CYAN)
    config["fwma"] = single_color(PURPLE)
    config["pwma"] = single_color(PINK)
    config["swma"] = single_color(YELLOW)
    config["sinwma"] = single_color(GREEN)
    config["alma"] = single_color(RED)
    config["mcgd"] = single_color(BLUE)
    config["jma"] = single_color(ORANGE)
    config["hl2"] = single_color(CYAN)
    config["hlc3"] = single_color(PURPLE)
    config["ohlc4"] = single_color(PINK)
    config["wcp"] = single_color(YELLOW)
    config["midpoint"] = single_color(GREEN)
    config["midprice"] = single_color(RED)
    config["linreg"] = single_color(BLUE)
    config["ht_trendline"] = single_color(ORANGE)
    config["vwap"] = single_color(TEAL, pane=0)

    # Multi-line Overlaps
    config["bb"] = {
        "pane": 0,
        "colors": {
            "dark": {
                "upper": get_dark_color(SKY),
                "middle": get_dark_color(SLATE),
                "lower": get_dark_color(SKY),
                "bandwidth": get_dark_color(SKY),
                "percentage": get_dark_color(SKY),
            },
            "light": {
                "upper": SKY,
                "middle": SLATE,
                "lower": SKY,
                "bandwidth": SKY,
                "percentage": SKY,
            },
        },
        "lineStyles": {
            "upper": DASHED,
            "middle": SOLID,
            "lower": DASHED,
            "bandwidth": HIDDEN,
            "percentage": HIDDEN,
        },
        "valueFormat": PRICE,
    }
    config["ichimoku"] = {
        "pane": 0,
        "colors": {
            "dark": {
                "conversion": get_dark_color(CYAN),
                "base": get_dark_color(RED),
                "lagging": get_dark_color(GREEN),
                "spanA": get_dark_color(GREEN),
                "spanB": get_dark_color(RED),
            },
            "light": {
                "conversion": CYAN,
                "base": RED,
                "lagging": GREEN,
                "spanA": GREEN,
                "spanB": RED,
            },
        },
        "lineStyles": {
            "conversion": DASHED,
            "base": SOLID,
            "lagging": DASHED,
            "spanA": SOLID,
            "spanB": DASHED,
        },
        "valueFormat": PRICE,
    }
    config["supertrend"] = single_color(GREEN, pane=0)
    config["hilo"] = single_color(BLUE, pane=0)
    config["alligator"] = {
        "pane": 0,
        "colors": {
            "dark": {
                "jaw": get_dark_color(BLUE),
                "teeth": get_dark_color(RED),
                "lips": get_dark_color(GREEN),
            },
            "light": {"jaw": BLUE, "teeth": RED, "lips": GREEN},
        },
        "lineStyles": {"jaw": DASHED, "teeth": SOLID, "lips": DASHED},
        "valueFormat": PRICE,
    }
    config["mama"] = {
        "pane": 0,
        "colors": {
            "dark": {"mama": get_dark_color(CYAN), "fama": get_dark_color(RED)},
            "light": {"mama": CYAN, "fama": RED},
        },
        "lineStyles": {"mama": DASHED, "fama": SOLID},
        "valueFormat": PRICE,
    }

    # ------------------------------------------------------------------
    # MOMENTUM - Usually separated panes
    # ------------------------------------------------------------------

    config["rsi"] = single_color(PURPLE, pane=2, value_format=NUMBER)
    config["macd"] = {
        "pane": 2,
        "colors": {
            "dark": {
                "line": get_dark_color(INDIGO),
                "signal": get_dark_color(ROSE),
                "histogram": get_dark_color(LIME),
            },
            "light": {"line": INDIGO, "signal": ROSE, "histogram": LIME},
        },
        "lineStyles": {"line": SOLID, "signal": DASHED, "histogram": SOLID},
        "valueFormat": NUMBER,
    }
    config["stoch"] = {
        "pane": 2,
        "colors": {
            "dark": {"k": get_dark_color(GREEN), "d": get_dark_color(RED)},
            "light": {"k": GREEN, "d": RED},
        },
        "lineStyles": {"k": SOLID, "d": DASHED},
        "valueFormat": NUMBER,
    }
    config["williams"] = single_color(CYAN, pane=2, value_format=NUMBER)
    config["cci"] = single_color(PURPLE, pane=2, value_format=NUMBER)
    config["roc"] = single_color(ORANGE, pane=2, value_format=NUMBER)

    # Other Momentums - Defaults to separate pane
    config["stochrsi"] = {
        "pane": 2,
        "colors": {
            "dark": {"k": get_dark_color(BLUE), "d": get_dark_color(RED)},
            "light": {"k": BLUE, "d": RED},
        },
        "lineStyles": {"k": SOLID, "d": DASHED},
        "valueFormat": PRICE,
    }
    config["mom"] = single_color(BLUE, pane=2)
    config["ao"] = single_color(GREEN, pane=2)
    config["apo"] = single_color(ORANGE, pane=2)
    config["ppo"] = {
        "pane": 2,
        "colors": {
            "dark": {
                "ppo": get_dark_color(BLUE),
                "signal": get_dark_color(RED),
                "histogram": get_dark_color(GREEN),
            },
            "light": {"ppo": BLUE, "signal": RED, "histogram": GREEN},
        },
        "lineStyles": {"ppo": SOLID, "signal": DASHED, "histogram": SOLID},
        "valueFormat": PRICE,
    }
    config["bias"] = single_color(CYAN, pane=2)
    config["brar"] = {
        "pane": 2,
        "colors": {
            "dark": {"ar": get_dark_color(PURPLE), "br": get_dark_color(ORANGE)},
            "light": {"ar": PURPLE, "br": ORANGE},
        },
        "lineStyles": {"ar": SOLID, "br": DASHED},
        "valueFormat": PRICE,
    }
    config["cfo"] = single_color(PINK, pane=2)
    config["cg"] = single_color(YELLOW, pane=2)
    config["cmo"] = single_color(GREEN, pane=2)
    config["coppock"] = single_color(RED, pane=2)
    config["cti"] = single_color(BLUE, pane=2)
    config["er"] = single_color(ORANGE, pane=2)
    config["eri"] = {
        "pane": 2,
        "colors": {
            "dark": {"bull": get_dark_color(GREEN), "bear": get_dark_color(RED)},
            "light": {"bull": GREEN, "bear": RED},
        },
        "lineStyles": {"bull": SOLID, "bear": DASHED},
        "valueFormat": PRICE,
    }
    config["fisher"] = {
        "pane": 2,
        "colors": {
            "dark": {"fisher": get_dark_color(CYAN), "signal": get_dark_color(ORANGE)},
            "light": {"fisher": CYAN, "signal": ORANGE},
        },
        "lineStyles": {"fisher": SOLID, "signal": DASHED},
        "valueFormat": PRICE,
    }
    config["inertia"] = single_color(PURPLE, pane=2)
    config["kdj"] = {
        "pane": 2,
        "colors": {
            "dark": {
                "k": get_dark_color(BLUE),
                "d": get_dark_color(ORANGE),
                "j": get_dark_color(PURPLE),
            },
            "light": {"k": BLUE, "d": ORANGE, "j": PURPLE},
        },
        "lineStyles": {"k": SOLID, "d": DASHED, "j": SOLID},
        "valueFormat": PRICE,
    }
    config["pgo"] = single_color(RED, pane=2)
    config["psl"] = single_color(GREEN, pane=2)
    config["qqe"] = {
        "pane": 2,
        "colors": {
            "dark": {
                "qqe": get_dark_color(BLUE),
                "long": get_dark_color(GREEN),
                "short": get_dark_color(RED),
            },
            "light": {"qqe": BLUE, "long": GREEN, "short": RED},
        },
        "lineStyles": {"qqe": SOLID, "long": DASHED, "short": SOLID},
        "valueFormat": PRICE,
    }
    config["rvgi"] = {
        "pane": 2,
        "colors": {
            "dark": {"rvgi": get_dark_color(BLUE), "signal": get_dark_color(RED)},
            "light": {"rvgi": BLUE, "signal": RED},
        },
        "lineStyles": {"rvgi": SOLID, "signal": DASHED},
        "valueFormat": PRICE,
    }
    config["slope"] = single_color(YELLOW, pane=2)
    config["smi"] = {
        "pane": 2,
        "colors": {
            "dark": {
                "smi": get_dark_color(BLUE),
                "signal": get_dark_color(RED),
                "oscillator": get_dark_color(YELLOW),
            },
            "light": {"smi": BLUE, "signal": RED, "oscillator": YELLOW},
        },
        "lineStyles": {"smi": SOLID, "signal": DASHED, "oscillator": SOLID},
        "valueFormat": PRICE,
    }
    config["squeeze"] = single_color(BLUE, pane=2)
    config["stc"] = single_color(PURPLE, pane=2)
    config["trix"] = {
        "pane": 2,
        "colors": {
            "dark": {"trix": get_dark_color(BLUE), "signal": get_dark_color(RED)},
            "light": {"trix": BLUE, "signal": RED},
        },
        "lineStyles": {"trix": SOLID, "signal": DASHED},
        "valueFormat": PRICE,
    }
    config["tsi"] = {
        "pane": 2,
        "colors": {
            "dark": {"tsi": get_dark_color(CYAN), "signal": get_dark_color(RED)},
            "light": {"tsi": CYAN, "signal": RED},
        },
        "lineStyles": {"tsi": SOLID, "signal": DASHED},
        "valueFormat": PRICE,
    }
    config["rsx"] = single_color(PINK, pane=2)
    config["tmo"] = {
        "pane": 2,
        "colors": {
            "dark": {"main": get_dark_color(BLUE), "signal": get_dark_color(RED)},
            "light": {"main": BLUE, "signal": RED},
        },
        "lineStyles": {"main": SOLID, "signal": DASHED},
        "valueFormat": PRICE,
    }
    config["crsi"] = single_color(YELLOW, pane=2)
    config["bop"] = single_color(BLUE, pane=2)
    config["stochf"] = {
        "pane": 2,
        "colors": {
            "dark": {"k": get_dark_color(GREEN), "d": get_dark_color(RED)},
            "light": {"k": GREEN, "d": RED},
        },
        "lineStyles": {"k": SOLID, "d": DASHED},
        "valueFormat": PRICE,
    }
    config["kst"] = {
        "pane": 2,
        "colors": {
            "dark": {"kst": get_dark_color(BLUE), "signal": get_dark_color(RED)},
            "light": {"kst": BLUE, "signal": RED},
        },
        "lineStyles": {"kst": SOLID, "signal": DASHED},
        "valueFormat": PRICE,
    }
    config["rsi_fast"] = single_color(ORANGE, pane=2)
    config["uo"] = single_color(CYAN, pane=2)
    config["squeeze_pro"] = single_color(BLUE, pane=2)

    # ------------------------------------------------------------------
    # TREND (Separated pane)
    # ------------------------------------------------------------------
    config["adx"] = {
        "pane": 2,
        "colors": {
            "dark": {
                "adx": get_dark_color(GREEN),
                "plusDI": get_dark_color(BLUE),
                "minusDI": get_dark_color(RED),
            },
            "light": {"adx": GREEN, "plusDI": BLUE, "minusDI": RED},
        },
        "lineStyles": {"adx": SOLID, "plusDI": DASHED, "minusDI": SOLID},
        "valueFormat": NUMBER,
    }
    config["aroon"] = {
        "pane": 2,
        "colors": {
            "dark": {"up": get_dark_color(GREEN), "down": get_dark_color(RED)},
            "light": {"up": GREEN, "down": RED},
        },
        "lineStyles": {"up": SOLID, "down": DASHED},
        "valueFormat": PRICE,
    }
    config["chop"] = single_color(BLUE, pane=2)
    config["decay"] = single_color(ORANGE, pane=2)
    config["dpo"] = single_color(CYAN, pane=2)
    config["qstick"] = single_color(PURPLE, pane=2)
    config["rwi"] = {
        "pane": 2,
        "colors": {
            "dark": {"high": get_dark_color(GREEN), "low": get_dark_color(RED)},
            "light": {"high": GREEN, "low": RED},
        },
        "lineStyles": {"high": SOLID, "low": DASHED},
        "valueFormat": PRICE,
    }
    config["vhf"] = single_color(PINK, pane=2)
    config["vortex"] = {
        "pane": 2,
        "colors": {
            "dark": {"pos": get_dark_color(GREEN), "neg": get_dark_color(RED)},
            "light": {"pos": GREEN, "neg": RED},
        },
        "lineStyles": {"pos": SOLID, "neg": DASHED},
        "valueFormat": PRICE,
    }
    config["alphatrend"] = single_color(BLUE, pane=0)
    config["amat"] = single_color(ORANGE, pane=0)
    config["trendflex"] = single_color(CYAN, pane=2)
    config["cksp"] = {
        "pane": 0,
        "colors": {
            "dark": {"long": get_dark_color(GREEN), "short": get_dark_color(RED)},
            "light": {"long": GREEN, "short": RED},
        },
        "lineStyles": {"long": SOLID, "short": DASHED},
        "valueFormat": PRICE,
    }
    config["ttm_trend"] = single_color(YELLOW, pane=2)
    config["psar"] = {
        "pane": 0,
        "colors": {
            "dark": {
                "psar": get_dark_color(PURPLE),
                "long": get_dark_color(GREEN),
                "short": get_dark_color(RED),
            },
            "light": {"psar": PURPLE, "long": GREEN, "short": RED},
        },
        "lineStyles": {"psar": SOLID, "long": DASHED, "short": SOLID},
        "valueFormat": PRICE,
    }

    # ------------------------------------------------------------------
    # VOLATILITY (Overlay or separated pane)
    # ------------------------------------------------------------------
    config["atr"] = single_color(PINK, pane=2, value_format=NUMBER)
    config["natr"] = single_color(RED, pane=2)
    config["kc"] = {  # Keltner Channels
        "pane": 0,
        "colors": {
            "dark": {
                "upper": get_dark_color(CYAN),
                "middle": get_dark_color(SLATE),
                "lower": get_dark_color(CYAN),
            },
            "light": {"upper": CYAN, "middle": SLATE, "lower": CYAN},
        },
        "lineStyles": {"upper": SOLID, "middle": DASHED, "lower": SOLID},
        "valueFormat": PRICE,
    }
    config["donchian"] = {
        "pane": 0,
        "colors": {
            "dark": {
                "upper": get_dark_color(ROSE),
                "middle": get_dark_color(SLATE),
                "lower": get_dark_color(TEAL),
            },
            "light": {"upper": ROSE, "middle": SLATE, "lower": TEAL},
        },
        "lineStyles": {"upper": SOLID, "middle": DASHED, "lower": SOLID},
        "valueFormat": PRICE,
    }
    config["accbands"] = {
        "pane": 0,
        "colors": {
            "dark": {
                "upper": get_dark_color(LIME),
                "middle": get_dark_color(SLATE),
                "lower": get_dark_color(LIME),
            },
            "light": {"upper": LIME, "middle": SLATE, "lower": LIME},
        },
        "lineStyles": {"upper": SOLID, "middle": DASHED, "lower": SOLID},
        "valueFormat": PRICE,
    }
    config["aberration"] = {
        "pane": 0,
        "colors": {
            "dark": {
                "zg": get_dark_color(GREEN),
                "sg": get_dark_color(RED),
                "xg": get_dark_color(BLUE),
                "atr": get_dark_color(YELLOW),
            },
            "light": {"zg": GREEN, "sg": RED, "xg": BLUE, "atr": YELLOW},
        },
        "lineStyles": {"zg": SOLID, "sg": DASHED, "xg": SOLID, "atr": SOLID},
        "valueFormat": PRICE,
    }
    config["massi"] = single_color(PURPLE, pane=2)
    config["rvi"] = single_color(YELLOW, pane=2)
    config["thermo"] = {
        "pane": 2,
        "colors": {
            "dark": {
                "thermo": get_dark_color(BLUE),
                "ma": get_dark_color(RED),
                "long": get_dark_color(GREEN),
                "short": get_dark_color(RED),
            },
            "light": {"thermo": BLUE, "ma": RED, "long": GREEN, "short": RED},
        },
        "lineStyles": {"thermo": SOLID, "ma": DASHED, "long": SOLID, "short": SOLID},
        "valueFormat": PRICE,
    }
    config["ui"] = single_color(RED, pane=2)
    config["true_range"] = single_color(GREEN, pane=2)
    config["pdist"] = single_color(CYAN, pane=2)

    # ------------------------------------------------------------------
    # VOLUME (Overlay on Pane 1 or separated pane)
    # ------------------------------------------------------------------
    # VOL_SMA with different colors per length
    config["vol_sma"] = single_color(
        TEAL, pane=1, value_format=NUMBER
    )  # Default fallback
    config["vol_sma_5"] = single_color(LIME, pane=1, value_format=NUMBER)
    config["vol_sma_10"] = single_color(GREEN, pane=1, value_format=NUMBER)
    config["vol_sma_20"] = single_color(TEAL, pane=1, value_format=NUMBER)
    config["vol_sma_50"] = single_color(CYAN, pane=1, value_format=NUMBER)
    config["vol_sma_100"] = single_color(SKY, pane=1, value_format=NUMBER)
    config["vol_sma_200"] = single_color(BLUE, pane=1, value_format=NUMBER)
    config["obv"] = single_color(TEAL, pane=1, value_format=NUMBER)
    config["mfi"] = single_color(AMBER, pane=2, value_format=NUMBER)
    config["cmf"] = single_color(TEAL, pane=2, value_format=NUMBER)

    config["adosc"] = single_color(GREEN, pane=2)
    config["efi"] = single_color(ORANGE, pane=2)
    config["eom"] = single_color(BLUE, pane=2)
    config["pvo"] = {
        "pane": 2,
        "colors": {
            "dark": {
                "pvo": get_dark_color(BLUE),
                "signal": get_dark_color(RED),
                "hist": get_dark_color(GREEN),
            },
            "light": {"pvo": BLUE, "signal": RED, "hist": GREEN},
        },
        "lineStyles": {"pvo": SOLID, "signal": DASHED, "hist": SOLID},
        "valueFormat": PRICE,
    }
    config["vwma"] = single_color(RED, pane=0)
    config["aobv"] = {
        "pane": 1,
        "colors": {
            "dark": {
                "obv": get_dark_color(CYAN),
                "min": get_dark_color(GREEN),
                "max": get_dark_color(RED),
                "ema": get_dark_color(ORANGE),
            },
            "light": {"obv": CYAN, "min": GREEN, "max": RED, "ema": ORANGE},
        },
        "lineStyles": {"obv": SOLID, "min": DASHED, "max": SOLID, "ema": SOLID},
        "valueFormat": PRICE,
    }
    config["tsv"] = single_color(PURPLE, pane=2)
    config["ad"] = single_color(GREEN, pane=1)
    config["nvi"] = single_color(BLUE, pane=1)
    config["pvi"] = single_color(ORANGE, pane=1)
    config["pvol"] = single_color(CYAN, pane=1)
    config["pvr"] = single_color(PURPLE, pane=1)
    config["pvt"] = single_color(PINK, pane=1)
    config["kvo"] = {
        "pane": 2,
        "colors": {
            "dark": {"kvo": get_dark_color(BLUE), "signal": get_dark_color(RED)},
            "light": {"kvo": BLUE, "signal": RED},
        },
        "lineStyles": {"kvo": SOLID, "signal": DASHED},
        "valueFormat": PRICE,
    }

    # ------------------------------------------------------------------
    # STATISTICS (Pane 1)
    # ------------------------------------------------------------------
    config["stdev"] = single_color(BLUE, pane=2)
    config["variance"] = single_color(ORANGE, pane=2)
    config["zscore"] = single_color(CYAN, pane=2)
    config["skew"] = single_color(PURPLE, pane=2)
    config["kurtosis"] = single_color(PINK, pane=2)
    config["entropy"] = single_color(GREEN, pane=2)
    config["mad"] = single_color(RED, pane=2)
    config["median"] = single_color(YELLOW, pane=0)
    config["quantile"] = single_color(BLUE, pane=0)
    config["tos_stdevall"] = {
        "pane": 2,
        "colors": {
            "dark": {
                "lr": get_dark_color(BLUE),
                "upper": get_dark_color(GREEN),
                "lower": get_dark_color(RED),
            },
            "light": {"lr": BLUE, "upper": GREEN, "lower": RED},
        },
        "lineStyles": {"lr": SOLID, "upper": DASHED, "lower": SOLID},
        "valueFormat": PRICE,
    }

    # ------------------------------------------------------------------
    # CYCLE (Pane 1)
    # ------------------------------------------------------------------
    config["ebsw"] = single_color(ORANGE, pane=2)
    config["reflex"] = single_color(CYAN, pane=2)

    # ------------------------------------------------------------------
    # PERFORMANCE (Pane 1)
    # ------------------------------------------------------------------
    config["log_return"] = single_color(BLUE, pane=2)
    config["percent_return"] = single_color(GREEN, pane=2)

    # ------------------------------------------------------------------
    # MISC
    # ------------------------------------------------------------------
    config["pivot"] = {
        "pane": 0,
        "colors": {
            "dark": {
                "r1": get_dark_color(ROSE),
                "r2": get_dark_color(RED),
                "r3": get_dark_color(PINK),
                "s1": get_dark_color(TEAL),
                "s2": get_dark_color(GREEN),
                "s3": get_dark_color(LIME),
                "pivot": get_dark_color(INDIGO),
            },
            "light": {
                "r1": ROSE,
                "r2": RED,
                "r3": PINK,
                "s1": TEAL,
                "s2": GREEN,
                "s3": LIME,
                "pivot": INDIGO,
            },
        },
        "lineStyles": {
            "r1": SOLID,
            "r2": DASHED,
            "r3": SOLID,
            "s1": SOLID,
            "s2": DASHED,
            "s3": SOLID,
            "pivot": SOLID,
        },
        "priceLines": {
            "r1": "Resistance 1",
            "r2": "Resistance 2",
            "r3": "Resistance 3",
            "s1": "Support 1",
            "s2": "Support 2",
            "s3": "Support 3",
            "pivot": "Pivot",
        },
        "valueFormat": PRICE,
    }
    config["fib"] = {
        "pane": 0,
        "colors": {
            "dark": {
                "level_0": get_dark_color(RED),
                "level_236": get_dark_color(ROSE),
                "level_382": get_dark_color(ORANGE),
                "level_500": get_dark_color(AMBER),
                "level_618": get_dark_color(YELLOW),
                "level_786": get_dark_color(LIME),
                "level_100": get_dark_color(GREEN),
                "key": get_dark_color(INDIGO),
            },
            "light": {
                "level_0": RED,
                "level_236": ROSE,
                "level_382": ORANGE,
                "level_500": AMBER,
                "level_618": YELLOW,
                "level_786": LIME,
                "level_100": GREEN,
                "key": INDIGO,
            },
        },
        "lineStyles": {
            "level_0": SOLID,
            "level_236": DASHED,
            "level_382": SOLID,
            "level_500": SOLID,
            "level_618": DASHED,
            "level_786": SOLID,
            "level_100": SOLID,
            "key": SOLID,
        },
        "priceLines": {
            "level_0": "0%",
            "level_236": "23.6%",
            "level_382": "38.2%",
            "level_500": "50.0%",
            "level_618": "61.8%",
            "level_786": "78.6%",
            "level_100": "100%",
            "key": "Key",
        },
        "valueFormat": PRICE,
    }

    return config


DEFAULT_STYLING = _create_default_styling()
DEFAULT_CONFIG = IndicatorConfig()
