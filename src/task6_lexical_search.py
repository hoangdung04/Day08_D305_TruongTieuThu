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
from .task4_chunking_indexing import load_documents, chunk_documents

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    BM25Okapi = None

def strip_accents(s: str) -> str:
    s = s.replace('đ', 'd').replace('Đ', 'D')
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('utf-8')


def normalize_query(query: str) -> str:
    """Chuẩn hoá dấu tiếng Việt và thêm vài thuật ngữ song ngữ của corpus RMIT."""
    clean = strip_accents(query.lower())
    aliases = {
        "tuition": "hoc phi",
        "fee": "hoc phi",
        "scholarship": "hoc bong",
        "accommodation": "ky tuc xa",
        "library": "thu vien",
    }
    return " ".join([clean, *(aliases.get(token, "") for token in clean.split())])


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
    Xây dựng BM25 index từ corpus.
    """
    tokenized_corpus = [
        strip_accents(doc["content"].lower()).split() for doc in corpus
    ]
    if BM25Okapi is not None:
        return BM25Okapi(tokenized_corpus)

    # Fallback thuần Python để pipeline vẫn chạy được khi môi trường demo chưa
    # cài rank-bm25. Công thức giữ nguyên các thành phần TF, IDF và chuẩn hoá độ dài.
    import math
    document_frequency: dict[str, int] = {}
    for tokens in tokenized_corpus:
        for token in set(tokens):
            document_frequency[token] = document_frequency.get(token, 0) + 1
    return {
        "tokens": tokenized_corpus,
        "df": document_frequency,
        "avgdl": sum(len(tokens) for tokens in tokenized_corpus) / max(len(tokenized_corpus), 1),
    }


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
    clean_query = normalize_query(query)
    tokenized_query = clean_query.split()

    if BM25Okapi is not None:
        scores = bm25.get_scores(tokenized_query)
    else:
        import math
        n_docs = len(bm25["tokens"])
        k1, b = 1.5, 0.75
        scores = []
        for tokens in bm25["tokens"]:
            doc_len = len(tokens)
            score = 0.0
            for token in tokenized_query:
                tf = tokens.count(token)
                if not tf:
                    continue
                df = bm25["df"].get(token, 0)
                idf = math.log(1 + (n_docs - df + 0.5) / (df + 0.5))
                score += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * doc_len / bm25["avgdl"]))
            scores.append(score)

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
