import os
import nltk
from typing import List, Optional, Tuple
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

nltk.download('punkt', quiet=True)
from nltk.tokenize import sent_tokenize

EMBEDDING_MODEL = "intfloat/multilingual-e5-small"
CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "knowledge_base"
KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "knowledge")
SIMILARITY_THRESHOLD = 0.3

_model = None
_client = None
_collection = None

def get_embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model

def get_chroma_collection():
    global _client, _collection
    if _client is None:
        _client = chromadb.PersistentClient(path=CHROMA_DIR, settings=Settings(anonymized_telemetry=False))
        try:
            _collection = _client.get_collection(COLLECTION_NAME)
        except:
            _collection = _client.create_collection(COLLECTION_NAME)
    return _collection

def split_into_chunks(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    sentences = sent_tokenize(text, language='russian')
    chunks = []
    current_chunk = ""
    for sent in sentences:
        if len(current_chunk) + len(sent) <= chunk_size:
            current_chunk += " " + sent
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            overlap_text = current_chunk[-overlap:] if overlap > 0 else ""
            current_chunk = overlap_text + " " + sent
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def index_knowledge_files():
    collection = get_chroma_collection()
    model = get_embedding_model()
    
    try:
        collection.delete(where={})
        print("Cleared existing collection")
    except:
        pass
    
    for filename in os.listdir(KNOWLEDGE_DIR):
        if not filename.endswith(".txt"):
            continue
        filepath = os.path.join(KNOWLEDGE_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
        knowledge_type = filename[:-4]
        chunks = split_into_chunks(text)
        ids = []
        documents = []
        metadatas = []
        for i, chunk in enumerate(chunks):
            chunk_id = f"{knowledge_type}_{i}"
            ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append({"type": knowledge_type, "source": filename})
        embeddings = model.encode(documents, show_progress_bar=True).tolist()
        collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )
        print(f"Indexed {len(chunks)} chunks from {filename}")

def retrieve_knowledge(query: str, top_k: int = 5, filter_type: Optional[str] = None) -> Tuple[List[str], dict]:
    collection = get_chroma_collection()
    model = get_embedding_model()
    query_embedding = model.encode([query]).tolist()[0]
    where = {"type": filter_type} if filter_type else None
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k * 2,
        where=where
    )
    
    metadata = {
        "type": filter_type,
        "requested_k": top_k,
        "found_count": 0,
        "filtered_count": 0,
        "used_fallback": False
    }
    
    if not results or not results['documents'] or not results['documents'][0]:
        metadata["found_count"] = 0
        metadata["filtered_count"] = 0
        return [], metadata
    
    documents = results['documents'][0]
    distances = results['distances'][0] if 'distances' in results else [1.0] * len(documents)
    
    metadata["found_count"] = len(documents)
    
    filtered_docs = []
    for doc, dist in zip(documents, distances):
        if dist < SIMILARITY_THRESHOLD:
            filtered_docs.append(doc)
    
    metadata["filtered_count"] = len(filtered_docs)
    
    if not filtered_docs and documents:
        filtered_docs = documents[:top_k]
        metadata["used_fallback"] = True
    
    result_docs = filtered_docs[:top_k]
    
    return result_docs, metadata

def retrieve_knowledge_simple(query: str, top_k: int = 5, filter_type: Optional[str] = None) -> List[str]:
    docs, _ = retrieve_knowledge(query, top_k, filter_type)
    return docs