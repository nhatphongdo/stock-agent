from datetime import datetime
from app.llm.gemini_client import GeminiClient
from app.tools.stock_tools import get_stock_news

# Constants for parsing delimiters
SENTIMENT_DELIMITER = "---SENTIMENT_LABEL---"
SOURCES_DELIMITER = "---SOURCES---"

class NewsAgent:
    def __init__(self, name: str, client: GeminiClient):
        self.name = name
        self.client = client

    async def run(self, symbol: str, company_name: str = ""):
        import json

        # 1. Fetch News Programmatically
        news_data = get_stock_news(symbol)
        tool_news_items = news_data.get("news", [])

        # 2. Immediately yield data chunk so UI updates with Tool News
        yield json.dumps({"type": "data", "news": tool_news_items}) + "\n"

        # 3. Prepare Context
        news_context = ""
        if tool_news_items:
            news_context = "Dưới đây là các tin tức mới nhất được thu thập từ nguồn dữ liệu thực tế:\n"
            for item in tool_news_items:
                title = item.get('title', 'N/A')
                date = item.get('date', 'N/A')
                source = item.get('source', 'N/A')
                link = item.get('link', 'N/A')
                news_context += f"- {title} (Ngày: {date}, Nguồn: {source}) ({link})\n"
        else:
            news_context = "Hiện tại chưa tìm thấy tin tức mới nhất từ hệ thống dữ liệu."

        # 4. Construct Prompt
        prompt = f"""
Bạn là một chuyên gia phân tích tin tức tài chính và chứng khoán.
Nhiệm vụ của bạn là phân tích tình hình hiện tại của mã cổ phiếu **{symbol}** ({company_name}).

**Nguồn dữ liệu:**
1. **Dữ liệu được cung cấp (Context)**: Xem danh sách bên dưới.
2. **Kiến thức/Tìm kiếm của bạn (Internet)**: Hãy tìm kiếm thêm thông tin mới nhất trên Internet (nếu có khả năng) hoặc sử dụng kiến thức của bạn để bổ sung các sự kiện quan trọng.

{news_context}

**Yêu cầu phân tích:**
1. **Kết hợp thông tin**: Tổng hợp tin tức từ cả dữ liệu cung cấp và kiến thức/tìm kiếm của bạn.
2. **Tổng hợp sự kiện**: Tóm tắt các sự kiện chính.
3. **Đánh giá Sentiment**: Đánh giá tâm lý thị trường.
4. **Nhận định**: Đưa ra nhận định ngắn gọn.

**Lưu ý quan trọng:**
- **KHÔNG** liệt kê lại danh sách nguồn tin trong phần nội dung chính.
- **BẮT BUỘC**: Ở cuối cùng của câu trả lời, hãy cung cấp 2 thông tin sau trong các block riêng biệt:
  1. `{SENTIMENT_DELIMITER}` [Nhãn ngắn gọn: Tích cực/Tiêu cực/Trung lập/Tiềm năng/Rủi ro/...]
  2. `{SOURCES_DELIMITER}` [JSON danh sách nguồn]

Cấu trúc trả về mong muốn:

[Nội dung phân tích Markdown bình thường...]

{SENTIMENT_DELIMITER}
Tiềm năng

{SOURCES_DELIMITER}
[
  {{ "title": "Tiêu đề bài báo", "link": "https://example.com/bai-viet", "date": "YYYY-MM-DD", "source": "TenNguon" }},
  ...
]
"""

        is_parsing_sources = False
        collected_sources_text = ""

        is_parsing_sentiment = False
        collected_sentiment_text = ""

        try:
            # 5. Stream Analysis Content
            async for chunk in self.client.generate_content(prompt):
                 # Detect Start of Sentiment Block
                 if SENTIMENT_DELIMITER in chunk:
                     parts = chunk.split(SENTIMENT_DELIMITER)
                     if parts[0].strip():
                        yield json.dumps({"type": "content", "chunk": parts[0]}) + "\n"

                     is_parsing_sentiment = True
                     is_parsing_sources = False

                     if len(parts) > 1:
                         remaining = parts[1]
                         if SOURCES_DELIMITER in remaining:
                             label_part, source_part = remaining.split(SOURCES_DELIMITER, 1)
                             collected_sentiment_text += label_part
                             is_parsing_sentiment = False
                             is_parsing_sources = True
                             collected_sources_text += source_part
                         else:
                             collected_sentiment_text += remaining
                     continue

                 # Detect Start of Sources Block
                 if SOURCES_DELIMITER in chunk:
                     parts = chunk.split(SOURCES_DELIMITER)

                     if is_parsing_sentiment:
                         collected_sentiment_text += parts[0]
                         is_parsing_sentiment = False
                     elif parts[0].strip():
                         yield json.dumps({"type": "content", "chunk": parts[0]}) + "\n"

                     is_parsing_sources = True
                     if len(parts) > 1:
                         collected_sources_text += parts[1]
                     continue

                 if is_parsing_sentiment:
                     collected_sentiment_text += chunk
                     # Watch for sources start if chunked awkwardly
                     if SOURCES_DELIMITER in collected_sentiment_text:
                         label_part, source_part = collected_sentiment_text.split(SOURCES_DELIMITER, 1)
                         collected_sentiment_text = label_part
                         is_parsing_sentiment = False
                         is_parsing_sources = True
                         collected_sources_text += source_part

                 elif is_parsing_sources:
                     collected_sources_text += chunk
                 else:
                     # Normal content stream
                     yield json.dumps({"type": "content", "chunk": chunk}) + "\n"

            # --- PROCESS SENTIMENT ---
            if collected_sentiment_text.strip():
                label = collected_sentiment_text.strip()
                # Clean up if AI added extra formatting
                label = label.replace("`", "").replace("*", "").strip()

                # Determine color
                color = "gray"
                l_lower = label.lower()

                pos_keywords = ["tích cực", "tiềm năng", "tăng trưởng", "mua", "khả quan", "đáng đầu tư", "cơ hội"]
                neg_keywords = ["tiêu cực", "rủi ro", "giảm", "bán", "thận trọng", "cảnh báo", "khó khăn", "thách thức"]

                has_pos = any(k in l_lower for k in pos_keywords)
                has_neg = any(k in l_lower for k in neg_keywords)

                # Priority Check: Mixed Sentiment -> Orange
                if has_pos and has_neg:
                     color = "orange"
                elif has_pos:
                    color = "green"
                elif has_neg:
                    color = "red"
                elif any(x in l_lower for x in ["trung lập", "đi ngang", "theo dõi", "chờ đợi", "quan sát"]):
                    color = "yellow"
                elif any(x in l_lower for x in ["nắm giữ", "hold"]):
                    color = "blue"

                yield json.dumps({"type": "sentiment", "label": label, "color": color}) + "\n"

            # --- PROCESS SOURCES ---
            final_news_list = list(tool_news_items) # Start with tool items

            if collected_sources_text.strip():
                try:
                    json_text = collected_sources_text.strip()
                    if "```" in json_text:
                        parts = json_text.split("```")
                        if len(parts) >= 3:
                            json_text = parts[1]
                            if json_text.startswith("json"):
                                json_text = json_text[4:]

                    ai_sources = json.loads(json_text.strip())

                    # Merge Logic
                    existing_links = {item.get('link') for item in final_news_list if item.get('link')}

                    for src in ai_sources:
                        link = src.get('link', '')
                        if (link and link in existing_links):
                            continue
                        final_news_list.append(src)

                except Exception as parse_err:
                    print(f"Error parsing AI sources: {parse_err}")
                    pass

            # 7. Send Updated List
            yield json.dumps({"type": "data", "news": final_news_list}) + "\n"

        except Exception as e:
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"
