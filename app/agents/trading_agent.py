from datetime import datetime, timedelta
from app.llm.gemini_client import GeminiClient
from app.tools.vietcap_tools import (
    VIETCAP_TOOLS,
    get_top_tickers,
    get_company_info,
    get_latest_ohlcv,
    get_technical_indicators,
    get_trending_news,
    get_coverage_universe,
    get_financial_ratios,
    get_annual_return,
    get_stock_news,
    get_stock_events,
    get_short_financial,
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
        "trending_news": [],
    }

    try:
        # 1. Get trending news FIRST to extract related tickers
        news = get_trending_news(language=1)
        if isinstance(news, list):
            context["trending_news"] = news

        # 2. Get top tickers (9 positive, 9 negative from All)
        top_result = get_top_tickers(top_pos=9, top_neg=9, group="all")
        tickers = set()

        # get_top_tickers returns a flat list with sentiment info
        if isinstance(top_result, list):
            tickers.update([t["ticker"] for t in top_result if t.get("ticker")])

        # 3. Get coverage universe and filter BUY-rated stocks
        coverage = get_coverage_universe()
        if coverage and isinstance(coverage, list):
            buy_stocks = [s for s in coverage if s.get("rating") == "BUY"][:10]
            tickers.update([s.get("ticker") for s in buy_stocks if s.get("ticker")])

        # 4. Add tickers from trending news
        if isinstance(news, list):
            tickers.update([n.get("ticker") for n in news if n.get("ticker")])

        # 5. Add portfolio stocks if provided
        if portfolio_stocks:
            # Extract ticker symbols from portfolio format "TICKER(cost)" or just "TICKER"
            for stock in portfolio_stocks:
                ticker = stock.split('(')[0].strip().upper()
                if ticker:
                    tickers.add(ticker)

        # Convert to list for processing
        tickers = list(tickers)

        # 6. Fetch details for each ticker (parallel execution)
        if tickers:
            with ThreadPoolExecutor(max_workers=5) as executor:
                # Fetch company info
                company_futures = {ticker: executor.submit(get_company_info, ticker) for ticker in tickers}
                # Fetch technical indicators
                tech_futures = {ticker: executor.submit(get_technical_indicators, ticker, "ONE_DAY") for ticker in tickers}
                # Fetch OHLCV (latest price)
                ohlcv_futures = {ticker: executor.submit(get_latest_ohlcv, ticker) for ticker in tickers}
                # Fetch financial ratios
                ratio_futures = {ticker: executor.submit(get_financial_ratios, ticker) for ticker in tickers}
                # Fetch annual return
                return_futures = {ticker: executor.submit(get_annual_return, ticker, 10) for ticker in tickers}
                # Fetch stock news (last 7 days)
                seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
                today = datetime.now().strftime("%Y%m%d")
                news_futures = {ticker: executor.submit(get_stock_news, ticker, seven_days_ago, today) for ticker in tickers}
                # Fetch stock events (last 7 days)
                events_futures = {ticker: executor.submit(get_stock_events, ticker, seven_days_ago, today) for ticker in tickers}
                # Fetch short financial
                short_fin_futures = {ticker: executor.submit(get_short_financial, ticker) for ticker in tickers}

                for ticker in tickers:
                    stock_data = {"ticker": ticker}

                    # Company info
                    try:
                        company = company_futures[ticker].result(timeout=10)
                        if company and "error" not in company:
                            stock_data["company"] = company
                    except:
                        pass

                    # Technical indicators
                    try:
                        tech = tech_futures[ticker].result(timeout=10)
                        if tech and "error" not in tech:
                            stock_data["technical"] = tech
                    except:
                        pass

                    # Latest OHLCV price
                    try:
                        ohlcv = ohlcv_futures[ticker].result(timeout=10)
                        if ohlcv and "error" not in ohlcv:
                            stock_data["price"] = ohlcv
                    except:
                        pass

                    # Financial ratios (P/E, P/B)
                    try:
                        ratios_resp = ratio_futures[ticker].result(timeout=10)
                        if ratios_resp and "ratios" in ratios_resp:
                            stock_data["financials"] = ratios_resp["ratios"]
                    except:
                        pass

                    # Annual return - Last 10 years
                    try:
                        returns_resp = return_futures[ticker].result(timeout=10)
                        if returns_resp and "returns" in returns_resp:
                            current_year = datetime.now().year
                            stock_data["returns"] = [
                                r for r in returns_resp["returns"]
                                if r.get("year") and r.get("year") >= current_year - 9
                            ]
                    except:
                        pass

                    # Stock news - Last 7 days
                    try:
                        news_resp = news_futures[ticker].result(timeout=10)
                        if news_resp and "news" in news_resp and news_resp["news"]:
                            stock_data["news"] = news_resp["news"]
                    except:
                        pass

                    # Stock events - Last 7 days
                    try:
                        events_resp = events_futures[ticker].result(timeout=10)
                        if events_resp and "events" in events_resp and events_resp["events"]:
                            stock_data["events"] = events_resp["events"]
                    except:
                        pass

                    # Short financial
                    try:
                        short_fin_resp = short_fin_futures[ticker].result(timeout=10)
                        if short_fin_resp and "financials" in short_fin_resp and short_fin_resp["financials"]:
                            stock_data["quarterlyFinancials"] = short_fin_resp["financials"]
                    except:
                        pass

                    context["stocks_data"].append(stock_data)
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
            lines.append(f"- Rating: {company.get('rating', 'N/A')}")

            indicators = tech.get('indicators', {})
            gauges = tech.get('gauges', {})
            pivot = tech.get('pivot', {})
            fib = tech.get('fibonacci', {})
            lines.append(f"- RSI: {indicators.get('rsi', 'N/A')} | MACD: {indicators.get('macd', 'N/A')} | Stochastic: {indicators.get('stochastic', 'N/A')} | Momentum: {indicators.get('momentum', 'N/A')}")
            lines.append(f"- SMA20: {indicators.get('sma20', 'N/A')} | SMA50: {indicators.get('sma50', 'N/A')} | EMA20: {indicators.get('ema20', 'N/A')} | EMA50: {indicators.get('ema50', 'N/A')}")
            lines.append(f"- Pivot: {pivot.get('pivotPoint', 'N/A')} | S1: {pivot.get('support1', 'N/A')} | S2: {pivot.get('support2', 'N/A')} | R1: {pivot.get('resistance1', 'N/A')} | R2: {pivot.get('resistance2', 'N/A')}")
            lines.append(f"- Fib S1: {fib.get('support1', 'N/A')} | Fib S2: {fib.get('support2', 'N/A')} | Fib R1: {fib.get('resistance1', 'N/A')} | Fib R2: {fib.get('resistance2', 'N/A')}")
            lines.append(f"- Signal: {gauges.get('summary', {}).get('rating', 'N/A')} (MA: {gauges.get('movingAverage', {}).get('rating', 'N/A')}, Osc: {gauges.get('oscillator', {}).get('rating', 'N/A')})")
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

            # Stock-specific news (last 7 days, max 5)
            stock_news = s.get("news", [])
            if stock_news:
                news_titles = " | ".join([n.get("title", "") for n in stock_news[:5] if n.get("title")])
                if news_titles:
                    lines.append(f"- Tin tức 7 ngày: {news_titles}")

            # Stock-specific events (last 7 days, max 5)
            stock_events = s.get("events", [])
            if stock_events:
                event_titles = " | ".join([f"{e.get('event', '')}: {e.get('title', '')}" for e in stock_events[:5] if e.get("title")])
                if event_titles:
                    lines.append(f"- Sự kiện 7 ngày: {event_titles}")

            # Quarterly financials (last 8 quarters)
            quarterly = s.get("quarterlyFinancials", [])
            if quarterly:
                # API returns ascending order, reverse to get latest first
                latest_quarters = list(reversed(quarterly))[:8]
                lines.append("- Báo cáo quý gần nhất:")
                for q in latest_quarters:
                    if q.get('period'):
                        lines.append(
                            f"  {q.get('period')}: Rev={q.get('revenue')}, RevGr={q.get('revenueGrowth')}%, "
                            f"NP={q.get('netProfit')}, NPGr={q.get('netProfitGrowth')}%, "
                            f"GM={q.get('grossMargin')}%, NM={q.get('netMargin')}%, "
                            f"ROE={q.get('roe')}%, ROA={q.get('roa')}%, "
                            f"CR={q.get('currentRatio')}, QR={q.get('quickRatio')}, D/E={q.get('debtEquity')}"
                        )

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
        news_count = len(market_context.get('trending_news') or [])
        yield json.dumps({"type": "reasoning", "chunk": f"✅ Đã tải {len(tickers_list)} mã cổ phiếu: {', '.join(tickers_list)}\n\n📰 {news_count} tin tức trending\n\n"}) + "\n"

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

