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
    generate_method_evaluations,
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
        end_date = today.strftime("%Y-%m-%d")

        # Short-term: 1 year daily data
        start_date_short = (today - relativedelta(years=1)).strftime("%Y-%m-%d")

        # Long-term: 5 years weekly data
        start_date_long = (today - relativedelta(years=5)).strftime("%Y-%m-%d")

        # 1. Fetch OHLCV Data
        ohlcv_daily = get_stock_ohlcv(
            symbol=symbol,
            start_date=start_date_short,
            end_date=end_date,
            interval="1D",
        )

        ohlcv_weekly = get_stock_ohlcv(
            symbol=symbol,
            start_date=start_date_long,
            end_date=end_date,
            interval="1W",
        )

        # 2. Fetch Company Info (for context)
        company_info = get_company_info(symbol)

        # 3. Calculate Technical Indicators
        short_term_data = self._process_ohlcv_data(ohlcv_daily, "short_term")
        long_term_data = self._process_ohlcv_data(ohlcv_weekly, "long_term")

        # 4. Build Context for LLM
        short_term_context = self._build_analysis_context(
            short_term_data, "ngắn hạn (1D, 1 năm)"
        )
        long_term_context = self._build_analysis_context(
            long_term_data, "dài hạn (1W, 5 năm)"
        )

        # 5. Construct Prompt
        prompt = self._build_prompt(
            symbol=symbol,
            company_name=company_name or company_info.get("name", ""),
            short_term_context=short_term_context,
            long_term_context=long_term_context,
            company_info=company_info,
        )

        # 6. Stream Analysis
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

            # 7. Process Recommendation
            if collected_recommendation_text.strip():
                recommendation = self._parse_recommendation(
                    collected_recommendation_text
                )
                yield json.dumps(recommendation) + "\n"

            # 8. Process Indicators Data
            if collected_indicators_text.strip():
                indicators_output = self._parse_indicators_output(
                    collected_indicators_text
                )
                if indicators_output:
                    yield json.dumps(indicators_output) + "\n"

            # 9. Send Technical Data with calculated indicators
            yield json.dumps(
                {
                    "type": "data",
                    "short_term": {
                        "timeframe": "1D (1 năm)",
                        "ohlcv": short_term_data.get("ohlcv_data", []),
                        "indicators": short_term_data.get("indicators", {}),
                        "methods": short_term_data.get("methods", []),
                    },
                    "long_term": {
                        "timeframe": "1W (5 năm)",
                        "ohlcv": long_term_data.get("ohlcv_data", []),
                        "indicators": long_term_data.get("indicators", {}),
                        "methods": long_term_data.get("methods", []),
                    },
                    # Legacy format for UI compatibility
                    "indicators": short_term_data.get("indicators", {}),
                    "gauges": self._build_gauges(short_term_data.get("indicators", {})),
                    "fibonacci": short_term_data.get("indicators", {}).get(
                        "fibonacci", {}
                    ),
                }
            ) + "\n"

        except Exception as e:
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"

    def _process_ohlcv_data(self, ohlcv_result: dict, timeframe: str) -> dict:
        """
        Process OHLCV data and calculate all technical indicators.

        Args:
            ohlcv_result: Result from get_stock_ohlcv
            timeframe: 'short_term' or 'long_term'

        Returns:
            Dictionary with indicators and method evaluations
        """
        if "error" in ohlcv_result or not ohlcv_result.get("data"):
            return {
                "indicators": {},
                "methods": [],
                "ohlcv_data": [],
                "error": ohlcv_result.get("error", "No data"),
            }

        ohlcv_data = ohlcv_result.get("data", [])

        # Create DataFrame
        df = create_ohlcv_dataframe(ohlcv_data)

        if df.empty:
            return {
                "indicators": {},
                "methods": [],
                "ohlcv_data": [],
                "error": "Empty DataFrame",
            }

        # Calculate all indicators
        indicators = calculate_all_indicators(df, timeframe)

        # Generate method evaluations
        methods = generate_method_evaluations(indicators, timeframe)

        return {
            "indicators": indicators,
            "methods": methods,
            "ohlcv_data": ohlcv_data,
        }

    def _build_analysis_context(self, data: dict, timeframe_label: str) -> str:
        """Build analysis context string for the prompt."""
        if data.get("error"):
            return f"\n### Phân tích {timeframe_label}\nLỗi: {data['error']}\n"

        indicators = data.get("indicators", {})
        methods = data.get("methods", [])

        ctx = f"\n### Phân tích {timeframe_label}\n"

        # Price info
        current_price = indicators.get("current_price")
        if current_price:
            price_change_pct = indicators.get("price_change_pct", 0)
            ctx += (
                f"**Giá hiện tại**: {current_price:,.0f} ({price_change_pct:+.2f}%)\n"
            )

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
Bạn là một chuyên gia phân tích kỹ thuật chứng khoán với nhiều năm kinh nghiệm.
Nhiệm vụ của bạn là phân tích kỹ thuật toàn diện cho mã cổ phiếu **{symbol}** ({company_name}).

