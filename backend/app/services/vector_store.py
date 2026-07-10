# backend/app/services/vector_store.py
import shutil
import os
import urllib.request
import json
import uuid
from typing import List, Optional, Dict
from langchain.schema import Document
from langchain.embeddings.base import Embeddings
from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.core.config import settings

class BatchOllamaEmbeddings(Embeddings):
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url
        self.model = model
        
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents using Ollama's batch API (9x faster) with local caching."""
        if not texts:
            return []
            
        # Load local embedding cache
        cache_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "scratch", "embedding_cache.json")
        cache = {}
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    cache = json.load(f)
            except Exception as e:
                print(f"Error loading embedding cache: {e}")

        # Check which texts can be retrieved from cache
        embeddings_all = [None] * len(texts)
        missing_indices = []
        missing_texts = []
        
        for idx, text in enumerate(texts):
            if text in cache:
                embeddings_all[idx] = cache[text]
            else:
                missing_indices.append(idx)
                missing_texts.append(text)
                
        if missing_texts:
            print(f"   [Embedding Cache] Cache hit: {len(texts) - len(missing_texts)}/{len(texts)}. Generating {len(missing_texts)} new embeddings...")
            
            # Embed missing texts in batches of 15
            batch_size = 15
            new_embeddings = []
            
            for i in range(0, len(missing_texts), batch_size):
                batch = missing_texts[i:i+batch_size]
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
                        new_embeddings.extend(embeddings)
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
                                new_embeddings.append(res.get("embeddings", [])[0])
                        except Exception:
                            dim = 1024 if "bge-m3" in self.model.lower() else 768
                            new_embeddings.append([0.0] * dim)

            # Assign new embeddings back to correct indices
            for idx, emb in zip(missing_indices, new_embeddings):
                embeddings_all[idx] = emb
                # Update cache
                cache[texts[idx]] = emb
                
            # Save updated cache
            try:
                os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(cache, f)
            except Exception as e:
                print(f"Error saving embedding cache: {e}")
                
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

class MockCollection:
    def __init__(self, store: 'QdrantVectorStore'):
        self.store = store

    def count(self) -> int:
        client = QdrantClient(path=self.store.path)
        try:
            return client.count(collection_name=self.store.collection_name).count
        except Exception:
            return 0
        finally:
            client.close()

    def get(self, where: Optional[Dict] = None, limit: Optional[int] = None, include: Optional[List[str]] = None) -> Dict:
        filter_obj = None
        if where:
            conditions = []
            for key, val in where.items():
                if isinstance(val, dict) and "$in" in val:
                    conditions.append(models.FieldCondition(
                        key=f"metadata.{key}",
                        match=models.MatchAny(any=val["$in"])
                    ))
                else:
                    conditions.append(models.FieldCondition(
                        key=f"metadata.{key}",
                        match=models.MatchValue(value=val)
                    ))
            if conditions:
                filter_obj = models.Filter(must=conditions)
                
        client = QdrantClient(path=self.store.path)
        try:
            scroll_res, _ = client.scroll(
                collection_name=self.store.collection_name,
                scroll_filter=filter_obj,
                limit=limit or 10000,
                with_payload=True,
                with_vectors=False
            )
        except Exception:
            scroll_res = []
        finally:
            client.close()
        
        formatted = {"ids": [], "metadatas": [], "documents": []}
        for point in scroll_res:
            formatted["ids"].append(point.id)
            payload = point.payload or {}
            formatted["metadatas"].append(payload.get("metadata", {}))
            formatted["documents"].append(payload.get("page_content", ""))
            
        return formatted

class MockRetriever:
    def __init__(self, store, k):
        self.store = store
        self.k = k
        
    def get_relevant_documents(self, query: str) -> List[Document]:
        return self.store.similarity_search(query, k=self.k)

class QdrantVectorStore:
    def __init__(self, path: str, collection_name: str, embedding_function):
        self.path = path
        self.collection_name = collection_name
        self.embedding_function = embedding_function
        self._init_collection()
        self._collection = MockCollection(self)

    def _init_collection(self):
        dummy_vector = self.embedding_function.embed_query("test")
        vector_dim = len(dummy_vector)
        
        client = QdrantClient(path=self.path)
        try:
            collections = client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            if not exists:
                client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=vector_dim,
                        distance=models.Distance.COSINE
                    )
                )
        except Exception:
            pass
        finally:
            client.close()

    def add_documents(self, documents: List[Document]):
        if not documents:
            return
        
        texts = [doc.page_content for doc in documents]
        embeddings = self.embedding_function.embed_documents(texts)
        
        points = []
        for i, (doc, vector) in enumerate(zip(documents, embeddings)):
            chunk_id = doc.metadata.get("chunk_id", str(uuid.uuid4()))
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id))
            
            points.append(models.PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "page_content": doc.page_content,
                    "metadata": doc.metadata
                }
            ))
            
        client = QdrantClient(path=self.path)
        try:
            client.upsert(
                collection_name=self.collection_name,
                points=points
            )
        finally:
            client.close()

    def similarity_search_by_vector(self, query_vector: List[float], k: int = 4) -> List[Document]:
        client = QdrantClient(path=self.path)
        try:
            search_result = client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=k
            )
            hits = search_result.points
        except Exception:
            hits = []
        finally:
            client.close()
        
        docs = []
        for hit in hits:
            payload = hit.payload or {}
            docs.append(Document(
                page_content=payload.get("page_content", ""),
                metadata=payload.get("metadata", {})
            ))
        return docs

    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        query_vector = self.embedding_function.embed_query(query)
        return self.similarity_search_by_vector(query_vector, k)

    def delete_collection(self):
        client = QdrantClient(path=self.path)
        try:
            client.delete_collection(self.collection_name)
        except Exception:
            pass
        finally:
            client.close()

    def persist(self):
        pass

    def as_retriever(self, search_kwargs: Dict):
        k = search_kwargs.get("k", 5)
        return MockRetriever(self, k)

class VectorStoreManager:
    def __init__(self):
        print("[Init] Initializing Vector Store Manager (with Qdrant DB)...")
        self.embeddings = BatchOllamaEmbeddings(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.EMBEDDING_MODEL
        )
        self.vendor_store = None
        self.govt_store = None
    
    def get_vendor_store(self) -> QdrantVectorStore:
        if self.vendor_store is None:
            settings.VENDOR_DB_DIR.mkdir(parents=True, exist_ok=True)
            self.vendor_store = QdrantVectorStore(
                path=str(settings.VENDOR_DB_DIR),
                collection_name=settings.VENDOR_COLLECTION,
                embedding_function=self.embeddings
            )
        return self.vendor_store
    
    def get_govt_store(self) -> QdrantVectorStore:
        if self.govt_store is None:
            settings.GOVT_DB_DIR.mkdir(parents=True, exist_ok=True)
            self.govt_store = QdrantVectorStore(
                path=str(settings.GOVT_DB_DIR),
                collection_name=settings.GOVT_COLLECTION,
                embedding_function=self.embeddings
            )
        return self.govt_store
    
    def add_vendor_documents(self, documents: List[Document]) -> int:
        if not documents:
            return 0
        store = self.get_vendor_store()
        
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
            print("[Success] Vendor collection deleted programmatically")
        except Exception as e:
            print(f"[Warning] Error deleting vendor collection: {e}")
        try:
            self.get_govt_store().delete_collection()
            print("[Success] Govt collection deleted programmatically")
        except Exception as e:
            print(f"[Warning] Error deleting govt collection: {e}")
        self.vendor_store = None
        self.govt_store = None
        print("[Success] Both collections cleared")