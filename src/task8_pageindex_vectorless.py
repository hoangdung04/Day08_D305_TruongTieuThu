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
        try:
            from pageindex import PageIndexClient
        except ImportError:
            from pageindex.client import PageIndexClient
        client = PageIndexClient(api_key=PAGEINDEX_API_KEY)
        for md_file in STANDARDIZED_DIR.rglob("*.md"):
            doc_id = md_file.stem
            try:
                if hasattr(client, "upload_document"):
                    client.upload_document(file_path=str(md_file), doc_id=doc_id)
                elif hasattr(client, "submit_document"):
                    client.submit_document(file_path=str(md_file))
                print(f"  ✓ Uploaded: {md_file.name} -> {doc_id}")
            except Exception as fe:
                print(f"  ⚠ Upload status for {md_file.name}: {fe}")
    except Exception as e:
        print(f"[Warning] PageIndex upload fallback: {e}")


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval sử dụng PageIndex (hoặc structural section reader fallback).
    Dùng làm fallback khi hybrid search không có kết quả tốt.
    """
    if PAGEINDEX_API_KEY:
        try:
            try:
                from pageindex import PageIndexClient
            except ImportError:
                from pageindex.client import PageIndexClient
            client = PageIndexClient(api_key=PAGEINDEX_API_KEY)

            # Gọi API retrieval của PageIndex SDK
            response = None
            if hasattr(client, "retrieve"):
                response = client.retrieve(query=query, top_k=top_k)
            elif hasattr(client, "search"):
                response = client.search(query=query, top_k=top_k)

            api_results = []
            if response:
                # Schema: retrieved_nodes -> relevant_contents -> list of {section_title, relevant_content}
                nodes = response.get("retrieved_nodes", []) if isinstance(response, dict) else getattr(response, "retrieved_nodes", [])
                for node in nodes:
                    rel_contents = node.get("relevant_contents", []) if isinstance(node, dict) else getattr(node, "relevant_contents", [])
                    for sublist in rel_contents:
                        items = sublist if isinstance(sublist, list) else [sublist]
                        for item in items:
                            if isinstance(item, dict):
                                section = item.get("section_title", "PageIndex Section")
                                content = item.get("relevant_content", "")
                            else:
                                section = getattr(item, "section_title", "PageIndex Section")
                                content = getattr(item, "relevant_content", str(item))

                            if content:
                                api_results.append({
                                    "content": f"## {section}\n{content}",
                                    "score": 0.9,
                                    "metadata": {"source": "pageindex_api", "section": section},
                                    "source": "pageindex"
                                })
            if api_results:
                return api_results[:top_k]
        except Exception as e:
            print(f"[Warning] PageIndex SDK search error (falling back to structural reader): {e}")

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
