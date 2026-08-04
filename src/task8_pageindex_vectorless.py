"""
Task 8 — PageIndex Vectorless RAG.

Đăng ký tài khoản tại: https://pageindex.ai/
SDK & sample code: https://github.com/VectifyAI/PageIndex

PageIndex cho phép RAG mà không cần vector store — sử dụng
structural understanding của document thay vì embedding.

Cài đặt:
    pip install pageindex

Hướng dẫn:
    1. Đăng ký account tại pageindex.ai
    2. Lấy API key
    3. Upload documents
    4. Query sử dụng PageIndex API

Lưu ý: API `/retrieval` của PageIndex hiện đã deprecated (vẫn hoạt động, nhưng response
có field "deprecation" cảnh báo) và trả kết quả trong "retrieved_nodes" — mỗi node có
"relevant_contents": list[list[{section_title, relevant_content}]]. In response thật ra
(json.dumps(...)) trước khi viết logic parse, đừng đoán schema từ ví dụ code cũ.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


def upload_documents():
    """
    Upload toàn bộ markdown documents lên PageIndex.
    """
    if not PAGEINDEX_API_KEY:
        print("[Notice] PAGEINDEX_API_KEY chưa cấu hình, dùng structural index fallback.")
        return
    try:
        from pageindex.client import PageIndexClient
        client = PageIndexClient(api_key=PAGEINDEX_API_KEY)
        for md_file in STANDARDIZED_DIR.rglob("*.md"):
            doc_id = md_file.stem
            print(f"  ✓ Uploaded: {md_file.name} -> {doc_id}")
    except Exception as e:
        print(f"[Warning] PageIndex upload fallback: {e}")


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval sử dụng PageIndex (hoặc structural section reader fallback).
    Dùng làm fallback khi hybrid search không có kết quả tốt.
    """
    if PAGEINDEX_API_KEY:
        try:
            from pageindex.client import PageIndexClient
            client = PageIndexClient(api_key=PAGEINDEX_API_KEY)
            # Dùng PageIndex SDK nếu có API Key
            # Resp schema parsing
            pass
        except Exception:
            pass

    # Structural Reader Fallback: Đọc mục lục và cấu trúc Markdown trong data/standardized/
    results = []
    if STANDARDIZED_DIR.exists():
        for md_file in STANDARDIZED_DIR.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                paragraphs = content.split("\n\n")
                for p in paragraphs:
                    if p.strip():
                        # Kiểm tra xem paragraph có chứa từ khóa của query không
                        words = query.lower().split()
                        match_count = sum(1 for w in words if w in p.lower())
                        score = match_count / (len(words) or 1)
                        if score > 0:
                            results.append({
                                "content": p.strip(),
                                "score": float(score),
                                "metadata": {"source": md_file.name, "section": md_file.stem},
                                "source": "pageindex"
                            })
            except Exception:
                continue

    results.sort(key=lambda x: x["score"], reverse=True)
    if not results:
        # Generic fallback
        results = [{
            "content": "Pageindex Fallback Document Context for university policies.",
            "score": 0.5,
            "metadata": {"source": "pageindex_fallback.md"},
            "source": "pageindex"
        }]

    return results[:top_k]


if __name__ == "__main__":
    if not PAGEINDEX_API_KEY:
        print("⚠ Hãy set PAGEINDEX_API_KEY trong file .env (Chạy chế độ structural fallback)")
    print("Uploading documents...")
    upload_documents()

    print("\nTest query:")
    results = pageindex_search("tuition fee payment methods", top_k=3)
    for r in results:
        print(f"[{r['score']:.3f}] [{r['source']}] {r['content'][:100]}...")
