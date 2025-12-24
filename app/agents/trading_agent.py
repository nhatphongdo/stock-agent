from datetime import datetime, timedelta
from app.llm.gemini_client import GeminiClient
from app.tools.vietcap_tools import (
    VIETCAP_TOOLS,
    get_top_tickers,
    get_company_info,
    get_ohlcv_data,
    get_technical_indicators,
    get_trending_news,
    get_coverage_universe,
    get_financial_ratios,
    get_annual_return,
)
import json
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Constant for parsing delimiter
REASONING_DELIMITER = "---REASONING---"
FINAL_DELIMITER = "---FINAL---"

def fetch_market_context(portfolio_stocks: list[str] = None):
    """
    Pre-fetch essential market data to reduce model tool calls.
    Returns a structured context with top stocks, technicals, and news.

    Args:
        portfolio_stocks: List of stock tickers from user's portfolio to include in prefetch
    """
    context = {
        "stocks_data": [],
        "trending_news": None,
    }

    try:
        # 1. Get top tickers (9 positive, 9 negative from All)
        top_result = get_top_tickers(top_pos=9, top_neg=9, group="all")
        tickers = set()

        if "ticker_info" in top_result:
            tickers.update([t["ticker"] for t in top_result["ticker_info"]])

        # 2. Get coverage universe and filter BUY-rated stocks
        coverage = get_coverage_universe()
        if coverage and "data" in coverage:
            buy_stocks = [s for s in coverage["data"] if s.get("rating") == "BUY"][:10]
            tickers.update([s.get("ticker") for s in buy_stocks if s.get("ticker")])

        # 3. Add portfolio stocks if provided
        if portfolio_stocks:
            # Extract ticker symbols from portfolio format "TICKER(cost)" or just "TICKER"
            for stock in portfolio_stocks:
                ticker = stock.split('(')[0].strip().upper()
                if ticker:
                    tickers.add(ticker)

        # Convert to list for processing
        tickers = list(tickers)

        # 3. Fetch details for each ticker (parallel execution)
        if tickers:
            with ThreadPoolExecutor(max_workers=10) as executor:
                # Fetch company info
                company_futures = {ticker: executor.submit(get_company_info, ticker) for ticker in tickers}
                # Fetch technical indicators
                tech_futures = {ticker: executor.submit(get_technical_indicators, ticker, "ONE_DAY") for ticker in tickers}
                # Fetch OHLCV (last 1 day only)
                ohlcv_futures = {ticker: executor.submit(get_ohlcv_data, ticker, 1, "ONE_DAY") for ticker in tickers}
                # Fetch financial ratios
                ratio_futures = {ticker: executor.submit(get_financial_ratios, ticker, 10) for ticker in tickers}
                # Fetch annual return
                return_futures = {ticker: executor.submit(get_annual_return, ticker, 10) for ticker in tickers}

                for ticker in tickers:
                    stock_data = {"ticker": ticker}

                    # Company info
                    try:
                        company = company_futures[ticker].result(timeout=10)
                        if company and "data" in company:
                            d = company["data"]
                            stock_data["company"] = {
                                "name": d.get("viOrganName", d.get("enOrganName", "")),
                                "sector": d.get("sectorVn", d.get("sector", "")),
                                "currentPrice": d.get("currentPrice"),
                                "rating": d.get("rating"),
                                "analyst": d.get("analyst"),
                                "marketCap": d.get("marketCap"),
                                "highestPrice1Year": d.get("highestPrice1Year"),
                                "lowestPrice1Year": d.get("lowestPrice1Year"),
                                "averageMatchValue1Month": d.get("averageMatchValue1Month"),
                                "averageMatchVolume1Month": d.get("averageMatchVolume1Month"),
                            }
                    except:
                        pass

                    # Technical indicators
                    try:
                        tech = tech_futures[ticker].result(timeout=10)
                        if tech and "data" in tech:
                            d = tech["data"]

                            # Extract all oscillators as dict
                            oscillators = {osc.get("name"): {"value": osc.get("value"), "rating": osc.get("rating")}
                                          for osc in d.get("oscillators", []) if osc.get("name")}

                            # Extract all moving averages as dict
                            moving_averages = {ma.get("name"): {"value": ma.get("value"), "rating": ma.get("rating")}
                                              for ma in d.get("movingAverages", []) if ma.get("name")}

                            # Get pivot points
                            pivot = d.get("pivot", {})

                            # Get all gauge summaries
                            gauge_summary = d.get("gaugeSummary", {})
                            gauge_ma = d.get("gaugeMovingAverage", {})
                            gauge_osc = d.get("gaugeOscillator", {})

                            stock_data["technical"] = {
                                # Key oscillators
                                "rsi": round(oscillators.get("rsi", {}).get("value", 0), 2) if oscillators.get("rsi", {}).get("value") else None,
                                "macd": round(oscillators.get("macd", {}).get("value", 0), 2) if oscillators.get("macd", {}).get("value") else None,
                                "stochastic": oscillators.get("stochastic", {}).get("value"),
                                "momentum": oscillators.get("momentum", {}).get("value"),
                                # Key moving averages
                                "sma20": moving_averages.get("sma20", {}).get("value"),
                                "sma50": moving_averages.get("sma50", {}).get("value"),
                                "ema20": moving_averages.get("ema20", {}).get("value"),
                                "ema50": moving_averages.get("ema50", {}).get("value"),
                                # Pivot points
                                "pivotPoint": pivot.get("pivotPoint"),
                                "support1": pivot.get("support1"),
                                "support2": pivot.get("support2"),
                                "support3": pivot.get("support3"),
                                "resistance1": pivot.get("resistance1"),
                                "resistance2": pivot.get("resistance2"),
                                "resistance3": pivot.get("resistance3"),
                                # Signals
                                "signalSummary": gauge_summary.get("rating"),
                                "signalMA": gauge_ma.get("rating"),
                                "signalOsc": gauge_osc.get("rating"),
                            }
                    except:
                        pass

                    # OHLCV - just get latest price info
                    try:
                        ohlcv = ohlcv_futures[ticker].result(timeout=10)
                        if ohlcv and isinstance(ohlcv, list) and len(ohlcv) > 0:
                            data = ohlcv[0]  # First item contains the stock data
                            # Data format: {symbol, o: [], h: [], l: [], c: [], v: [], t: []}
                            if data and data.get("c") and len(data.get("c", [])) > 0:
                                idx = -1  # Get last element
                                # Get timestamp and convert to readable format
                                timestamps = data.get("t", [])
                                timestamp = int(timestamps[idx]) if timestamps else None
                                time_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M") if timestamp else "N/A"
                                stock_data["price"] = {
                                    "open": data.get("o", [])[idx] if data.get("o") else None,
                                    "high": data.get("h", [])[idx] if data.get("h") else None,
                                    "low": data.get("l", [])[idx] if data.get("l") else None,
                                    "close": data.get("c", [])[idx] if data.get("c") else None,
                                    "volume": data.get("v", [])[idx] if data.get("v") else None,
                                    "timestamp": time_str
                                }
                    except:
                        pass

                    # Financial ratios (P/E, P/B) - filter last 10 actual days
                    try:
                        ratios = ratio_futures[ticker].result(timeout=10)
                        if ratios and "data" in ratios and len(ratios["data"]) > 0:
                            # Filter for entries within the last 10 days
                            ten_days_ago = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
                            filtered_data = [
                                r for r in ratios["data"]
                                if r.get("tradingDate") and r.get("tradingDate", "").split("T")[0] >= ten_days_ago
                            ]

                            stock_data["financials"] = [
                                {
                                    "date": r.get("tradingDate", "").split("T")[0],
                                    "pe": round(r.get("pe"), 2) if r.get("pe") is not None else None,
                                    "pb": round(r.get("pb"), 2) if r.get("pb") is not None else None,
                                }
                                for r in filtered_data[-10:]  # Still take max 10 entries from recent days
                            ]
                    except:
                        pass

                    # Annual return - 10 years
                    try:
                        returns = return_futures[ticker].result(timeout=10)
                        if returns and "data" in returns and len(returns["data"]) > 0:
                            stock_data["returns"] = [
                                {
                                    "year": r.get("year"),
                                    "stockReturn": round(r.get("stockReturn", 0) * 100, 2) if r.get("stockReturn") else None,
                                    "vnIndex": round(r.get("vnIndex", 0) * 100, 2) if r.get("vnIndex") else None,
                                    "outperformance": round(r.get("annualOutperformanceVNIndex", 0) * 100, 2) if r.get("annualOutperformanceVNIndex") else None,
                                }
                                for r in returns["data"]
                            ]
                    except:
                        pass

                    context["stocks_data"].append(stock_data)

        # 3. Get trending news
        news = get_trending_news(language=1)
        if news and "data" in news:
            def parse_date(iso_date):
                """Convert ISO date to full time format (GMT+7)"""
                try:
                    if iso_date:
                        dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
                        return dt.strftime("%d/%m/%Y %H:%M")
                except:
                    pass
                return iso_date or "N/A"

            context["trending_news"] = [
                {"title": n.get("name", ""), "date": parse_date(n.get("date", "")), "detail": n.get("detail", "")}
                for n in news["data"]
                if n.get("name")  # Filter out empty names
            ]
    except Exception as e:
        context["error"] = str(e)

    return context