**Thông tin công ty:**
- Ngành: {company_info.get('sector', 'N/A')}
- Vốn hóa: {company_info.get('marketCap', 'N/A'):,} tỷ VND
- Giá 52 tuần: {company_info.get('lowestPrice1Year', 'N/A')} - {company_info.get('highestPrice1Year', 'N/A')}

---

## Dữ liệu phân tích

{short_term_context}

---

{long_term_context}

---

## Yêu cầu phân tích

### 1. Phân tích ngắn hạn (Đầu tư giao dịch)
- Đánh giá xu hướng ngắn hạn dựa trên dữ liệu 1D trong 1 năm
- Xác định điểm vào/ra tiềm năng
- Phân tích các chỉ báo momentum (RSI, Stochastic, MACD)
- Xác định mức hỗ trợ/kháng cự ngắn hạn

### 2. Phân tích dài hạn (Tích lũy đầu tư)
- Đánh giá xu hướng dài hạn dựa trên dữ liệu 1W trong 5 năm
- Xác định vùng giá tích lũy hấp dẫn
- Phân tích đường MA dài hạn (SMA50, SMA200)
- Đánh giá sức mạnh xu hướng (ADX)

### 3. Tổng hợp khuyến nghị
- So sánh tín hiệu ngắn hạn vs dài hạn
- Đưa ra khuyến nghị cụ thể cho từng chiến lược
- Xác định các mức giá quan trọng cần theo dõi

**Lưu ý:**
- LUÔN trả lời bằng tiếng Việt
- Phân tích phải có căn cứ từ dữ liệu được cung cấp
- Giải thích rõ ràng từng phương pháp phân tích sử dụng

**BẮT BUỘC**: Ở cuối cùng của câu trả lời, cung cấp 2 thông tin sau:

{RECOMMENDATION_DELIMITER}
[Khuyến nghị tổng hợp: Mua mạnh/Mua/Nắm giữ/Theo dõi/Bán/Bán mạnh]

{INDICATORS_DELIMITER}
{{
  "short_term": {{
    "trend": "Tăng/Giảm/Đi ngang",
    "signal": "Mua/Bán/Trung tính",
    "confidence": 0.8
  }},
  "long_term": {{
    "trend": "Tăng/Giảm/Đi ngang",
    "signal": "Tích lũy/Chờ đợi/Phân phối",
    "confidence": 0.7
  }},
  "key_levels": {{
    "support": [giá hỗ trợ 1, giá hỗ trợ 2],
    "resistance": [giá kháng cự 1, giá kháng cự 2]
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
            return {"type": "analysis_summary", "summary": parsed}
        except Exception as e:
            print(f"Error parsing indicators output: {e}")
            return None
