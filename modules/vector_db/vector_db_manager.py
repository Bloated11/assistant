import logging
import os
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class VectorDBManager:
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.db_path = config.get('db_path', 'data/vector_db')
        self.collection_name = config.get('collection_name', 'documents')
        self.embedding_model = config.get('embedding_model', 'all-MiniLM-L6-v2')
        self.provider = config.get('provider', 'chromadb')
        
        self.client = None
        self.collection = None
        self.embeddings = None
        
        if self.enabled:
            self._initialize()
        
        logger.info(f"VectorDBManager initialized with {self.provider}")
    
    def _initialize(self):
        try:
            if self.provider == 'chromadb':
                self._initialize_chromadb()
            elif self.provider == 'faiss':
                self._initialize_faiss()
            else:
                logger.error(f"Unknown provider: {self.provider}")
        except Exception as e:
            logger.error(f"Error initializing vector database: {e}")
            self.enabled = False
    
    def _initialize_chromadb(self):
        try:
            import chromadb
            from chromadb.config import Settings
            
            os.makedirs(self.db_path, exist_ok=True)
            
            self.client = chromadb.PersistentClient(
                path=self.db_path,
                settings=Settings(anonymized_telemetry=False)
            )
            
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Document embeddings for semantic search"}
            )
            
            logger.info("ChromaDB initialized successfully")
        except ImportError:
            logger.warning("chromadb not installed. Run: pip install chromadb")
            self.enabled = False
        except Exception as e:
            logger.error(f"ChromaDB initialization error: {e}")
            self.enabled = False
    
    def _initialize_faiss(self):
        try:
            import faiss
            import numpy as np
            from sentence_transformers import SentenceTransformer
            
            self.embeddings = SentenceTransformer(self.embedding_model)
            
            embedding_dim = self.embeddings.get_sentence_embedding_dimension()
            self.index = faiss.IndexFlatL2(embedding_dim)
            
            self.documents = []
            self.metadata = []
            
            index_path = os.path.join(self.db_path, 'faiss.index')
            if os.path.exists(index_path):
                self.index = faiss.read_index(index_path)
                
                meta_path = os.path.join(self.db_path, 'metadata.json')
                if os.path.exists(meta_path):
                    with open(meta_path, 'r') as f:
                        data = json.load(f)
                        self.documents = data.get('documents', [])
                        self.metadata = data.get('metadata', [])
            
            logger.info("FAISS initialized successfully")
        except ImportError:
            logger.warning("faiss or sentence-transformers not installed")
            self.enabled = False
        except Exception as e:
            logger.error(f"FAISS initialization error: {e}")
            self.enabled = False
    
    def add_document(self, document: str, metadata: Dict[str, Any] = None) -> bool:
        if not self.enabled:
            return False
        
        try:
            if self.provider == 'chromadb':
                return self._add_document_chromadb(document, metadata)
            elif self.provider == 'faiss':
                return self._add_document_faiss(document, metadata)
            return False
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return False
    
    def _add_document_chromadb(self, document: str, metadata: Dict[str, Any] = None) -> bool:
        doc_id = f"doc_{datetime.now().timestamp()}"
        
        meta = metadata or {}
        meta['added_at'] = datetime.now().isoformat()
        
        self.collection.add(
            documents=[document],
            metadatas=[meta],
            ids=[doc_id]
        )
        
        return True
    
    def _add_document_faiss(self, document: str, metadata: Dict[str, Any] = None) -> bool:
        import numpy as np
        
        embedding = self.embeddings.encode([document])[0]
        
        self.index.add(np.array([embedding]).astype('float32'))
        
        self.documents.append(document)
        self.metadata.append(metadata or {})
        
        self._save_faiss()
        
        return True
    
    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        
        try:
            if self.provider == 'chromadb':
                return self._search_chromadb(query, n_results)
            elif self.provider == 'faiss':
                return self._search_faiss(query, n_results)
            return []
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []
    
    def _search_chromadb(self, query: str, n_results: int) -> List[Dict[str, Any]]:
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        search_results = []
        for i in range(len(results['documents'][0])):
            search_results.append({
                'document': results['documents'][0][i],
                'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                'distance': results['distances'][0][i] if results['distances'] else 0,
                'id': results['ids'][0][i]
            })
        
        return search_results
    
    def _search_faiss(self, query: str, n_results: int) -> List[Dict[str, Any]]:
        import numpy as np
        
        query_embedding = self.embeddings.encode([query])[0]
        
        k = min(n_results, self.index.ntotal)
        if k == 0:
            return []
        
        distances, indices = self.index.search(
            np.array([query_embedding]).astype('float32'),
            k
        )
        
        search_results = []
        for i, idx in enumerate(indices[0]):
            if idx >= 0 and idx < len(self.documents):
                search_results.append({
                    'document': self.documents[idx],
                    'metadata': self.metadata[idx],
                    'distance': float(distances[0][i]),
                    'id': idx
                })
        
        return search_results
    
    def _save_faiss(self):
        import faiss
        
        os.makedirs(self.db_path, exist_ok=True)
        
        index_path = os.path.join(self.db_path, 'faiss.index')
        faiss.write_index(self.index, index_path)
        
        meta_path = os.path.join(self.db_path, 'metadata.json')
        with open(meta_path, 'w') as f:
            json.dump({
                'documents': self.documents,
                'metadata': self.metadata
            }, f, indent=2)
    
    def add_documents_bulk(self, documents: List[str], metadatas: List[Dict[str, Any]] = None) -> int:
        if not self.enabled:
            return 0
        
        count = 0
        for i, doc in enumerate(documents):
            meta = metadatas[i] if metadatas and i < len(metadatas) else None
            if self.add_document(doc, meta):
                count += 1
        
        return count
    
    def delete_collection(self) -> bool:
        if not self.enabled:
            return False
        
        try:
            if self.provider == 'chromadb':
                self.client.delete_collection(self.collection_name)
                self.collection = self.client.create_collection(self.collection_name)
                return True
            elif self.provider == 'faiss':
                import faiss
                embedding_dim = self.embeddings.get_sentence_embedding_dimension()
                self.index = faiss.IndexFlatL2(embedding_dim)
                self.documents = []
                self.metadata = []
                self._save_faiss()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        if not self.enabled:
            return {'enabled': False}
        
        try:
            if self.provider == 'chromadb':
                count = self.collection.count()
                return {
                    'enabled': True,
                    'provider': 'chromadb',
                    'collection': self.collection_name,
                    'document_count': count
                }
            elif self.provider == 'faiss':
                return {
                    'enabled': True,
                    'provider': 'faiss',
                    'document_count': self.index.ntotal,
                    'embedding_model': self.embedding_model
                }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
        
        return {'enabled': False}
