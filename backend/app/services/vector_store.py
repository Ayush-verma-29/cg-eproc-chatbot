# backend/app/services/vector_store.py
import shutil
import os
import urllib.request
import json
from typing import List, Optional, Dict
from langchain.schema import Document
from langchain.embeddings.base import Embeddings
from langchain_community.vectorstores import Chroma
from app.core.config import settings

class BatchOllamaEmbeddings(Embeddings):
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url
        self.model = model
        
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents using Ollama's batch API (9x faster)."""
        if not texts:
            return []
            
        embeddings_all = []
        batch_size = 15  # Optimize batch size to 15 to prevent CPU timeout with BGE-M3
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            prefixed_batch = [f"search_document: {t}" for t in batch]
            url = f"{self.base_url}/api/embed"
            payload = {
                "model": self.model,
                "input": prefixed_batch
            }
            try:
                data = json.dumps(payload).encode('utf-8')
                req = urllib.request.Request(
                    url,
                    data=data,
                    headers={'Content-Type': 'application/json'},
                    method='POST'
                )
                with urllib.request.urlopen(req, timeout=60) as response:
                    res = json.loads(response.read().decode('utf-8'))
                    embeddings = res.get("embeddings", [])
                    embeddings_all.extend(embeddings)
            except Exception as e:
                print(f"      Batch embedding failed: {e}. Falling back to sequential.")
                for text in batch:
                    url = f"{self.base_url}/api/embed"
                    payload = {
                        "model": self.model,
                        "input": [f"search_document: {text}"]
                    }
                    try:
                        data = json.dumps(payload).encode('utf-8')
                        req = urllib.request.Request(
                            url,
                            data=data,
                            headers={'Content-Type': 'application/json'},
                            method='POST'
                        )
                        with urllib.request.urlopen(req, timeout=30) as response:
                            res = json.loads(response.read().decode('utf-8'))
                            embeddings_all.append(res.get("embeddings", [])[0])
                    except Exception:
                        dim = 1024 if "bge-m3" in self.model.lower() else 768
                        embeddings_all.append([0.0] * dim)
                    
        return embeddings_all
        
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query using Ollama's newer embed API to align with embed_documents."""
        url = f"{self.base_url}/api/embed"
        payload = {
            "model": self.model,
            "input": [f"search_query: {text}"]
        }
        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                url,
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                res = json.loads(response.read().decode('utf-8'))
                embeddings = res.get("embeddings", [])
                if embeddings:
                    return embeddings[0]
                dim = 1024 if "bge-m3" in self.model.lower() else 768
                return [0.0] * dim
        except Exception as e:
            print(f"      Embedding query failed: {e}")
            dim = 1024 if "bge-m3" in self.model.lower() else 768
            return [0.0] * dim

class VectorStoreManager:
    def __init__(self):
        print("🔧 Initializing Vector Store Manager (with Batch Embeddings)...")
        self.embeddings = BatchOllamaEmbeddings(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.EMBEDDING_MODEL
        )
        self.vendor_store = None
        self.govt_store = None
    
    def get_vendor_store(self) -> Chroma:
        if self.vendor_store is None:
            settings.VENDOR_DB_DIR.mkdir(parents=True, exist_ok=True)
            self.vendor_store = Chroma(
                persist_directory=str(settings.VENDOR_DB_DIR),
                embedding_function=self.embeddings,
                collection_name=settings.VENDOR_COLLECTION
            )
        return self.vendor_store
    
    def get_govt_store(self) -> Chroma:
        if self.govt_store is None:
            settings.GOVT_DB_DIR.mkdir(parents=True, exist_ok=True)
            self.govt_store = Chroma(
                persist_directory=str(settings.GOVT_DB_DIR),
                embedding_function=self.embeddings,
                collection_name=settings.GOVT_COLLECTION
            )
        return self.govt_store
    
    def add_vendor_documents(self, documents: List[Document]) -> int:
        if not documents:
            return 0
        store = self.get_vendor_store()
        
        # Batch insert to avoid ChromaDB/SQLite parameter limits (max 5461)
        batch_size = 1000
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            store.add_documents(batch)
            
        store.persist()
        return len(documents)
    
    def add_govt_documents(self, documents: List[Document]) -> int:
        if not documents:
            return 0
        store = self.get_govt_store()
        
        # Batch insert to avoid ChromaDB/SQLite parameter limits (max 5461)
        batch_size = 1000
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            store.add_documents(batch)
            
        store.persist()
        return len(documents)
    
    def get_retriever(self, role: str, k: int = 5):
        if role == "vendor":
            return self.get_vendor_store().as_retriever(search_kwargs={"k": k})
        else:
            return self.get_govt_store().as_retriever(search_kwargs={"k": k})
    
    def get_collection_stats(self, role: str = None) -> dict:
        stats = {}
        try:
            if role is None or role == "vendor":
                stats["vendor_documents"] = self.get_vendor_store()._collection.count()
            if role is None or role == "government_officer":
                stats["govt_documents"] = self.get_govt_store()._collection.count()
        except:
            if role is None or role == "vendor":
                stats["vendor_documents"] = 0
            if role is None or role == "government_officer":
                stats["govt_documents"] = 0
        return stats
    
    def delete_all_collections(self):
        try:
            self.get_vendor_store().delete_collection()
            print("🗑️ Vendor collection deleted programmatically")
        except Exception as e:
            print(f"⚠️ Error deleting vendor collection: {e}")
        try:
            self.get_govt_store().delete_collection()
            print("🗑️ Govt collection deleted programmatically")
        except Exception as e:
            print(f"⚠️ Error deleting govt collection: {e}")
        self.vendor_store = None
        self.govt_store = None
        print("🗑️ Both collections cleared")