**QUAN TRỌNG - KHI NÀO GỌI TOOL**:
- ✅ GỌI TOOL nếu: mã CỔ PHIẾU KHÔNG CÓ trong danh sách trên
- ✅ GỌI TOOL nếu: cần giá real-time (get_latest_ohlcv) hoặc phân tích đa ngày (get_ohlcv_by_day)
- ✅ GỌI TOOL nếu: cần tin tức/sự kiện MỚI HƠN trong 24h (get_stock_news, get_stock_events)
- ✅ GỌI TOOL nếu: dữ liệu ở trên KHÔNG ĐỦ để trả lời câu hỏi
- ✅ GỌI TOOL nếu: cần so sánh với ngành (get_sector_comparison)
- ❌ KHÔNG GỌI nếu: mã đã có đầy đủ thông tin phù hợp ở trên

**PHÂN TÍCH KỸ THUẬT**:
- Sử dụng RSI, Trend, Signal từ dữ liệu ở trên
- Nếu cần giá MỚI NHẤT (real-time theo phút), gọi `get_latest_ohlcv`
- Nếu cần phân tích ĐA NGÀY (xu hướng, mô hình nến, hỗ trợ/kháng cự), gọi `get_ohlcv_by_day`
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
- Thời gian hệ thống: {date + " 00:00:00" if (date and len(date) == 10) else (date if date else datetime.now().strftime("%Y-%m-%d %H:%M:%S"))}
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
VI. QUY ƯỚC OUTPUT (BẮT BUỘC)
────────────────────────────────
**CRITICAL: Output PHẢI tuân theo format sau CHÍNH XÁC, không được thiếu bất kỳ delimiter nào:**