def format_context_for_prompt(context: dict) -> str:
    """Format pre-fetched context into a readable string for the prompt."""
    lines = []

    # Stock data - show all information
    if context.get("stocks_data"):
        lines.append("\n### CHI TIẾT CÁC MÃ ĐÃ TỔNG HỢP SẴN")
        for s in context["stocks_data"]:
            company = s.get("company", {})
            tech = s.get("technical", {})
            price = s.get("price", {})

            lines.append(f"\n**{s['ticker']}** - {company.get('name', 'N/A')}")
            lines.append(f"- Ngành: {company.get('sector', 'N/A')}")
            current_price = price.get('close') or company.get('currentPrice', 'N/A')
            lines.append(f"- Giá hiện tại: {current_price} | High 1Y: {company.get('highestPrice1Year', 'N/A')} | Low 1Y: {company.get('lowestPrice1Year', 'N/A')}")
            lines.append(f"- Vốn hóa: {company.get('marketCap', 'N/A')} | KLGD TB: {company.get('averageMatchVolume1Month', 'N/A')}")
            lines.append(f"- Rating: {company.get('rating', 'N/A')} | Analyst: {company.get('analyst', 'N/A')}")
            lines.append(f"- RSI: {tech.get('rsi', 'N/A')} | MACD: {tech.get('macd', 'N/A')} | Stochastic: {tech.get('stochastic', 'N/A')} | Momentum: {tech.get('momentum', 'N/A')}")
            lines.append(f"- SMA20: {tech.get('sma20', 'N/A')} | SMA50: {tech.get('sma50', 'N/A')} | EMA20: {tech.get('ema20', 'N/A')} | EMA50: {tech.get('ema50', 'N/A')}")
            lines.append(f"- Pivot: {tech.get('pivotPoint', 'N/A')} | S1: {tech.get('support1', 'N/A')} | S2: {tech.get('support2', 'N/A')} | R1: {tech.get('resistance1', 'N/A')} | R2: {tech.get('resistance2', 'N/A')}")
            lines.append(f"- Signal: {tech.get('signalSummary', 'N/A')} (MA: {tech.get('signalMA', 'N/A')}, Osc: {tech.get('signalOsc', 'N/A')})")
            if price:
                lines.append(f"- OHLCV: O={price.get('open')} H={price.get('high')} L={price.get('low')} C={price.get('close')} V={price.get('volume')} @ {price.get('timestamp', 'N/A')}")
            financials = s.get("financials", [])
            if financials:
                pe_str = " | ".join([f"{f.get('date')}: {f.get('pe')}" for f in financials if f.get('pe') is not None])
                pb_str = " | ".join([f"{f.get('date')}: {f.get('pb')}" for f in financials if f.get('pb') is not None])
                if pe_str:
                    lines.append(f"- P/E: {pe_str}")
                if pb_str:
                    lines.append(f"- P/B: {pb_str}")
            returns = s.get("returns", [])
            if returns:
                returns_str = " | ".join([f"{r.get('year')}: {r.get('stockReturn')}%" for r in returns if r.get('stockReturn') is not None])
                if returns_str:
                    lines.append(f"- Annual Return: {returns_str}")

    # Trending news
    if context.get("trending_news"):
        lines.append("\n### TIN TỨC TRENDING")
        for i, n in enumerate(context["trending_news"], 1):
            lines.append(f"\n**{i}. {n['title']}** ({n['date']})")
            # Include article content, strip HTML tags
            detail = n.get('detail', '')
            if detail:
                # Remove HTML tags
                clean_detail = re.sub(r'<[^>]+>', '', detail)
                # Remove extra whitespace
                clean_detail = ' '.join(clean_detail.split())
                lines.append(f"   {clean_detail[:1000]}..." if len(clean_detail) > 1000 else f"   {clean_detail}")

    return "\n".join(lines)


