"""
RAG Chatbot — University Services (Starter Template)
Streamlit app kết nối RAG Retrieval (Task 9) và Generation (Task 10).

Chạy:
    streamlit run app.py
"""

import os
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Thêm project root vào sys.path để import các task từ src/
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="University Services RAG Chatbot",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# SIDEBAR — INFO & SETTINGS
# =============================================================================

with st.sidebar:
    st.title("🎓 University Services RAG")
    st.caption("Trợ lý hỏi đáp về dịch vụ và chính sách đại học (học phí, học bổng, ký túc xá, thư viện)")

    st.divider()

    st.subheader("💡 Câu hỏi gợi ý")
    suggestions = [
        "Học phí tại RMIT Vietnam là bao nhiêu?",
        "Làm sao để đặt phòng học nhóm ở thư viện?",
        "Điều kiện xin học bổng Academic Achievement?",
        "Dịch vụ hỗ trợ chỗ ở cho sinh viên như thế nào?",
        "Cách đăng ký học phần qua myRMIT?",
    ]
    for s in suggestions:
        if st.button(s, use_container_width=True, key=f"sug_{s[:20]}"):
            st.session_state["pending_query"] = s

    st.divider()
    st.subheader("⚙️ Thiết lập")
    top_k = st.slider("Số chunks retrieval (top_k)", 3, 10, 5)

    st.divider()
    st.caption("**Kiến trúc hệ thống:**")
    st.caption("Hybrid Retrieval (Semantic + BM25) → RRF Rerank → PageIndex Fallback → LLM Generation có Citation")

# =============================================================================
# SESSION STATE
# =============================================================================

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

# =============================================================================
# MAIN CHAT AREA
# =============================================================================

st.title("🎓 University Services RAG Chatbot")
st.caption("Hệ thống hỏi đáp thông tin dịch vụ đại học (Học phí, Học bổng, Ký túc xá, Thư viện)")

# Hiển thị lịch sử chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and "sources" in msg and msg["sources"]:
            with st.expander(f"📚 Nguồn tham khảo ({len(msg['sources'])} chunks)"):
                for i, src in enumerate(msg["sources"], 1):
                    meta = src.get("metadata", {})
                    ret_method = src.get("source", "RRF Rerank")
                    st.markdown(f"**[{i}] {source_name}** `{doc_type}` | **Alg:** `{ret_method}` | score: `{score:.4f}`")
                    st.text(src.get("content", "")[:300] + "...")
                    st.divider()

# =============================================================================
# QUERY HANDLING
# =============================================================================

# Xử lý khi bấm nút gợi ý hoặc nhập câu hỏi mới
user_input = st.chat_input("Nhập câu hỏi của bạn về chính sách/dịch vụ đại học...")
query = user_input or st.session_state.pending_query

if query:
    st.session_state.pending_query = None

    # Hiển thị câu hỏi của user
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # Sinh câu trả lời từ RAG Pipeline
    with st.chat_message("assistant"):
        with st.spinner("Đang tìm kiếm tài liệu và tổng hợp câu trả lời..."):
            try:
                from src.task10_generation import generate_with_citation
                res = generate_with_citation(query, top_k=top_k)
                answer = res.get("answer", "Chưa thể trả lời.")
                sources = res.get("sources", [])
            except Exception as ex:
                try:
                    from src.task5_semantic_search import semantic_search
                    sources = semantic_search(query, top_k=top_k)
                    if sources:
                        best_chunk = sources[0]["content"]
                        answer = f"**[Kết quả tra cứu từ Semantic Search]**\n\n{best_chunk}"
                    else:
                        answer = "Không tìm thấy thông tin phù hợp trong cơ sở dữ liệu."
                except Exception as inner_ex:
                    # Emergency Fallback: Đọc trực tiếp từ kho dữ liệu Markdown chuẩn
                    from pathlib import Path
                    std_dir = Path("data/standardized")
                    matched_content = ""
                    sources = []
                    if std_dir.exists():
                        for md_file in std_dir.rglob("*.md"):
                            txt = md_file.read_text(encoding="utf-8")
                            if any(w in txt.lower() for w in query.lower().split() if len(w) > 2):
                                matched_content = txt[:600]
                                sources.append({
                                    "content": txt[:600],
                                    "score": 0.5,
                                    "metadata": {"source": md_file.name, "type": md_file.parent.name}
                                })
                                break
                    if matched_content:
                        answer = f"**[Kết quả trích xuất trực tiếp từ tài liệu]**\n\n{matched_content}"
                    else:
                        answer = "Chưa tìm thấy tài liệu phù hợp cho câu hỏi này."

            st.markdown(answer)

            if sources:
                with st.expander(f"📚 Nguồn tham khảo ({len(sources)} chunks)"):
                    for i, src in enumerate(sources, 1):
                        meta = src.get("metadata", {})
                        source_name = meta.get("source", "Unknown")
                        doc_type = meta.get("type", "unknown")
                        score = src.get("score", 0)
                        ret_method = src.get("source", "RRF Rerank")
                        st.markdown(f"**[{i}] {source_name}** `{doc_type}` | **Alg:** `{ret_method}` | score: `{score:.4f}`")
                        st.text(src.get("content", "")[:300] + "...")
                        st.divider()

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
    })
