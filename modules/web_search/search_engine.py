import logging
import os
from typing import List, Dict, Any

try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except (ImportError, ValueError) as e:
    DDGS_AVAILABLE = False
    if isinstance(e, ValueError):
        logging.warning("duckduckgo_search incompatible with uvloop - search disabled")
    else:
        logging.warning("duckduckgo_search module not available")

try:
    import wikipediaapi
    WIKI_AVAILABLE = True
except ImportError:
    WIKI_AVAILABLE = False
    logging.warning("wikipediaapi module not available")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logging.warning("requests module not available")

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    logging.warning("beautifulsoup4 module not available")

logger = logging.getLogger(__name__)

class SearchEngine:
    def __init__(self, config: dict):
        self.config = config
        self.engines = config.get('engines', ['duckduckgo'])
        self.max_results = config.get('max_results', 5)
        self.wiki = wikipediaapi.Wikipedia('Phenom/1.0', 'en') if WIKI_AVAILABLE else None
        
        # Disable SSL warnings for systems with self-signed certificates
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        if not (DDGS_AVAILABLE or WIKI_AVAILABLE):
            logger.warning("No search engines available")
        logger.info(f"SearchEngine initialized with {self.engines}")
    
    def search(self, query: str, engine: str = None) -> List[Dict[str, Any]]:
        if not engine:
            engine = self.engines[0] if self.engines else 'bing'
        
        try:
            if engine == 'bing':
                return self._search_bing(query)
            elif engine == 'duckduckgo':
                return self._search_duckduckgo(query)
            elif engine == 'wikipedia':
                return self._search_wikipedia(query)
            else:
                return self._search_bing(query)
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def _search_bing(self, query: str) -> List[Dict[str, Any]]:
        """Search using Bing Web Search API"""
        if not REQUESTS_AVAILABLE:
            logger.warning("Requests library not available for Bing search")
            return []
        
        api_key = os.getenv('BING_SEARCH_API_KEY')
        if not api_key:
            logger.warning("BING_SEARCH_API_KEY not found in environment")
            return []
        
        try:
            endpoint = "https://api.bing.microsoft.com/v7.0/search"
            headers = {'Ocp-Apim-Subscription-Key': api_key}
            params = {
                'q': query,
                'count': self.max_results,
                'textDecorations': True,
                'textFormat': 'HTML'
            }
            
            response = requests.get(endpoint, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            search_results = response.json()
            results = []
            
            if 'webPages' in search_results and 'value' in search_results['webPages']:
                for item in search_results['webPages']['value']:
                    results.append({
                        'title': item.get('name', ''),
                        'url': item.get('url', ''),
                        'snippet': item.get('snippet', ''),
                        'source': 'bing'
                    })
            
            logger.info(f"Bing search returned {len(results)} results")
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Bing search error: {e}")
            return []
        except Exception as e:
            logger.error(f"Bing search unexpected error: {e}")
            return []
    
    def _search_duckduckgo(self, query: str) -> List[Dict[str, Any]]:
        if not DDGS_AVAILABLE:
            logger.warning("DuckDuckGo search not available")
            return []
            
        try:
            results = []
            import ssl
            import time
            
            # Disable SSL verification for systems with self-signed certificates
            old_ssl_context = ssl._create_default_https_context
            ssl._create_default_https_context = ssl._create_unverified_context
            
            try:
                # Retry logic for rate limiting
                max_retries = 2
                for attempt in range(max_retries):
                    try:
                        with DDGS(timeout=20) as ddgs:
                            search_results = ddgs.text(query, max_results=self.max_results)
                            for r in search_results:
                                results.append({
                                    'title': r.get('title', ''),
                                    'url': r.get('href', ''),
                                    'snippet': r.get('body', ''),
                                    'source': 'duckduckgo'
                                })
                        break  # Success, exit retry loop
                    except Exception as retry_error:
                        if 'Ratelimit' in str(retry_error) and attempt < max_retries - 1:
                            logger.warning(f"Rate limited, retrying in 2 seconds... (attempt {attempt + 1})")
                            time.sleep(2)
                        else:
                            raise  # Re-raise if not rate limit or last attempt
            finally:
                # Restore original SSL context
                ssl._create_default_https_context = old_ssl_context
            
            logger.info(f"DuckDuckGo search returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []
    
    def _search_wikipedia(self, query: str) -> List[Dict[str, Any]]:
        try:
            page = self.wiki.page(query)
            
            if page.exists():
                return [{
                    'title': page.title,
                    'url': page.fullurl,
                    'snippet': page.summary[:500] + '...' if len(page.summary) > 500 else page.summary,
                    'source': 'wikipedia'
                }]
            
            return []
        except Exception as e:
            logger.error(f"Wikipedia search error: {e}")
            return []
    
    def get_page_content(self, url: str) -> str:
        try:
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Phenom/1.0'
            })
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for script in soup(['script', 'style']):
                script.decompose()
            
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split('  '))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text[:5000]
        except Exception as e:
            logger.error(f"Error fetching page content: {e}")
            return ""
    
    def quick_answer(self, query: str) -> str:
        if not DDGS_AVAILABLE:
            return ""
            
        try:
            import ssl
            import warnings
            
            old_ssl_context = ssl._create_default_https_context
            ssl._create_default_https_context = ssl._create_unverified_context
            
            warnings.filterwarnings('ignore', category=RuntimeWarning, message='.*coroutine.*')
            
            try:
                with DDGS(timeout=10) as ddgs:
                    answer = ddgs.answers(query)
                    answer_list = list(answer) if answer else []
                    if answer_list:
                        return answer_list[0].get('text', '')
            finally:
                ssl._create_default_https_context = old_ssl_context
            
            return ""
        except Exception as e:
            logger.debug(f"Quick answer unavailable: {e}")
            return ""
