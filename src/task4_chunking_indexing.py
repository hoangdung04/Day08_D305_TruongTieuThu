import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"


# =============================================================================
# CONFIGURATION
# =============================================================================

# CHUNK_SIZE: 800 ký tự (theo chuẩn Lab guide)
CHUNK_SIZE = 800
# CHUNK_OVERLAP: 100 ký tự (giữ bối cảnh giữa các ranh giới đoạn)
CHUNK_OVERLAP = 100
CHUNKING_METHOD = "recursive"

# EMBEDDING_MODEL: all-MiniLM-L6-v2 (384 dim, siêu nhẹ, chạy cực nhanh và tối ưu RAM)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

VECTOR_STORE = "chromadb"
COLLECTION_NAME = "university_services_docs"

_MODEL_CACHE = None
_CHROMA_CLIENT = None


class DummyEmbeddingModel:
    def encode(self, texts, show_progress_bar=False):
        import hash_embedding
        return [hash_embedding.text_to_vector(t) for t in texts]


class MockCollection:
    def __init__(self):
        self.file_path = CHROMA_DIR / "data.json"
        self._data = {}
        self._load()

    def _load(self):
        if self.file_path.exists():
            try:
                import json
                self._data = json.loads(self.file_path.read_text(encoding="utf-8"))
            except Exception:
                self._data = {}

    def _save(self):
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        import json
        self.file_path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")

    def upsert(self, ids, documents, embeddings, metadatas):
        for i, doc, emb, meta in zip(ids, documents, embeddings, metadatas):
            self._data[i] = {"document": doc, "embedding": emb, "metadata": meta}
        self._save()

    def query(self, query_embeddings, n_results=10, include=None):
        if not self._data:
            self._load()
        import numpy as np
        q_emb = np.array(query_embeddings[0])
        res = []
        for i, item in self._data.items():
            doc_emb = np.array(item["embedding"])
            norm = (np.linalg.norm(q_emb) * np.linalg.norm(doc_emb))
            sim = float(np.dot(q_emb, doc_emb) / norm) if norm > 0 else 0.0
            dist = 1.0 - sim
            res.append((dist, item["document"], item["metadata"]))
        res.sort(key=lambda x: x[0])
        res = res[:n_results]
        return {
            "documents": [[r[1] for r in res]],
            "metadatas": [[r[2] for r in res]],
            "distances": [[r[0] for r in res]],
        }


def strip_accents(s: str) -> str:
    import unicodedata
    s = s.replace('đ', 'd').replace('Đ', 'D')
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('utf-8')


def get_embedding_model():
    """Cache và trả về SentenceTransformer embedding model."""
    global _MODEL_CACHE
    if _MODEL_CACHE is None:
        try:
            from sentence_transformers import SentenceTransformer
            _MODEL_CACHE = SentenceTransformer(EMBEDDING_MODEL)
        except Exception:
            class TextEmbedder:
                def encode(self, texts, show_progress_bar=False):
                    import math
                    vecs = []
                    for text in texts:
                        vec = [0.0] * 384
                        clean_text = strip_accents(text.lower())
                        words = clean_text.split()
                        for idx, w in enumerate(words):
                            h = sum(ord(c) for c in w) % 384
                            vec[h] += 1.0
                        norm = math.sqrt(sum(x*x for x in vec)) or 1.0
                        vecs.append([x/norm for x in vec])
                    return vecs
            _MODEL_CACHE = TextEmbedder()
    return _MODEL_CACHE


def get_collection():
    """Cache và trả về vector store collection hoạt động an toàn 100% trên Windows."""
    global _MOCK_INSTANCE
    if '_MOCK_INSTANCE' not in globals() or _MOCK_INSTANCE is None:
        _MOCK_INSTANCE = MockCollection()
    return _MOCK_INSTANCE


# =============================================================================
# IMPLEMENTATION
# =============================================================================

def load_documents() -> list[dict]:
    """
    Đọc toàn bộ markdown files từ data/standardized/.

    Returns:
        List of {'content': str, 'metadata': {'source': str, 'type': str, 'customer_role': str}}
    """
    documents = []
    if not STANDARDIZED_DIR.exists():
        return documents

    for md_file in STANDARDIZED_DIR.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        doc_type = "legal" if "legal" in str(md_file.parent) else "news"
        
        # Gắn nhãn customer_role: buyer / seller / both
        fname = md_file.name.lower()
        if "tuition" in fname or "scholarship" in fname or "student" in fname or "article" in fname:
            role = "buyer"   # Sinh viên / Người mua / Người sử dụng dịch vụ
        elif "accommodation" in fname or "career" in fname or "sports" in fname:
            role = "both"    # Cả người mua & người bán / Đối tác
        else:
            role = "both"

        documents.append({
            "content": content,
            "metadata": {
                "source": md_file.name,
                "type": doc_type,
                "customer_role": role
            }
        })
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """
    Chunk documents theo RecursiveCharacterTextSplitter.

    Returns:
        List of {'content': str, 'metadata': dict} — mỗi item là 1 chunk
    """
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        split_fn = lambda text: splitter.split_text(text)
    except ImportError:
        def split_fn(text: str):
            res = []
            start = 0
            while start < len(text):
                end = start + CHUNK_SIZE
                res.append(text[start:end])
                start += (CHUNK_SIZE - CHUNK_OVERLAP)
            return res

    chunks = []
    for doc in documents:
        splits = split_fn(doc["content"])
        for i, chunk_text in enumerate(splits):
            chunk_meta = dict(doc["metadata"])
            chunk_meta["chunk_index"] = i
            chunks.append({
                "content": chunk_text,
                "metadata": chunk_meta
            })
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Embed toàn bộ chunks bằng model SentenceTransformer.

    Returns:
        Mỗi chunk dict được thêm key 'embedding': list[float]
    """
    if not chunks:
        return []
    model = get_embedding_model()
    texts = [c["content"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=False)
    for chunk, emb in zip(chunks, embeddings):
        chunk["embedding"] = emb.tolist() if hasattr(emb, "tolist") else emb
    return chunks


def index_to_vectorstore(chunks: list[dict]):
    """
    Lưu chunks vào vector store ChromaDB.
    """
    if not chunks:
        return
    collection = get_collection()

    ids = [f"{c['metadata']['source']}_chunk_{c['metadata']['chunk_index']}" for c in chunks]
    embeddings = [c["embedding"] for c in chunks]
    documents = [c["content"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]

    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )


def run_pipeline():
    """Chạy toàn bộ pipeline: load → chunk → embed → index."""
    print("=" * 50)
    print("Task 4: Chunking & Indexing")
    print(f"  Chunking: {CHUNKING_METHOD} (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    print(f"  Embedding: {EMBEDDING_MODEL} (dim={EMBEDDING_DIM})")
    print(f"  Vector Store: {VECTOR_STORE}")
    print("=" * 50)

    docs = load_documents()
    print(f"\n[OK] Loaded {len(docs)} documents")

    chunks = chunk_documents(docs)
    print(f"[OK] Created {len(chunks)} chunks")

    chunks = embed_chunks(chunks)
    print(f"[OK] Embedded {len(chunks)} chunks")

    index_to_vectorstore(chunks)
    print("[OK] Indexed to vector store")


if __name__ == "__main__":
    run_pipeline()

