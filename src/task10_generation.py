"""
Task 10 — Generation Có Citation.

Hướng dẫn:
    1. Chọn top_k, top_p phù hợp (giải thích lý do)
    2. Sắp xếp lại chunks sau reranking để tránh "lost in the middle"
    3. Inject context vào prompt
    4. Yêu cầu LLM trả lời có citation
    5. Nếu không đủ evidence → "I cannot verify this information"

Gợi ý LLM: OpenRouter có nhiều model gắn hậu tố ":free" không tính phí — xem
https://openrouter.ai/models?max_price=0 — phù hợp nếu chưa có credit trả phí.
Base URL: "https://openrouter.ai/api/v1", dùng chung interface với OpenAI SDK.
"""

import os
from dotenv import load_dotenv

load_dotenv()

from .task9_retrieval_pipeline import retrieve


# =============================================================================
# CONFIGURATION — Giải thích lựa chọn
# =============================================================================

# top_k: Số chunks đưa vào context
# Chọn 5 vì: đủ evidence mà không quá dài gây lost in the middle
TOP_K = 5

# top_p (nucleus sampling): Xác suất tích luỹ cho token generation
# Chọn 0.9 vì: đủ diverse nhưng không quá random
TOP_P = 0.9

# temperature: Độ ngẫu nhiên của output
# Chọn 0.3 vì: RAG cần factual, ít sáng tạo
TEMPERATURE = 0.3

# TODO: Chọn LLM model (OpenRouter model ID)
LLM_MODEL = "openai/gpt-4o-mini"  # hoặc model ":free" nếu chưa có credit


# =============================================================================
# SYSTEM PROMPT
# =============================================================================

SYSTEM_PROMPT = """Bạn là trợ lý trả lời câu hỏi về dịch vụ và chính sách đại học
(học phí, học bổng, ký túc xá, thư viện, đăng ký học phần).

Quy tắc bắt buộc:
1. Chỉ sử dụng thông tin từ context được cung cấp — KHÔNG bịa đặt
2. Mỗi khẳng định phải có trích dẫn ngay sau, ví dụ: [Tuition Fees, 2026]
3. Nếu context không đủ thông tin → trả lời: "Tôi không thể xác minh thông tin này từ nguồn hiện có"
4. Trả lời bằng tiếng Việt, có cấu trúc rõ ràng theo đoạn văn
5. Không suy luận hay mở rộng ngoài những gì được nêu trong context"""


# =============================================================================
# DOCUMENT REORDERING (tránh lost in the middle)
# =============================================================================

def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """
    Sắp xếp chunks để tránh "lost in the middle" effect.
    Input order (by score):  [1, 2, 3, 4, 5]
    Output order:            [1, 3, 5, 4, 2]
    """
    if not chunks or len(chunks) <= 2:
        return chunks

    front = chunks[::2]
    back = chunks[1::2]
    return front + back[::-1]


