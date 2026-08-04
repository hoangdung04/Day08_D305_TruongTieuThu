import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from .task4_chunking_indexing import get_collection, get_embedding_model


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm ngữ nghĩa sử dụng vector similarity.
    """
    try:
        model = get_embedding_model()
        raw_emb = model.encode([query], show_progress_bar=False)[0]
        query_vector = raw_emb.tolist() if hasattr(raw_emb, "tolist") else raw_emb

        collection = get_collection()
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
    except Exception as e:
        print(f"[Warning] ChromaDB auto-recovery triggered: {e}")
        from .task4_chunking_indexing import run_pipeline
        run_pipeline()
        model = get_embedding_model()
        raw_emb = model.encode([query], show_progress_bar=False)[0]
        query_vector = raw_emb.tolist() if hasattr(raw_emb, "tolist") else raw_emb
        collection = get_collection()
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

    output = []
    if results and results.get("documents") and results["documents"][0]:
        docs = results["documents"][0]
        metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
        dists = results["distances"][0] if results.get("distances") else [0.0] * len(docs)

        for doc, meta, dist in zip(docs, metas, dists):
            score = max(0.0, 1.0 - dist)
            output.append({
                "content": doc,
                "score": round(score, 4),
                "metadata": meta
            })

    output.sort(key=lambda x: x["score"], reverse=True)
    return output[:top_k]


if __name__ == "__main__":
    results = semantic_search("tuition fee payment", top_k=5)
    print(f"[OK] Returned {len(results)} results:")
    for r in results:
        print(f"  [{r['score']:.4f}] {r['content'][:100]}...")