class TradingAgent:
    def __init__(self, name: str, client: GeminiClient):
        self.name = name
        self.client = client

    async def run(self, task: str = None, date: str = None, stocks: list[str] = None, blacklist: list[str] = None, divident_rate: float = None):
        # Pre-fetch market context
        yield json.dumps({"type": "reasoning", "chunk": "🔄 Đang tải dữ liệu thị trường...\n\n"}) + "\n"

        market_context = fetch_market_context(portfolio_stocks=stocks)
        context_text = format_context_for_prompt(market_context)

        tickers_list = [s['ticker'] for s in market_context.get('stocks_data', [])]
        yield json.dumps({"type": "reasoning", "chunk": f"✅ Đã tải {len(tickers_list)} mã cổ phiếu: {', '.join(tickers_list)}\n\n📰 {len(market_context.get('trending_news', []))} tin tức trending\n\n"}) + "\n"

        # Build tool names for prompt
        tool_names = [tool.__name__ for tool in VIETCAP_TOOLS]

        # Instruction prompt for agent
        prompt = f"""
Bạn là một hệ thống hỗ trợ phân tích giao dịch chứng khoán chuyên nghiệp, hoạt động theo nguyên tắc:
DỮ LIỆU THỰC - THỜI GIAN THỰC - KIỂM CHỨNG ĐƯỢC - FAIL FAST.

────────────────────────────────
I. DỮ LIỆU ĐÃ ĐƯỢC CHUẨN BỊ SẴN
────────────────────────────────
Dữ liệu sau đã được truy xuất TỰ ĐỘNG tại thời điểm {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} GMT+7.
**HÃY SỬ DỤNG DỮ LIỆU NÀY TRƯỚC**, chỉ gọi công cụ khi cần thông tin CHI TIẾT HƠN hoặc về MÃ KHÁC.

{context_text}

────────────────────────────────
II. KHẢ NĂNG VÀ CÔNG CỤ
────────────────────────────────
Bạn có các khả năng sau:
- Suy nghĩ và suy luận logic dựa trên dữ liệu ĐƯỢC CUNG CẤP Ở TRÊN và dữ liệu thực tế đã được xác minh.
- Phân tích dữ liệu và trả lời đúng nhiệm vụ được giao
- Chỉ gọi công cụ khi THỰC SỰ CẦN THIẾT: {json.dumps(tool_names, ensure_ascii=False)}

**QUAN TRỌNG**:
- DỮ LIỆU Ở TRÊN ĐÃ ĐỦ để đưa ra phân tích tổng quan
- Chỉ gọi tool khi cần: thông tin mã KHÔNG có trong danh sách, dữ liệu OHLCV chi tiết, tin tức cụ thể
- TRÁNH gọi tool cho các mã đã có thông tin ở trên

**PHÂN TÍCH KỸ THUẬT**:
- Sử dụng RSI, Trend, Signal từ dữ liệu ở trên
- Nếu cần phân tích OHLCV chi tiết, gọi `get_ohlcv_data`
- Phân tích:
  - Nhận diện xu hướng giá (uptrend/downtrend/sideway)
  - Phân tích mô hình nến (engulfing, doji, hammer, etc.)
  - Đánh giá khối lượng giao dịch so với trung bình
  - Xác định vùng hỗ trợ/kháng cự từ dữ liệu giá
  - So sánh giá hiện tại với các mốc giá lịch sử

────────────────────────────────
III. NGUYÊN TẮC TUYỆT ĐỐI
────────────────────────────────
1. **MỌI GIÁ TRỊ GIÁ** phải là **mới nhất** và kèm timestamp

2. **TUYỆT ĐỐI KHÔNG** sử dụng kiến thức sẵn có của mô hình cho giá

3. Nếu **BẤT KỲ** điều kiện nào sau đây xảy ra:
  - Không xác định được timestamp.
  - Công cụ trả về lỗi.
  - Không thể xác minh dữ liệu mới nhất.
→ **DỪNG TOÀN BỘ PHÂN TÍCH NGAY LẬP TỨC**.
- Trả lời duy nhất:
  "Không đủ dữ liệu giá mới nhất và hợp lệ để đưa ra phân tích chính xác tại thời điểm này."

- **KHÔNG**:
  - Phân tích tiếp.
  - Suy đoán.
  - Đưa ra khuyến nghị thay thế.

4. Mọi dữ liệu **BẮT BUỘC** trích dẫn theo định dạng:

  <Nội dung>
  (Nguồn: Vietcap API - Thời gian cập nhật DD/MM/YYYY HH:mm GMT+7)

- Thiếu bất kỳ thành phần nào → dữ liệu không hợp lệ.

5. **TUYỆT ĐỐI KHÔNG**:
  - Làm tròn số.
  - Nội suy.
  - Giả lập.
  - Dự đoán cảm tính.

6. Nếu thời gian hệ thống:
  - Là ngày nghỉ, ngày lễ, hoặc ngoài giờ giao dịch:
    - Chỉ sử dụng dữ liệu của **phiên giao dịch gần nhất đã kết thúc**.
    - Phải nêu rõ điều này trong phần trả lời.

7. **LUÔN** trả lời bằng tiếng Việt

8. Đảm bảo đúng **01 khoảng trắng** sau mỗi dấu chấm (.), dấu phẩy (,), dấu hai chấm (:).

9. Trình bày bảng với đầy đủ thông tin kỹ thuật

────────────────────────────────
IV. THÔNG TIN NGỮ CẢNH CÁ NHÂN
────────────────────────────────
- Thời gian hệ thống: {datetime.strptime(date, "%Y-%m-%d %H:%M:%S") if date is not None else datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- Danh mục đang nắm giữ (Mã (Giá vốn)): {"Không có" if stocks is None else ', '.join(stocks)}
- Loại trừ lĩnh vực: {', '.join(blacklist) if blacklist is not None else "Không có"}
- Tỷ suất lợi nhuận tối thiểu: {divident_rate or 6}%

────────────────────────────────
V. NHIỆM VỤ
────────────────────────────────
- Nếu người dùng có yêu cầu cụ thể hợp lệ → trả lời **DUY NHẤT** yêu cầu đó và **DỪNG**.
- Nếu không có yêu cầu cụ thể hợp lệ, thực hiện lần lượt:

1. Phân tích tổng quan thị trường hiện tại.
2. Đưa ra khuyến nghị đầu tư dựa trên:
   - Dữ liệu thị trường.
   - Danh mục cá nhân.
3. Danh sách 05 mã cổ phiếu có xu hướng tăng ngắn hạn (< 1 tháng) theo phân tích kỹ thuật:
   - Phân loại: **NÊN MUA**, **THEO DÕI**, **THẬN TRỌNG**
   - Trình bày bảng gồm:
     Mã | Tên công ty | Phân loại | Giá hiện tại | Giá mua KN | Giá bán KN | RSI | MACD Signal | Xu hướng | Mô hình nến | Khối lượng vs TB | Hỗ trợ | Kháng cự | Phân tích
   - Trong đó:
     - RSI: Giá trị RSI 14 ngày (quá mua >70, quá bán <30)
     - MACD Signal: Bullish/Bearish/Neutral
     - Xu hướng: Uptrend/Downtrend/Sideway
     - Mô hình nến: Mô hình nến gần nhất (nếu có)
     - Khối lượng vs TB: So với trung bình 20 phiên (VD: +25%, -10%)
4. Danh sách 10 mã cổ phiếu ổn định, tỷ suất lợi nhuận cao, dài hạn (> 6 tháng):
   - Loại trừ cổ phiếu có tỷ suất lợi nhuận TB < {divident_rate or 6}%
   - Trình bày bảng gồm:
     Mã | Tên công ty | Giá hiện tại | Giá mua KN | Giá bán KN | TSLN TB (%) | RSI | Xu hướng | P/E | P/B | Phân tích
5. Danh sách các mã cổ phiếu nên tránh mua hiện tại:
   - Trình bày bảng gồm:
     Mã | Tên công ty | Giá hiện tại | RSI | MACD Signal | Xu hướng | Lý do tránh
6. Khuyến nghị bán từ danh mục đang nắm giữ:
   - Trình bày bảng gồm:
     Mã | Tên công ty | Giá vốn | Giá hiện tại | Lãi/Lỗ % | RSI | MACD Signal | Xu hướng | Hỗ trợ | Kháng cự | Khuyến nghị | Giá bán KN | Phân tích

────────────────────────────────
VI. QUY ƯỚC OUTPUT
────────────────────────────────
Output được chia thành 2 block:

{REASONING_DELIMITER}
Quá trình suy luận (không hiển thị cho người dùng)

{FINAL_DELIMITER}
Phân tích chính thức cho người dùng

────────────────────────────────
VII. YÊU CẦU NGƯỜI DÙNG
────────────────────────────────
{"Không có" if task is None else task}
"""

        # Collect tool calls for reasoning
        tool_call_log = []

        def on_tool_call(tool_name, args, result):
            tool_call_log.append({
                "tool": tool_name,
                "args": args,
            })

        try:
            # Generate with tools and stream results incrementally
            current_section = "reasoning" # Default section

            async for chunk in self.client.generate_with_tools(prompt, VIETCAP_TOOLS, on_tool_call):
                if not chunk:
                    continue

                # Check for section changes in the chunk
                if FINAL_DELIMITER in chunk:
                    parts = chunk.split(FINAL_DELIMITER, 1)

                    # Process part before delimiter
                    pre_chunk = parts[0].replace(REASONING_DELIMITER, "").strip()
                    if pre_chunk:
                        yield json.dumps({"type": current_section, "chunk": pre_chunk}) + "\n"

                    # Switch to final section
                    current_section = "final"

                    # Process part after delimiter
                    post_chunk = parts[1].strip()
                    if post_chunk:
                        yield json.dumps({"type": current_section, "chunk": post_chunk}) + "\n"
                else:
                    # Just a normal chunk, clean it up and yield
                    clean_chunk = chunk.replace(REASONING_DELIMITER, "").replace(FINAL_DELIMITER, "")
                    if clean_chunk:
                        yield json.dumps({"type": current_section, "chunk": clean_chunk}) + "\n"

            # If we had tool calls, report them as a final reasoning summary if not already yielded
            if tool_call_log:
                # We can yield this at the end or as they happen.
                # Since the current logic collects them in on_tool_call, let's yield at the end
                tool_summary = "\n\n📊 **Các công cụ đã sử dụng:**\n"
                for call in tool_call_log:
                    tool_summary += f"- `{call['tool']}`\n"
                yield json.dumps({"type": "reasoning", "chunk": tool_summary}) + "\n"

        except Exception as e:
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"
