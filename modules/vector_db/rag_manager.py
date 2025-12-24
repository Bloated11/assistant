import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class RAGManager:
    def __init__(self, vector_db_manager, ai_manager):
        self.vector_db = vector_db_manager
        self.ai = ai_manager
        self.enabled = vector_db_manager.enabled
        self.min_similarity_threshold = 0.5
        self.max_context_length = 2000
        
        logger.info("RAGManager initialized")
    
    def generate_with_context(self, query: str, n_context: int = 3, force_cloud: bool = False) -> str:
        if not self.enabled or not self.vector_db.enabled:
            return self.ai.generate(query, force_cloud=force_cloud)
        
        try:
            relevant_docs = self.vector_db.search(query, n_results=n_context)
            
            if not relevant_docs:
                return self.ai.generate(query, force_cloud=force_cloud)
            
            context = self._build_context(relevant_docs)
            
            enhanced_prompt = self._create_rag_prompt(query, context)
            
            response = self.ai.generate(enhanced_prompt, force_cloud=force_cloud)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in RAG generation: {e}")
            return self.ai.generate(query, force_cloud=force_cloud)
    
    def _build_context(self, docs: List[Dict[str, Any]]) -> str:
        context_parts = []
        total_length = 0
        
        for doc in docs:
            doc_text = doc['document']
            doc_length = len(doc_text)
            
            if total_length + doc_length > self.max_context_length:
                break
            
            context_parts.append(doc_text)
            total_length += doc_length
        
        return "\n\n".join(context_parts)
    
    def _create_rag_prompt(self, query: str, context: str) -> str:
        prompt = f"""Use the following context to answer the question. If the context doesn't contain relevant information, use your general knowledge.

Context:
{context}

Question: {query}

Answer:"""
        
        return prompt
    
    def chat_with_context(self, messages: List[Dict[str, str]], n_context: int = 3, force_cloud: bool = False) -> str:
        if not self.enabled or not self.vector_db.enabled:
            return self.ai.chat(messages, force_cloud=force_cloud)
        
        try:
            last_user_message = None
            for msg in reversed(messages):
                if msg.get('role') == 'user':
                    last_user_message = msg.get('content', '')
                    break
            
            if not last_user_message:
                return self.ai.chat(messages, force_cloud=force_cloud)
            
            relevant_docs = self.vector_db.search(last_user_message, n_results=n_context)
            
            if not relevant_docs:
                return self.ai.chat(messages, force_cloud=force_cloud)
            
            context = self._build_context(relevant_docs)
            
            enhanced_messages = messages.copy()
            enhanced_messages.insert(0, {
                'role': 'system',
                'content': f"Use this context in your responses:\n\n{context}"
            })
            
            response = self.ai.chat(enhanced_messages, force_cloud=force_cloud)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in RAG chat: {e}")
            return self.ai.chat(messages, force_cloud=force_cloud)
    
    def add_knowledge(self, text: str, metadata: Dict[str, Any] = None) -> bool:
        if not self.enabled:
            return False
        
        return self.vector_db.add_document(text, metadata)
    
    def add_knowledge_bulk(self, texts: List[str], metadatas: List[Dict[str, Any]] = None) -> int:
        if not self.enabled:
            return 0
        
        return self.vector_db.add_documents_bulk(texts, metadatas)
    
    def semantic_search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        
        return self.vector_db.search(query, n_results)
    
    def get_stats(self) -> Dict[str, Any]:
        stats = {
            'enabled': self.enabled,
            'vector_db_stats': self.vector_db.get_stats() if self.enabled else {}
        }
        
        return stats
