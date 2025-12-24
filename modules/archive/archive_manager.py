import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict
import uuid

logger = logging.getLogger(__name__)

class ArchiveManager:
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.storage_path = config.get('storage_path', 'data/archive.json')
        
        self.documents = {}
        self.references = {}
        self.folders = {}
        self.tags = set()
        
        if self.enabled:
            self._load_data()
        
        logger.info("ArchiveManager initialized")
    
    def _load_data(self):
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.documents = data.get('documents', {})
                    self.references = data.get('references', {})
                    self.folders = data.get('folders', {})
                    self.tags = set(data.get('tags', []))
                logger.info(f"Loaded {len(self.documents)} archived documents")
        except Exception as e:
            logger.error(f"Error loading archive data: {e}")
    
    def _save_data(self):
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump({
                    'documents': self.documents,
                    'references': self.references,
                    'folders': self.folders,
                    'tags': list(self.tags),
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving archive data: {e}")
    
    def add_document(self, title: str, content: str = "", doc_type: str = None,
                    file_path: str = None, url: str = None, author: str = None,
                    date: str = None, folder_id: str = None, tags: List[str] = None,
                    notes: str = "", important: bool = False) -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            doc_id = str(uuid.uuid4())[:8]
            
            doc_tags = tags or []
            self.tags.update(doc_tags)
            
            self.documents[doc_id] = {
                'id': doc_id,
                'title': title,
                'content': content,
                'type': doc_type,
                'file_path': file_path,
                'url': url,
                'author': author,
                'date': date,
                'folder_id': folder_id,
                'tags': doc_tags,
                'notes': notes,
                'important': important,
                'archived_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'access_count': 0,
                'last_accessed': None
            }
            
            self._save_data()
            logger.info(f"Added document to archive: {title}")
            return self.documents[doc_id].copy()
            
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return None
    
    def add_reference(self, title: str, ref_type: str, content: str = "",
                     url: str = None, author: str = None, publication: str = None,
                     year: int = None, tags: List[str] = None) -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            ref_id = str(uuid.uuid4())[:8]
            
            ref_tags = tags or []
            self.tags.update(ref_tags)
            
            self.references[ref_id] = {
                'id': ref_id,
                'title': title,
                'type': ref_type,
                'content': content,
                'url': url,
                'author': author,
                'publication': publication,
                'year': year,
                'tags': ref_tags,
                'citation': self._generate_citation(title, author, publication, year),
                'added_at': datetime.now().isoformat(),
                'access_count': 0
            }
            
            self._save_data()
            logger.info(f"Added reference: {title}")
            return ref_id
            
        except Exception as e:
            logger.error(f"Error adding reference: {e}")
            return None
    
    def _generate_citation(self, title: str, author: str = None, 
                          publication: str = None, year: int = None) -> str:
        parts = []
        if author:
            parts.append(author)
        if year:
            parts.append(f"({year})")
        parts.append(f'"{title}"')
        if publication:
            parts.append(f"In {publication}")
        
        return ". ".join(parts) + "."
    
    def create_folder(self, name: str, description: str = "", parent_id: str = None) -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            folder_id = str(uuid.uuid4())[:8]
            
            self.folders[folder_id] = {
                'id': folder_id,
                'name': name,
                'description': description,
                'parent_id': parent_id,
                'created_at': datetime.now().isoformat()
            }
            
            self._save_data()
            logger.info(f"Created folder: {name}")
            return folder_id
            
        except Exception as e:
            logger.error(f"Error creating folder: {e}")
            return None
    
    def update_document(self, doc_id: str, **updates) -> bool:
        if not self.enabled or doc_id not in self.documents:
            return False
        
        try:
            for key, value in updates.items():
                if key in self.documents[doc_id]:
                    self.documents[doc_id][key] = value
            
            if 'tags' in updates:
                self.tags.update(updates['tags'])
            
            self.documents[doc_id]['updated_at'] = datetime.now().isoformat()
            self._save_data()
            logger.info(f"Updated document: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            return False
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        doc = self.documents.get(doc_id)
        if doc:
            doc['access_count'] += 1
            doc['last_accessed'] = datetime.now().isoformat()
            self._save_data()
        return doc
    
    def get_reference(self, ref_id: str) -> Optional[Dict[str, Any]]:
        ref = self.references.get(ref_id)
        if ref:
            ref['access_count'] += 1
            self._save_data()
        return ref
    
    def list_documents(self, doc_type: str = None, folder_id: str = None,
                      important: bool = None) -> List[Dict[str, Any]]:
        docs = list(self.documents.values())
        
        if doc_type:
            docs = [d for d in docs if d.get('type') == doc_type]
        if folder_id:
            docs = [d for d in docs if d.get('folder_id') == folder_id]
        if important is not None:
            docs = [d for d in docs if d.get('important') == important]
        
        return sorted(docs, key=lambda x: x.get('archived_at', ''), reverse=True)
    
    def list_references(self, ref_type: str = None) -> List[Dict[str, Any]]:
        refs = list(self.references.values())
        
        if ref_type:
            refs = [r for r in refs if r.get('type') == ref_type]
        
        return sorted(refs, key=lambda x: x.get('added_at', ''), reverse=True)
    
    def search_documents(self, query: str) -> List[Dict[str, Any]]:
        query_lower = query.lower()
        results = []
        
        for doc in self.documents.values():
            if (query_lower in doc['title'].lower() or
                query_lower in doc.get('content', '').lower() or
                query_lower in doc.get('author', '').lower() or
                query_lower in doc.get('notes', '').lower() or
                query_lower in ' '.join(doc.get('tags', [])).lower()):
                results.append(doc)
        
        return results
    
    def search_references(self, query: str) -> List[Dict[str, Any]]:
        query_lower = query.lower()
        results = []
        
        for ref in self.references.values():
            if (query_lower in ref['title'].lower() or
                query_lower in ref.get('author', '').lower() or
                query_lower in ref.get('content', '').lower() or
                query_lower in ' '.join(ref.get('tags', [])).lower()):
                results.append(ref)
        
        return results
    
    def get_documents_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        return [d for d in self.documents.values() if tag in d.get('tags', [])]
    
    def get_references_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        return [r for r in self.references.values() if tag in r.get('tags', [])]
    
    def get_important_documents(self) -> List[Dict[str, Any]]:
        return [d for d in self.documents.values() if d.get('important', False)]
    
    def get_folder_contents(self, folder_id: str) -> Dict[str, Any]:
        if folder_id not in self.folders:
            return None
        
        folder = self.folders[folder_id].copy()
        folder['documents'] = [d for d in self.documents.values() if d.get('folder_id') == folder_id]
        folder['subfolders'] = [f for f in self.folders.values() if f.get('parent_id') == folder_id]
        
        return folder
    
    def get_stats(self) -> Dict[str, Any]:
        total_documents = len(self.documents)
        total_references = len(self.references)
        total_folders = len(self.folders)
        total_tags = len(self.tags)
        
        important_docs = sum(1 for d in self.documents.values() if d.get('important', False))
        
        by_doc_type = defaultdict(int)
        by_ref_type = defaultdict(int)
        
        for doc in self.documents.values():
            if doc.get('type'):
                by_doc_type[doc['type']] += 1
        
        for ref in self.references.values():
            if ref.get('type'):
                by_ref_type[ref['type']] += 1
        
        most_accessed_docs = sorted(self.documents.values(), 
                                    key=lambda x: x.get('access_count', 0), 
                                    reverse=True)[:5]
        
        return {
            'total_documents': total_documents,
            'total_references': total_references,
            'total_folders': total_folders,
            'total_tags': total_tags,
            'important_documents': important_docs,
            'by_document_type': dict(by_doc_type),
            'by_reference_type': dict(by_ref_type),
            'most_accessed': [{'id': d['id'], 'title': d['title'], 'accesses': d['access_count']} 
                             for d in most_accessed_docs]
        }
    def get_all_documents(self):
        return self.list_documents()

    
    
    def delete_document(self, doc_id: str) -> bool:
        if not self.enabled or doc_id not in self.documents:
            return False
        del self.documents[doc_id]
        self._save_data()
        return True