def format_context(chunks: list[dict]) -> str:
    """
    Format chunks thành context string cho prompt.
    Mỗi chunk có label source để LLM có thể cite.
    """
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get("metadata", {}).get("source", f"Source {i}")
        doc_type = chunk.get("metadata", {}).get("type", "unknown")
        context_parts.append(
            f"[Document {i} | Source: {source} | Type: {doc_type}]\n"
            f"{chunk['content']}\n"
        )
    return "\n---\n".join(context_parts)


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """
    End-to-end RAG generation có citation.
    """
    import re
    clean_q = query.strip().lower()

    # 0. Xử lý biểu thức toán học đơn giản (ví dụ: 1+1, 5 * 10 bằng bao nhiêu...)
    math_match = re.search(r'^\s*(\d+\s*[\+\-\*/]\s*\d+)', clean_q)
    if math_match:
        try:
            expr = math_match.group(1)
            result = eval(expr, {"__builtins__": None}, {})
            return {
                "answer": f"**Kết quả tính toán:** `{expr}` = **{result}**\n\n*(Lưu ý: Đây là câu hỏi tính toán cá nhân, không nằm trong bộ tài liệu tư vấn RMIT).*",
                "sources": [],
                "retrieval_source": "direct_calculation"
            }
        except Exception:
            pass

    # 0.1 Xử lý câu hỏi về nguồn gốc thông tin của Chatbot
    if any(phrase in clean_q for phrase in ["lay thong tin", "lấy thông tin", "nguon o dau", "nguồn ở đâu", "lay tu dau", "lấy từ đâu", "lay o dau", "lấy ở đâu"]):
        return {
            "answer": "Thông tin được trích xuất trực tiếp từ các văn bản chính thức của RMIT Việt Nam (gồm **Quy định học phí**, **Quy chế học bổng**, **Quy định dịch vụ lưu trú KTX**, và **Tin tức thư viện/tuyển sinh**) được lưu trữ trong cơ sở dữ liệu của hệ thống.",
            "sources": [],
            "retrieval_source": "meta_info"
        }

    # Step 1: Retrieve
    chunks = retrieve(query, top_k=top_k)

    # Kiểm tra mức độ liên quan của kết quả tìm kiếm với câu hỏi
    rmit_keywords = [
        "hoc phi", "học phí", "hoc bong", "học bổng", "ky tuc xa", "ký túc xá", "ktx",
        "thu vien", "thư viện", "rmit", "phong", "phòng", "dang ky", "đăng ký", 
        "mon hoc", "môn học", "chinh sach", "chính sách", "tin tuc", "tin tức",
        "luu tru", "lưu trú", "cho o", "chỗ ở", "gia", "giá", "chi phi", "chi phí",
        "o dau", "ở đâu", "the nao", "thế nào", "nhu nao", "như thế nào", "han", "hạn"
    ]
    has_rmit_kw = any(kw in clean_q for kw in rmit_keywords)
    best_score = chunks[0].get("score", 0.0) if chunks else 0.0

    if not chunks or (best_score < 0.05 and not has_rmit_kw):
        return {
            "answer": "Tôi không thể xác minh thông tin này từ nguồn tài liệu RMIT hiện có.\n\nHệ thống hỗ trợ trả lời các câu hỏi về: Học phí, Học bổng, Dịch vụ lưu trú (KTX), Thư viện và Tin tức tuyển sinh tại RMIT.",
            "sources": [],
            "retrieval_source": "none"
        }

    # Step 2: Reorder
    reordered = reorder_for_llm(chunks)

    # Step 3: Format context
    context = format_context(reordered)

    # Step 4: Build prompt & call LLM if API Key available
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")

    answer = ""

    if openrouter_key or openai_key or gemini_key:
        try:
            from openai import OpenAI
            if gemini_key and not (openrouter_key or openai_key):
                client = OpenAI(
                    api_key=gemini_key,
                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
                )
                model_name = "gemini-2.0-flash"
            elif openrouter_key:
                client = OpenAI(api_key=openrouter_key, base_url="https://openrouter.ai/api/v1")
                model_name = LLM_MODEL
            else:
                client = OpenAI(api_key=openai_key)
                model_name = LLM_MODEL

            user_message = f"Context:\n{context}\n\n---\n\nQuestion: {query}"

            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                temperature=TEMPERATURE,
                top_p=TOP_P,
            )
            answer = response.choices[0].message.content
        except Exception as e:
            print(f"[Warning] LLM Call Fallback: {e}")
            answer = ""

    # Synthesized Answer Fallback (Nếu thiếu API Key hoặc gọi API lỗi)
    if not answer:
        top_src = chunks[0].get("metadata", {}).get("source", "Tài liệu RMIT")
        main_content = chunks[0].get("content", "").strip()
        answer = f"**[Trả lời trích dẫn từ nguồn chuẩn]**\n\nDựa trên tài liệu [{top_src}]:\n\n{main_content}"

    retrieval_source = chunks[0].get("source", "hybrid") if chunks else "hybrid"
    return {
        "answer": answer,
        "sources": chunks,
        "retrieval_source": retrieval_source
    }


if __name__ == "__main__":
    test_queries = [
        "Học phí tại RMIT Vietnam là bao nhiêu?",
        "Làm sao để đặt phòng học nhóm ở thư viện?",
        "Sinh viên quốc tế có những học bổng nào?",
    ]

    for q in test_queries:
        print(f"\n{'='*70}")
        print(f"Q: {q}")
        print("=" * 70)
        result = generate_with_citation(q)
        print(f"\nA: {result['answer']}")
        print(f"\n[Sources: {len(result['sources'])} chunks | via {result['retrieval_source']}]")
