"""
Task 6 — Lexical Search Module (BM25).

Mặc định sử dụng BM25. Nếu dùng phương pháp khác (TF-IDF, Elasticsearch,
Weaviate BM25 built-in), hãy giải thích cơ chế trong buổi demo → +5 bonus.

Cài đặt:
    pip install rank-bm25

BM25 hoạt động thế nào:
    - Term Frequency (TF): từ xuất hiện nhiều trong document → điểm cao
    - Inverse Document Frequency (IDF): từ hiếm → quan trọng hơn
    - Document length normalization: document dài không bị ưu tiên quá mức
    - Formula: score(q,d) = Σ IDF(qi) * (tf(qi,d) * (k1+1)) / (tf(qi,d) + k1*(1-b+b*|d|/avgdl))
    - k1=1.5 (term saturation), b=0.75 (length normalization)
"""

import unicodedata
from rank_bm25 import BM25Okapi
from .task4_chunking_indexing import load_documents, chunk_documents

def strip_accents(s: str) -> str:
    s = s.replace('đ', 'd').replace('Đ', 'D')
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('utf-8')


_BM25_INDEX = None
_CORPUS_CACHE = None


def get_corpus() -> list[dict]:
    """Tải hoặc cache corpus dạng list chunk dicts."""
    global _CORPUS_CACHE
    if _CORPUS_CACHE is None:
        docs = load_documents()
        chunks = chunk_documents(docs)
        _CORPUS_CACHE = chunks
    return _CORPUS_CACHE


def build_bm25_index(corpus: list[dict]):
    """
    Xây dựng BM25 index từ corpus với hỗ trợ metadata và từ khóa song ngữ.
    """
    synonyms = {
        "tuition": "học phí hoc phi tuition fee",
        "fee": "học phí hoc phi phí phi fee",
        "scholarship": "học bổng hoc bong scholarship",
        "accommodation": "ký túc xá ky tuc xa chỗ ở cho o accommodation",
        "library": "thư viện thu vien library",
        "registration": "đăng ký dang ky registration enrol enrolment",
        "course": "môn học mon hoc học phần hoc phan phần học phan hoc course",
    }
    tokenized_corpus = []
    for doc in corpus:
        text = doc["content"].lower()
        meta = doc.get("metadata", {})
        source = str(meta.get("source", "")).lower()
        full_text = f"{text} {source}"
        for en, vi in synonyms.items():
            if en in source or any(v in text for v in vi.split()):
                full_text += f" {en}"
        tokenized_corpus.append(strip_accents(full_text).split())
    bm25 = BM25Okapi(tokenized_corpus)
    return bm25


def get_bm25_index():
    global _BM25_INDEX
    if _BM25_INDEX is None:
        corpus = get_corpus()
        _BM25_INDEX = build_bm25_index(corpus)
    return _BM25_INDEX


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm từ khóa sử dụng BM25.
    """
    corpus = get_corpus()
    if not corpus:
        return []

    bm25 = get_bm25_index()
    clean_query = strip_accents(query.lower())
    tokenized_query = clean_query.split()

    scores = bm25.get_scores(tokenized_query)

    import numpy as np
    top_indices = np.argsort(scores)[::-1]

    results = []
    for idx in top_indices:
        score = float(scores[idx])
        if score > 0 or len(results) == 0:
            item = corpus[idx].copy()
            results.append({
                "content": item["content"],
                "score": score,
                "metadata": item.get("metadata", {})
            })
        if len(results) >= top_k:
            break

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    results = lexical_search("tuition fee payment methods", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
