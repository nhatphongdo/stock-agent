"""
Technical Analysis Agent for Stock Market Analysis.
Analyzes stock price data and technical indicators to provide trading insights.
Uses OHLCV data with pandas-ta library for indicator calculations.
"""

import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from app.llm.gemini_client import GeminiClient
from app.tools.vietcap_tools import get_stock_ohlcv, get_company_info
from app.tools.technical_indicators import (
    create_ohlcv_dataframe,
    calculate_all_indicators,
    detect_candlestick_patterns,
)
from app.tools.analysis_methods import generate_method_evaluations
from app.tools.price_patterns import (
    detect_chart_patterns,
    detect_support_resistance_zones,
    detect_supply_demand_zones,
)

# Constants for parsing delimiters
RECOMMENDATION_DELIMITER = "---RECOMMENDATION_LABEL---"
INDICATORS_DELIMITER = "---INDICATORS---"


class TechnicalAnalysisAgent:
    """
    Agent for performing technical analysis on stocks.
    Uses OHLCV data and calculates technical indicators using pandas-ta.
    Provides dual-timeframe analysis: short-term (1D/1 year) and long-term (1W/5 years).
    """

    def __init__(self, name: str, client: GeminiClient):
        self.name = name
        self.client = client

    async def run(
        self,
        symbol: str,
        company_name: str = "",
    ):
        """
        Run technical analysis on a stock with dual-timeframe analysis.

        Args:
            symbol: Stock ticker symbol (e.g., 'VNM', 'SSI')
            company_name: Company name for context

        Yields:
            JSON strings with analysis content, recommendations, and data
        """
        # Calculate date ranges
        today = datetime.now()
        end_date = (today + relativedelta(days=1)).strftime("%Y-%m-%d")

        # Long-term: 5 years of data
        start_date_long = (today - relativedelta(years=5)).strftime("%Y-%m-%d")

        # 1. Fetch 5-year daily OHLCV data once (single API call)
        ohlcv_all_daily = get_stock_ohlcv(
            symbol=symbol,
            start_date=start_date_long,
            end_date=end_date,
            interval="1D",
        )

        # 2. Filter and aggregate data for different timeframes
        ohlcv_short_term, ohlcv_weekly, ohlcv_long_daily = self._prepare_timeframe_data(
            ohlcv_all_daily, today
        )

        # 3. Fetch Company Info (for context)
        company_info = get_company_info(symbol)

        # 4. Calculate Technical Indicators
        short_term_data = self._process_ohlcv_data(ohlcv_short_term, "short_term")
        long_term_data = self._process_ohlcv_data(
            ohlcv_weekly, "long_term", daily_data=ohlcv_long_daily
        )

        # 5. Send Technical Data with calculated indicators
        yield json.dumps(
            {
                "type": "data",
                "short_term": {
                    "timeframe": "1D (1 năm)",
                    "ohlcv": short_term_data.get("ohlcv", []),
                    "indicators": short_term_data.get("indicators", {}),
                    "methods": short_term_data.get("methods", []),
                    "gauges": short_term_data.get("gauges", {}),
                    "candlestick_patterns": short_term_data.get(
                        "candlestick_patterns", []
                    ),
                    "chart_patterns": short_term_data.get("chart_patterns", []),
                    "sr_zones": short_term_data.get("sr_zones", {}),
                    "sd_zones": short_term_data.get("sd_zones", {}),
                },
                "long_term": {
                    "timeframe": "1W (5 năm)",
                    "ohlcv": long_term_data.get("ohlcv", []),
                    "indicators": long_term_data.get("indicators", {}),
                    "methods": long_term_data.get("methods", []),
                    "gauges": long_term_data.get("gauges", {}),
                    "candlestick_patterns": long_term_data.get(
                        "candlestick_patterns", []
                    ),
                    "chart_patterns": long_term_data.get("chart_patterns", []),
                    "sr_zones": long_term_data.get("sr_zones", {}),
                    "sd_zones": long_term_data.get("sd_zones", {}),
                },
            }
        ) + "\n"

        # 6. Build Context for LLM
        short_term_context = self._build_analysis_context(
            short_term_data, "ngắn hạn (1D, 1 năm)"
        )
        long_term_context = self._build_analysis_context(
            long_term_data, "dài hạn (1W, 5 năm)"
        )

        # 7. Construct Prompt
        prompt = self._build_prompt(
            symbol=symbol,
            company_name=company_name or company_info.get("name", ""),
            short_term_context=short_term_context,
            long_term_context=long_term_context,
            company_info=company_info,
        )

        # 8. Stream Analysis
        is_parsing_recommendation = False
        collected_recommendation_text = ""
        is_parsing_indicators = False
        collected_indicators_text = ""

        try:
            async for chunk in self.client.generate_content(prompt):
                # Detect Start of Recommendation Block
                if RECOMMENDATION_DELIMITER in chunk:
                    parts = chunk.split(RECOMMENDATION_DELIMITER)
                    if parts[0].strip():
                        yield json.dumps({"type": "content", "chunk": parts[0]}) + "\n"

                    is_parsing_recommendation = True
                    is_parsing_indicators = False

                    if len(parts) > 1:
                        remaining = parts[1]
                        if INDICATORS_DELIMITER in remaining:
                            rec_part, ind_part = remaining.split(
                                INDICATORS_DELIMITER, 1
                            )
                            collected_recommendation_text += rec_part
                            is_parsing_recommendation = False
                            is_parsing_indicators = True
                            collected_indicators_text += ind_part
                        else:
                            collected_recommendation_text += remaining
                    continue

                # Detect Start of Indicators Block
                if INDICATORS_DELIMITER in chunk:
                    parts = chunk.split(INDICATORS_DELIMITER)

                    if is_parsing_recommendation:
                        collected_recommendation_text += parts[0]
                        is_parsing_recommendation = False
                    elif parts[0].strip():
                        yield json.dumps({"type": "content", "chunk": parts[0]}) + "\n"

                    is_parsing_indicators = True
                    if len(parts) > 1:
                        collected_indicators_text += parts[1]
                    continue

                if is_parsing_recommendation:
                    collected_recommendation_text += chunk
                    if INDICATORS_DELIMITER in collected_recommendation_text:
                        rec_part, ind_part = collected_recommendation_text.split(
                            INDICATORS_DELIMITER, 1
                        )
                        collected_recommendation_text = rec_part
                        is_parsing_recommendation = False
                        is_parsing_indicators = True
                        collected_indicators_text += ind_part

                elif is_parsing_indicators:
                    collected_indicators_text += chunk
                else:
                    # Normal content stream
                    yield json.dumps({"type": "content", "chunk": chunk}) + "\n"

            # 9. Process Recommendation
            if collected_recommendation_text.strip():
                recommendation = self._parse_recommendation(
                    collected_recommendation_text
                )
                yield json.dumps(recommendation) + "\n"

            # 10. Process Indicators Data
            if collected_indicators_text.strip():
                indicators_output = self._parse_indicators_output(
                    collected_indicators_text
                )
                if indicators_output:
                    yield json.dumps(indicators_output) + "\n"

        except Exception as e:
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"

    def _prepare_timeframe_data(
        self, ohlcv_all_daily: dict, today: datetime
    ) -> tuple[dict, dict, dict]:
        """
        Prepare data for different timeframes from 5-year daily data.

        Args:
            ohlcv_all_daily: 5-year daily OHLCV data from API
            today: Current datetime

        Returns:
            Tuple of (short_term_daily, weekly_aggregated, long_daily_2y)
        """
        if "error" in ohlcv_all_daily or not ohlcv_all_daily.get("data"):
            empty_result = {
                "data": [],
                "error": ohlcv_all_daily.get("error", "No data"),
            }
            return empty_result, empty_result, empty_result

        all_data = ohlcv_all_daily.get("data", [])

        # Filter dates - normalize to start of day for correct comparison
        one_year_ago = (today - relativedelta(years=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        two_years_ago = (today - relativedelta(years=2)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # 1. Short-term: last 1 year of daily data
        short_term_data = [
            candle
            for candle in all_data
            if datetime.strptime(candle["time"][:10], "%Y-%m-%d") >= one_year_ago
        ]

        # 2. Long-term daily: last 2 years (for indicator calculations)
        long_daily_data = [
            candle
            for candle in all_data
            if datetime.strptime(candle["time"][:10], "%Y-%m-%d") >= two_years_ago
        ]

        # 3. Aggregate all 5-year daily data to weekly
        weekly_data = self._aggregate_to_weekly(all_data)

        return (
            {"data": short_term_data},
            {"data": weekly_data},
            {"data": long_daily_data},
        )

    def _aggregate_to_weekly(self, daily_data: list) -> list:
        """
        Aggregate daily OHLCV data to weekly using pandas resample.

        Args:
            daily_data: List of daily OHLCV candles

        Returns:
            List of weekly OHLCV candles
        """
        if not daily_data:
            return []

        import pandas as pd

        # Create DataFrame from daily data
        df = pd.DataFrame(daily_data)
        df["time"] = pd.to_datetime(df["time"])
        df.set_index("time", inplace=True)

        # Resample to weekly (W-MON means week ending on Monday, so use W-SUN for week starting Monday)
        weekly = df.resample("W-MON", label="left", closed="left").agg(
            {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum",
            }
        )

        # Drop weeks with no data and reset index
        weekly = weekly.dropna()
        weekly = weekly.reset_index()
        weekly["time"] = weekly["time"].dt.strftime("%Y-%m-%d")

        return weekly.to_dict("records")

    def _process_ohlcv_data(
        self, ohlcv_result: dict, timeframe: str, daily_data: dict = None
    ) -> dict:
        """
        Process OHLCV data and calculate all technical indicators.

        Args:
            ohlcv_result: Result from get_stock_ohlcv
            timeframe: 'short_term' or 'long_term'
            daily_data: Optional daily OHLCV data for long-term indicators that need more granularity

        Returns:
            Dictionary with indicators and method evaluations
        """
        if "error" in ohlcv_result or not ohlcv_result.get("data"):
            return {
                "indicators": {},
                "methods": [],
                "ohlcv": [],
                "error": ohlcv_result.get("error", "No data"),
            }

        ohlcv_data = ohlcv_result.get("data", [])

        # Create DataFrame
        df = create_ohlcv_dataframe(ohlcv_data)

        if df.empty:
            return {
                "indicators": {},
                "methods": [],
                "ohlcv": [],
                "error": "Empty DataFrame",
            }

        # Calculate all indicators
        indicators = calculate_all_indicators(df, timeframe)

        # For long-term analysis, also create DataFrame from daily data if available
        df_daily = None
        if daily_data and daily_data.get("data"):
            df_daily = create_ohlcv_dataframe(daily_data.get("data", []))

        # Use daily data for long-term if available (more data points for indicators)
        daily_indicators = (
            indicators
            if timeframe == "short_term" or df_daily is None or df_daily.empty
            else calculate_all_indicators(df_daily, timeframe)
        )

        # Generate method evaluations
        methods = generate_method_evaluations(daily_indicators, timeframe)

        # 4. Advanced Pattern Detection
        # Candlestick Patterns
        candlestick_patterns = detect_candlestick_patterns(df)

        # Geometric Chart Patterns (Double Top/Bottom, Head & Shoulders, etc.)
        chart_patterns = detect_chart_patterns(df)

        # Support/Resistance Zones (Clustering)
        sr_zones = detect_support_resistance_zones(df)

        # Supply/Demand Zones
        sd_zones = detect_supply_demand_zones(df)

        return {
            "indicators": indicators,
            "methods": methods,
            "gauges": self._build_gauges(indicators),
            "ohlcv": ohlcv_data,
            "daily_ohlcv": daily_data.get("data", []) if daily_data else [],
            "candlestick_patterns": candlestick_patterns,
            "chart_patterns": chart_patterns,
            "sr_zones": sr_zones,
            "sd_zones": sd_zones,
        }

    def _build_analysis_context(self, data: dict, timeframe_label: str) -> str:
        """Build analysis context string for the prompt."""
        if data.get("error"):
            return f"\n### Phân tích {timeframe_label}\nLỗi: {data['error']}\n"

        indicators = data.get("indicators", {})
        methods = data.get("methods", [])
        ohlcv = data.get("ohlcv", [])

        ctx = f"\n### Phân tích {timeframe_label}\n"

        # Price info
        current_price = indicators.get("current_price")
        if current_price:
            price_change_pct = indicators.get("price_change_pct", 0)
            ctx += (
                f"**Giá hiện tại**: {current_price:,.0f} ({price_change_pct:+.2f}%)\n"
            )

        # Add recent OHLCV data (last 30 candles)
        if ohlcv:
            recent_ohlcv = ohlcv[-30:]  # Last 30 candles
            ctx += (
                "\n**Dữ liệu giá gần đây (10 phiên cuối trong 30 phiên phân tích):**\n"
            )
            ctx += "| Ngày | Open | High | Low | Close | Volume |\n"
            ctx += "|------|------|------|-----|-------|--------|\n"
            for candle in recent_ohlcv[-10:]:  # Show last 10 for brevity
                date = candle.get("time", "")[:10]
                ctx += f"| {date} | {candle.get('open', 0):,.0f} | {candle.get('high', 0):,.0f} | {candle.get('low', 0):,.0f} | {candle.get('close', 0):,.0f} | {candle.get('volume', 0):,.0f} |\n"

            # Price action summary
            if len(recent_ohlcv) >= 5:
                last_5_closes = [c.get("close", 0) for c in recent_ohlcv[-5:]]
                last_5_volumes = [c.get("volume", 0) for c in recent_ohlcv[-5:]]
                avg_vol_20 = sum(c.get("volume", 0) for c in recent_ohlcv[-20:]) / min(
                    20, len(recent_ohlcv)
                )

                ctx += f"\n**Tóm tắt 5 phiên gần nhất:**\n"
                ctx += f"- Close trend: {[f'{c:,.0f}' for c in last_5_closes]}\n"
                if avg_vol_20 > 0:
                    vol_ratio = last_5_volumes[-1] / avg_vol_20 * 100
                    ctx += f"- Volume gần nhất vs TB20: {last_5_volumes[-1]:,.0f} / {avg_vol_20:,.0f} ({vol_ratio:.0f}%)\n"

        # Key indicator values with interpretation
        ctx += "\n**Giá trị chỉ báo kỹ thuật:**\n"

        # RSI with status
        rsi_data = indicators.get("rsi", {})
        if rsi_data.get("value"):
            rsi_val = rsi_data["value"]
            if rsi_val < 30:
                rsi_status = "🔴 quá bán"
            elif rsi_val > 70:
                rsi_status = "🟢 quá mua"
            else:
                rsi_status = "🟡 trung tính"
            ctx += f"- **RSI(14)**: {rsi_val:.1f} ({rsi_status})\n"

        # MACD with signal
        macd = indicators.get("macd", {})
        if macd:
            macd_line = macd.get("macd_line", 0)
            signal_line = macd.get("signal_line", 0)
            histogram = macd.get("histogram", 0)
            if macd_line and signal_line:
                macd_signal = (
                    "🟢 MACD trên Signal"
                    if macd_line > signal_line
                    else "🔴 MACD dưới Signal"
                )
                hist_trend = "tăng" if histogram and histogram > 0 else "giảm"
                ctx += f"- **MACD**: Line={macd_line:.2f}, Signal={signal_line:.2f}, Histogram={histogram:.2f} ({macd_signal}, histogram {hist_trend})\n"

        # Stochastic
        stoch = indicators.get("stochastic", {})
        if stoch:
            k = stoch.get("k")
            d = stoch.get("d")
            if k is not None and d is not None:
                if k < 20:
                    stoch_status = "quá bán"
                elif k > 80:
                    stoch_status = "quá mua"
                else:
                    stoch_status = "trung tính"
                ctx += f"- **Stochastic**: K={k:.1f}, D={d:.1f} ({stoch_status})\n"

        # ADX
        adx_data = indicators.get("adx", {})
        if adx_data:
            adx = adx_data.get("adx")
            plus_di = adx_data.get("plus_di")
            minus_di = adx_data.get("minus_di")
            if adx is not None:
                trend_strength = "mạnh" if adx > 25 else "yếu"
                trend_dir = (
                    "tăng" if plus_di and minus_di and plus_di > minus_di else "giảm"
                )
                ctx += f"- **ADX**: {adx:.1f} (xu hướng {trend_strength}, hướng {trend_dir})\n"

        # Bollinger Bands
        bb = indicators.get("bollinger_bands", {})
        if bb and current_price:
            upper = bb.get("upper")
            middle = bb.get("middle")
            lower = bb.get("lower")
            bandwidth = bb.get("bandwidth")
            if upper and middle and lower:
                if current_price > middle + (upper - middle) * 0.7:
                    position = "gần upper band"
                elif current_price < middle - (middle - lower) * 0.7:
                    position = "gần lower band"
                else:
                    position = "trong kênh"
                bw_str = f", Bandwidth={bandwidth:.1f}%" if bandwidth else ""
                ctx += f"- **Bollinger Bands**: Upper={upper:,.0f}, Middle={middle:,.0f}, Lower={lower:,.0f} (Giá {position}{bw_str})\n"

        # Moving Averages position
        sma20 = indicators.get("sma20")
        sma50 = indicators.get("sma50")
        sma200 = indicators.get("sma200")
        if sma20 or sma50 or sma200:
            ctx += "- **Moving Averages**: "
            ma_parts = []
            if sma20 and current_price:
                pos = "trên" if current_price > sma20 else "dưới"
                ma_parts.append(f"SMA20={sma20:,.0f} (giá {pos})")
            if sma50 and current_price:
                pos = "trên" if current_price > sma50 else "dưới"
                ma_parts.append(f"SMA50={sma50:,.0f} (giá {pos})")
            if sma200 and current_price:
                pos = "trên" if current_price > sma200 else "dưới"
                ma_parts.append(f"SMA200={sma200:,.0f} (giá {pos})")
            ctx += ", ".join(ma_parts) + "\n"

        # ATR for volatility
        atr = indicators.get("atr")
        if atr and current_price:
            atr_pct = atr / current_price * 100
            ctx += f"- **ATR(14)**: {atr:,.0f} ({atr_pct:.2f}% của giá)\n"

        # Add method evaluations
        if methods:
            ctx += "\n**Các phương pháp phân tích:**\n"
            for m in methods:
                signal_emoji = (
                    "🟢"
                    if m["signal"] == "Bullish"
                    else "🔴" if m["signal"] == "Bearish" else "🟡"
                )
                ctx += f"\n**{m['name']}** ({m['category']}) {signal_emoji}\n"
                ctx += f"- Mô tả: {m['description']}\n"
                ctx += f"- Đánh giá: {m['evaluation']}\n"
                ctx += f"- Tín hiệu: {m['signal']}\n"

        # Support/Resistance
        pivot = indicators.get("pivot_points", {})
        fib = indicators.get("fibonacci", {})

        if pivot:
            ctx += f"\n**Pivot Points**: Pivot={pivot.get('pivot'):,.0f}, R1={pivot.get('r1'):,.0f}, S1={pivot.get('s1'):,.0f}\n"

        if fib:
            ctx += f"**Fibonacci**: 38.2%={fib.get('level_382'):,.0f}, 50%={fib.get('level_500'):,.0f}, 61.8%={fib.get('level_618'):,.0f}\n"

        # Advanced Patterns
        candlestick_patterns = data.get("candlestick_patterns", [])
        chart_patterns = data.get("chart_patterns", [])
        sr_zones = data.get("sr_zones", {})

        one_week_ago = datetime.now() - timedelta(days=7)
        if candlestick_patterns:
            # Filter patterns from last 1 week
            recent_patterns = [
                p
                for p in candlestick_patterns
                if p.get("date")
                and datetime.strptime(p["date"][:10], "%Y-%m-%d") >= one_week_ago
            ]
            if recent_patterns:
                ctx += "\n**Mô hình nến (Candlestick Patterns - 1 tuần gần nhất):**\n"
                ctx += "| Ngày | Mô hình | Tín hiệu | Giá |\n"
                ctx += "|---|---|---|---|\n"
                for p in recent_patterns:
                    ctx += f"| {p.get('date', '')} | {p.get('name', '')} | {p.get('signal', '')} | {p.get('price', '')} |\n"

        if chart_patterns:
            # Filter patterns that ended within last 1 week
            recent_chart_patterns = [
                p
                for p in chart_patterns
                if p.get("end_date")
                and datetime.strptime(p["end_date"][:10], "%Y-%m-%d") >= one_week_ago
            ]
            if recent_chart_patterns:
                ctx += "\n**Mô hình biểu đồ (Chart Patterns - 1 tuần gần nhất):**\n"
                ctx += "| Mô hình | Tín hiệu | Ngày bắt đầu | Ngày kết thúc | Neckline | Target | Peaks | Stop | Độ tin cậy |\n"
                ctx += "|---|---|---|---|---|---|---|---|---|\n"
                for p in recent_chart_patterns:
                    ctx += f"| {p.get('type', '')} | {p.get('signal', '')} | {p.get('start_date', '')} | {p.get('end_date', '')} | {p.get('neckline', 'N/A')} | {p.get('target', 'N/A')} | {', '.join(str(n) for n in p.get('peaks', []))} | {p.get('stop', 'N/A')} | {p.get('confidence', 'N/A')} |\n"

        if sr_zones:
            ctx += "\n**Vùng Hỗ trợ/Kháng cự quan trọng (Advanced S/R):**\n"
            supports = sr_zones.get("support_zones", [])
            resistances = sr_zones.get("resistance_zones", [])

            ctx += "| Loại | Giá | Range | Độ mạnh |\n"
            ctx += "|---|---|---|---|\n"

            if supports:
                for z in supports[:3]:
                    ctx += f"| Hỗ trợ | {z.get('price', 'N/A')} | {', '.join(str(n) for n in z.get('range', []))} | {z.get('strength', 'N/A')} |\n"

            if resistances:
                for z in resistances[:3]:
                    ctx += f"| Kháng cự | {z.get('price', 'N/A')} | {', '.join(str(n) for n in z.get('range', []))} | {z.get('strength', 'N/A')} |\n"

        return ctx

    def _build_gauges(self, indicators: dict) -> dict:
        """Build gauges for UI compatibility."""
        methods_signals = []

        # RSI
        rsi_data = indicators.get("rsi", {})
        rsi = rsi_data.get("value")
        if rsi is not None:
            if rsi < 30:
                methods_signals.append("buy")
            elif rsi > 70:
                methods_signals.append("sell")
            else:
                methods_signals.append("neutral")

        # MACD
        macd = indicators.get("macd", {})
        if macd.get("histogram"):
            if macd["histogram"] > 0:
                methods_signals.append("buy")
            else:
                methods_signals.append("sell")

        # MA position
        if indicators.get("price_vs_sma50") == "above":
            methods_signals.append("buy")
        elif indicators.get("price_vs_sma50") == "below":
            methods_signals.append("sell")

        # Calculate summary
        buy_count = methods_signals.count("buy")
        sell_count = methods_signals.count("sell")
        total = len(methods_signals)

        if total == 0:
            summary_label = "Neutral"
            summary_value = 0
        elif buy_count > sell_count:
            summary_label = "Strong Buy" if buy_count > total * 0.7 else "Buy"
            summary_value = buy_count / total
        elif sell_count > buy_count:
            summary_label = "Strong Sell" if sell_count > total * 0.7 else "Sell"
            summary_value = -sell_count / total
        else:
            summary_label = "Neutral"
            summary_value = 0

        return {
            "summary": {"label": summary_label, "value": summary_value},
            "movingAverage": {
                "label": (
                    "Buy" if indicators.get("price_vs_sma50") == "above" else "Sell"
                ),
                "value": 1 if indicators.get("price_vs_sma50") == "above" else -1,
            },
            "oscillator": {
                "label": (
                    "Buy"
                    if rsi is not None and rsi < 30
                    else "Sell" if rsi is not None and rsi > 70 else "Neutral"
                ),
                "value": rsi if rsi is not None else 50,
            },
        }

    def _build_prompt(
        self,
        symbol: str,
        company_name: str,
        short_term_context: str,
        long_term_context: str,
        company_info: dict,
    ) -> str:
        """Build the complete prompt for technical analysis."""
        prompt = f"""
Bạn là một chuyên gia phân tích kỹ thuật chứng khoán hàng đầu (CMT Charterholder) với nhiều năm kinh nghiệm tại các quỹ đầu tư lớn.
Nhiệm vụ của bạn là phân tích kỹ thuật chuyên sâu và đưa ra khuyến nghị hành động cụ thể cho mã cổ phiếu **{symbol}** ({company_name}).

**Thông tin công ty:**
- Ngành: {company_info.get('sector', 'N/A')}
- Vốn hóa: {company_info.get('marketCap', 'N/A'):,} tỷ VND
- Giá 52 tuần: {company_info.get('lowestPrice1Year', 'N/A')} - {company_info.get('highestPrice1Year', 'N/A')}

---

## DỮ LIỆU PHÂN TÍCH KỸ THUẬT

{short_term_context}

---

{long_term_context}

---

## YÊU CẦU PHÂN TÍCH

### 1. Tổng quan thị trường và cổ phiếu
- Vị thế hiện tại của cổ phiếu trong xu hướng lớn (uptrend/downtrend/sideways)
- So sánh diễn biến giá gần đây với các mức hỗ trợ/kháng cự quan trọng
- Đánh giá thanh khoản và sự tham gia của dòng tiền (volume analysis)

### 2. Phân tích Xu hướng & Động lượng (Trend & Momentum)
- Xác định xu hướng chính (Ngắn hạn & Dài hạn) dựa trên MA và cấu trúc đỉnh/đáy
- Đánh giá sức mạnh xu hướng qua ADX, Momentum, và độ dốc của các MA
- Phân tích sự phân kỳ (Divergence) của RSI, MACD nếu có
- Xác định giai đoạn thị trường: tích lũy, phân phối, markup, markdown

### 3. Phân tích Hành động giá & Mô hình (Price Action & Patterns)
- Đánh giá price action dựa trên dữ liệu OHLCV gần đây
- Đánh giá các mô hình nến (Candlestick) xuất hiện gần đây và ý nghĩa
- Phân tích các mô hình biểu đồ (Chart Patterns) nếu có
- Xác định vùng cung/cầu quan trọng dựa trên Pivot Points, Fibonacci, và S/R zones

### 4. Đánh giá rủi ro và cơ hội
- Xác định các yếu tố rủi ro kỹ thuật (breakdown levels, bearish signals)
- Xác định các yếu tố cơ hội (breakout potential, bullish signals)
- Đánh giá tỷ lệ Risk/Reward dựa trên các mức giá quan trọng

### 5. Kịch bản & Khuyến nghị giao dịch
- **Kịch bản Tích cực (Bullish)**: Điều kiện kích hoạt, mục tiêu giá ngắn/trung hạn
- **Kịch bản Tiêu cực (Bearish)**: Mức cảnh báo rủi ro, điểm cắt lỗ
- **Khuyến nghị hành động**: Mua mạnh/Mua/Nắm giữ/Theo dõi/Bán/Bán mạnh. Giải thích lý do cốt lõi.

### 6. Giá đề xuất cụ thể
Dựa trên phân tích trên, đề xuất các mức giá cụ thể:
- **Giá mua đề xuất**: Mức giá tốt để vào lệnh mua (nếu là tín hiệu mua), có thể có nhiều mức (mua ngay, canh mua)
- **Giá bán/chốt lời**: Mức giá mục tiêu để chốt lời (target 1, target 2)
- **Giá cắt lỗ**: Mức giá cắt lỗ nếu xu hướng đảo chiều
- **Tỷ lệ Risk/Reward**: Tính toán Risk/Reward ratio

**Lưu ý quan trọng:**
- LUÔN trả lời bằng tiếng Việt chuyên ngành nhưng dễ hiểu
- Phân tích phải khách quan, dựa trên dữ liệu (không đoán mò)
- Nếu dữ liệu mâu thuẫn, hãy nêu rõ sự xung đột và ưu tiên tín hiệu Price Action/Volume
- Giá đề xuất phải dựa trên các mức hỗ trợ/kháng cự thực tế từ dữ liệu

**BẮT BUỘC**: Ở cuối cùng của câu trả lời, CUNG CẤP ĐÚNG ĐỊNH DẠNG JSON sau (không thêm bớt):

{RECOMMENDATION_DELIMITER}
[Khuyến nghị tổng hợp: Mua mạnh/Mua/Nắm giữ/Theo dõi/Bán/Bán mạnh]

{INDICATORS_DELIMITER}
{{
  "short_term": {{
    "trend": "Tăng/Giảm/Đi ngang",
    "signal": "Tích cực/Tiêu cực/Trung tính",
    "confidence": 0.85
  }},
  "long_term": {{
    "trend": "Tăng/Giảm/Đi ngang",
    "signal": "Tích lũy/Phân phối/Chờ đợi",
    "confidence": 0.75
  }},
  "key_levels": {{
    "support": [giá hỗ trợ 1, giá hỗ trợ 2],
    "resistance": [giá kháng cự 1, giá kháng cự 2]
  }},
  "price_targets": {{
    "entry": giá mua đề xuất,
    "target_1": mục tiêu 1,
    "target_2": mục tiêu 2,
    "stop_loss": giá cắt lỗ,
    "risk_reward": tỷ lệ R:R (số thập phân),
    "confidence": "High/Medium/Low",
    "confidence_reason": "Lý do đánh giá mức độ tin cậy ngắn gọn"
  }}
}}
"""
        return prompt

    def _parse_recommendation(self, text: str) -> dict:
        """Parse recommendation from collected text."""
        label = text.strip().replace("`", "").replace("*", "").strip()

        # Determine color based on recommendation
        color = "gray"
        l_lower = label.lower()

        strong_buy_keywords = ["mua mạnh", "strong buy"]
        buy_keywords = ["mua", "tích lũy", "buy", "long"]
        strong_sell_keywords = ["bán mạnh", "strong sell"]
        sell_keywords = ["bán", "chốt lời", "sell", "short"]
        hold_keywords = ["nắm giữ", "hold", "giữ"]
        watch_keywords = ["theo dõi", "chờ", "quan sát", "watch"]

        if any(k in l_lower for k in strong_buy_keywords):
            color = "emerald"
        elif any(k in l_lower for k in buy_keywords):
            color = "green"
        elif any(k in l_lower for k in strong_sell_keywords):
            color = "rose"
        elif any(k in l_lower for k in sell_keywords):
            color = "red"
        elif any(k in l_lower for k in hold_keywords):
            color = "blue"
        elif any(k in l_lower for k in watch_keywords):
            color = "yellow"

        return {"type": "recommendation", "label": label, "color": color}

    def _parse_indicators_output(self, text: str) -> dict | None:
        """Parse indicators JSON from collected text."""
        try:
            json_text = text.strip()
            if "```" in json_text:
                parts = json_text.split("```")
                if len(parts) >= 3:
                    json_text = parts[1]
                    if json_text.startswith("json"):
                        json_text = json_text[4:]

            parsed = json.loads(json_text.strip())

            # Validate and ensure price_targets structure has required fields
            if "price_targets" in parsed:
                pt = parsed["price_targets"]
                # Ensure confidence field exists with default
                if "confidence" not in pt:
                    pt["confidence"] = "Medium"
                if "confidence_reason" not in pt:
                    pt["confidence_reason"] = ""
                # Ensure risk_reward is a number
                if "risk_reward" in pt and not isinstance(
                    pt["risk_reward"], (int, float)
                ):
                    try:
                        pt["risk_reward"] = float(pt["risk_reward"])
                    except (ValueError, TypeError):
                        pt["risk_reward"] = 0

            return {"type": "analysis_summary", "summary": parsed}
        except Exception as e:
            print(f"Error parsing indicators output: {e}")
            return None
