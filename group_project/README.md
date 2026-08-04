# Bài Tập Nhóm — University Services RAG Chatbot

## Mục Tiêu

Sau khi hoàn thành bài cá nhân, nhóm ngồi lại để xây dựng **1 trong 2 sản phẩm**:

---

## Yêu cầu 1: Sản phẩm nhóm RAG Chatbot

Xây dựng chatbot trả lời câu hỏi về dịch vụ và chính sách đại học liên quan.

**Yêu cầu:**
- Giao diện chat (Streamlit / Gradio / Chainlit)
- Trả lời có citation (dựa trên Task 10)
- Hỗ trợ follow-up questions (conversation memory)
- Hiển thị source documents đã dùng

**Stack gợi ý:**
```
Chainlit/Streamlit → Retrieval (Task 9) → Generation (Task 10) → Display
```

---

## Yêu cầu 2: RAG Evaluation Pipeline

Sử dụng **1 trong 3 framework** sau để evaluate pipeline RAG của nhóm:

### Framework lựa chọn

| Framework | Cài đặt | Đặc điểm |
|-----------|---------|-----------|
| [DeepEval](https://github.com/confident-ai/deepeval) | `pip install deepeval` | Nhiều metric built-in, dễ integrate với pytest |
| [RAGAS](https://github.com/explodinggradients/ragas) | `pip install ragas` | Chuẩn industry cho RAG eval, 3 trục chính |
| [TruLens](https://github.com/truera/trulens) | `pip install trulens` | Dashboard UI, feedback functions mạnh |

### Yêu cầu Evaluation

1. **Tạo Golden Dataset** — tối thiểu 15 cặp Q&A (question, expected_answer, expected_context)
2. **Chạy evaluation** trên toàn bộ golden dataset với các metrics sau:
   - **Faithfulness** — câu trả lời có bám đúng context không?
   - **Answer Relevance** — câu trả lời có đúng câu hỏi không?
   - **Context Recall** — retriever có lấy đủ evidence không?
   - **Context Precision** — trong context lấy về, bao nhiêu % thực sự hữu ích?
3. **So sánh A/B** — chạy eval trên ít nhất 2 config khác nhau (ví dụ: có reranking vs không reranking, hoặc hybrid vs dense-only)
4. **Báo cáo** — bảng điểm + phân tích worst performers + đề xuất cải tiến

Xem code mẫu (DeepEval/RAGAS/TruLens) chi tiết trong `README.md` gốc mục "Yêu cầu 2".

### Deliverable Evaluation

- [x] File `group_project/evaluation/golden_dataset.json` — 15+ cặp Q&A
- [x] File `group_project/evaluation/eval_pipeline.py` — script chạy evaluation
- [x] File `group_project/evaluation/results.md` — bảng điểm + phân tích
- [x] So sánh A/B ít nhất 2 configs

---

## Yêu Cầu Chung

1. **Tích hợp pipeline** từ bài cá nhân của các thành viên
2. **Demo hoạt động được** trong buổi trình bày (chạy local hoặc deploy)
3. **Evaluation pipeline** chạy được và có báo cáo kết quả
4. **Code push lên repository** chung của nhóm
5. **README** mô tả kiến trúc và phân công (điền bên dưới)

---

## Kiến Trúc Hệ Thống

```
                     ┌──────────────────────────────────────────┐
                     │ 1. Data Collection & Processing          │
                     │  - Legal Docs (PDF/DOCX)                 │
                     │  - News Articles (JSON/Web Crawl)        │
                     └────────────────────┬─────────────────────┘
                                          │ MarkItDown Converter
                                          ▼
                     ┌──────────────────────────────────────────┐
                     │ 2. Standardized Markdown (.md)           │
                     └────────────────────┬─────────────────────┘
                                          │ Recursive Chunking (size=800)
                                          ▼
                     ┌──────────────────────────────────────────┐
                     │ 3. Indexing & Vector Database            │
                     │  - Dense: ChromaDB (BAAI/bge-m3)         │
                     │  - Sparse: BM25 Lexical Index            │
                     └────────────────────┬─────────────────────┘
                                          │
    ┌─────────────────────────────────────┴─────────────────────────────────────┐
    │ User Query (Chatbot UI / Streamlit)                                       │
    └─────────────────────────────────────┬─────────────────────────────────────┘
                                          │
                                          ▼
                     ┌──────────────────────────────────────────┐
                     │ 4. Hybrid Retrieval                      │
                     │  - Semantic Search (Cosine Similarity)   │
                     │  - Lexical Search (BM25 Keyword Match)   │
                     └────────────────────┬─────────────────────┘
                                          │
                                          ▼
                     ┌──────────────────────────────────────────┐
                     │ 5. RRF Reranking (Reciprocal Rank)      │
                     └────────────────────┬─────────────────────┘
                                          │
                 ┌────────────────────────┴────────────────────────┐
                 │ Top Cosine Score >= 0.48?                       │
                 ├────────────────────────┬────────────────────────┤
                 │ YES                    │ NO                     │
                 ▼                        ▼                        
┌─────────────────────────────────┐   ┌──────────────────────────┐
│ Hybrid Top Chunks               │   │ PageIndex Fallback       │
└────────────────┬────────────────┘   └────────────┬─────────────┘
                 │                                 │
                 └────────────────┬────────────────┘
                                  │
                                  ▼
                     ┌──────────────────────────────────────────┐
                     │ 6. Context Preparation & Reordering      │
                     │  - Pattern: front + back[::-1]           │
                     │  - Lost-in-the-middle Mitigation         │
                     └────────────────────┬─────────────────────┘
                                          │
                                          ▼
                     ┌──────────────────────────────────────────┐
                     │ 7. Generation & Evaluation               │
                     │  - OpenRouter / LLM Citation Prompt      │
                     │  - Streamlit Chatbot UI (app.py)         │
                     │  - RAGAS Evaluation (4 Metrics)          │
                     └──────────────────────────────────────────┘
```

---

## Phân Công Công Việc

| Thành viên | MHV / MSSV | Vai trò | Nhiệm vụ | Trạng thái |
|-----------|------------|---------|----------|------------|
| **Hoàng Mạnh Dũng** | `2A202601213` | Người A (Team Leader & Data/Dense Search Dev) | Phụ trách Task 1 (Thu thập PDF), Task 2 (Crawl News), Task 3 (Convert Markdown), Task 4 (Chunking & Indexing ChromaDB), Task 5 (Semantic Dense Search), Phát triển Giao diện Chatbot Streamlit (`app.py`) | ✅ Hoàn thành |
| **Trần Việt Trường** | `2A202601467` | Người B (Sparse Search, Pipeline & QA Engineer) | Phụ trách Task 6 (Lexical BM25), Task 7 (RRF Reranking), Task 8 (PageIndex Fallback), Task 9 (Retrieval Pipeline & Threshold 0.48), Task 10 (Citation Generation & Reordering), Soạn `golden_dataset.json` (15 Q&A) & RAGAS Eval `eval_pipeline.py` (`results.md`) | ✅ Hoàn thành |

---

## Hướng Dẫn Chạy

```bash
# Cài đặt dependencies
pip install -r requirements.txt

# Chạy app
streamlit run app.py
# hoặc
chainlit run app.py
```

---

## Lưu ý

Hãy giữ lại repo này nếu như bạn học track 3 giai đoạn 2, chúng ta sẽ phát triển tiếp dự án lên knowledge graph để khắc phục các câu hỏi hóc búa khi có các câu hỏi khó.
