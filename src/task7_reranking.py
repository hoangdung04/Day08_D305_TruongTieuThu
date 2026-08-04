"""
Task 7 — Reranking Module.

Chọn 1 trong các phương pháp:
    - Cross-encoder reranker: Jina Reranker v2 (multilingual) hoặc Qwen3-Reranker
    - MMR (Maximal Marginal Relevance): tự implement
    - RRF (Reciprocal Rank Fusion): tự implement — khuyến nghị vì không cần API key

Nếu dùng MMR hoặc RRF, đảm bảo hiểu và giải thích được cơ chế.

Lưu ý quan trọng về RRF (sẽ dùng lại ở Task 9): điểm RRF fused CHỈ phụ thuộc thứ hạng,
không phải độ tương đồng thật. Top-1 sau khi fuse luôn xấp xỉ 1/(k+1) ≈ 0.0164 (k=60),
bất kể nội dung đó có thật sự liên quan đến câu hỏi hay không. Đừng dùng điểm RRF để
quyết định fallback ở Task 9 — xem ghi chú ở đó.
"""

from typing import Optional


def rerank_cross_encoder(
    query: str, candidates: list[dict], top_k: int = 5
) -> list[dict]:
    """
    Rerank candidates sử dụng cross-encoder hoặc lexical relevance score.
    """
    if not candidates:
        return []
    
    clean_query = query.lower().split()
    rescored = []
    for item in candidates:
        content = item.get("content", "").lower()
        match_count = sum(1 for w in clean_query if w in content)
        overlap_ratio = match_count / (len(clean_query) or 1)
        orig_score = float(item.get("score", 0.0))
        new_score = orig_score * 0.5 + overlap_ratio * 0.5
        cp = item.copy()
        cp["score"] = new_score
        rescored.append(cp)

    rescored.sort(key=lambda x: x["score"], reverse=True)
    return rescored[:top_k]


def rerank_mmr(
    query_embedding: list[float],
    candidates: list[dict],
    top_k: int = 5,
    lambda_param: float = 0.7,
) -> list[dict]:
    """
    Maximal Marginal Relevance — chọn candidates vừa relevant vừa diverse.
    """
    if not candidates:
        return []
    
    # Giả định candidates có score là relevance
    selected = []
    remaining = list(range(len(candidates)))

    for _ in range(min(top_k, len(candidates))):
        best_idx = None
        best_score = float('-inf')

        for idx in remaining:
            relevance = candidates[idx].get("score", 0.0)
            max_sim_to_selected = 0.0
            for sel_idx in selected:
                # Tính độ tương đồng đơn giản bằng từ xuất hiện chung giữa nội dung
                c1 = set(candidates[idx]["content"].lower().split())
                c2 = set(candidates[sel_idx]["content"].lower().split())
                overlap = len(c1 & c2) / (max(len(c1), len(c2)) or 1)
                max_sim_to_selected = max(max_sim_to_selected, overlap)

            mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim_to_selected
            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = idx

        if best_idx is not None:
            item = candidates[best_idx].copy()
            item["score"] = best_score
            selected.append(best_idx)
            remaining.remove(best_idx)

    return [candidates[i] for i in selected]


def rerank_rrf(
    ranked_lists: list[list[dict]], top_k: int = 5, k: int = 60
) -> list[dict]:
    """
    Reciprocal Rank Fusion — gộp kết quả từ nhiều ranker.
    RRF(d) = Σ 1 / (k + rank_r(d))
    """
    if not ranked_lists:
        return []

    # Nếu chỉ truyền vào 1 list candidates đơn lẻ
    if isinstance(ranked_lists[0], dict):
        ranked_lists = [ranked_lists]

    rrf_scores = {}
    content_map = {}

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, 1):
            key = item.get("content", "")
            rrf_scores[key] = rrf_scores.get(key, 0.0) + 1.0 / (k + rank)
            content_map[key] = item

    sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    results = []
    for content, score in sorted_items[:top_k]:
        item = content_map[content].copy()
        item["score"] = float(score)
        results.append(item)

    return results


# =============================================================================
# Main rerank interface
# =============================================================================

def rerank(
    query: str,
    candidates: list[dict],
    top_k: int = 5,
    method: str = "rrf",  # "cross_encoder" | "mmr" | "rrf"
) -> list[dict]:
    """
    Unified reranking interface.
    """
    if not candidates:
        return []

    if method == "cross_encoder":
        return rerank_cross_encoder(query, candidates, top_k)
    elif method == "mmr":
        return rerank_mmr([], candidates, top_k)
    elif method == "rrf":
        if isinstance(candidates, list) and len(candidates) > 0 and isinstance(candidates[0], dict):
            return rerank_rrf([candidates], top_k=top_k)
        return rerank_rrf(candidates, top_k=top_k)
    else:
        # Fallback to RRF
        return rerank_rrf([candidates], top_k=top_k)


if __name__ == "__main__":
    # Test with dummy data
    dummy_candidates = [
        {"content": "Tuition fee payment schedule", "score": 0.8, "metadata": {}},
        {"content": "Scholarship eligibility requirements", "score": 0.6, "metadata": {}},
        {"content": "Library study room booking guide", "score": 0.5, "metadata": {}},
    ]
    results = rerank("tuition fee payment", dummy_candidates, top_k=2)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content']}")