{REASONING_DELIMITER}
[Quá trình suy luận - không hiển thị cho người dùng]

{FINAL_DELIMITER}
[Phân tích chính thức cho người dùng - NỘI DUNG PHẢI CÓ SAU DELIMITER NÀY]

**LƯU Ý QUAN TRỌNG:**
- Delimiter "{REASONING_DELIMITER}" phải xuất hiện TRƯỚC phần suy luận
- Delimiter "{FINAL_DELIMITER}" phải xuất hiện TRƯỚC phần phân tích cuối cùng
- NẾU THIẾU BẤT KỲ DELIMITER NÀO → RESPONSE KHÔNG HỢP LỆ
- KHÔNG được kết thúc ở giữa, PHẢI hoàn thành cả 2 phần

────────────────────────────────
VII. YÊU CẦU NGƯỜI DÙNG
────────────────────────────────
{"Không có" if task is None else task}
"""

        # Collect tool calls for reasoning
        tool_call_log = []
        pending_tool_reasoning = []

        def on_tool_call(name, args, result=None):
            # Log for internal tracking
            tool_call_log.append({
                "tool": name,
                "args": args,
            })
            # Add to pending reasoning queue for UI visibility
            pending_tool_reasoning.append(f"🔍 Đang truy xuất thông tin từ: `{name}`...")

        try:
            # Generate with tools and stream results incrementally
            current_section = "reasoning" # Default section

            async for chunk in self.client.generate_with_tools(prompt, VIETCAP_TOOLS, on_tool_call):
                if not chunk:
                    continue

                # Yield any pending tool call reasoning first
                while pending_tool_reasoning:
                    msg = pending_tool_reasoning.pop(0)
                    yield json.dumps({"type": "reasoning", "chunk": f"\n\n{msg}\n\n"}) + "\n"

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

        except Exception as e:
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"
