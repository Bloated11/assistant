import logging
from typing import List, Dict, Any
from .search_engine import SearchEngine

logger = logging.getLogger(__name__)

class WebManager:
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get('enabled', True)
        
        if self.enabled:
            self.search_engine = SearchEngine(config)
        
        logger.info(f"WebManager initialized (enabled: {self.enabled})")
    
    def search(self, query: str, engine: str = None) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        
        return self.search_engine.search(query, engine)
    
    def get_quick_answer(self, query: str) -> str:
        if not self.enabled:
            return ""
        
        return self.search_engine.quick_answer(query)
    
    def fetch_content(self, url: str) -> str:
        if not self.enabled:
            return ""
        
        return self.search_engine.get_page_content(url)
    
    def summarize_search_results(self, results: List[Dict[str, Any]]) -> str:
        if not results:
            return "No results found."
        
        summary = f"Found {len(results)} results:\n\n"
        for i, result in enumerate(results, 1):
            summary += f"{i}. {result['title']}\n"
            summary += f"   {result['snippet'][:150]}...\n\n"
        
        return summary
