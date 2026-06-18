"""
Production Web Search - Tavily + DuckDuckGo + Wikipedia
"""
import asyncio
import httpx
import re
from typing import List, Dict, Optional
from urllib.parse import quote_plus
from loguru import logger
from app.config import settings

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False


class WebSearchService:
    """Production web search - Tavily priority + fallbacks"""
    
    def __init__(self):
        self.timeout = 15
        self.tavily_key = settings.TAVILY_API_KEY
        self.use_tavily = (
            settings.USE_TAVILY 
            and bool(self.tavily_key) 
            and TAVILY_AVAILABLE
        )
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
        }
        
        # Initialize Tavily client
        if self.use_tavily:
            try:
                self.tavily_client = TavilyClient(api_key=self.tavily_key)
                logger.info("🚀 Web Search: TAVILY (AI-Optimized) - PRODUCTION MODE")
            except Exception as e:
                logger.error(f"❌ Tavily init failed: {e}")
                self.use_tavily = False
                logger.info("🐌 Web Search: DuckDuckGo (Fallback Mode)")
        else:
            logger.info("🐌 Web Search: DuckDuckGo (Fallback Mode)")
    
    async def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """Smart search - Tavily first, fallbacks after"""
        logger.info(f"🌐 Searching: '{query[:60]}'")
        
        # PRIORITY 1: Tavily (best for AI)
        if self.use_tavily:
            results = await self._search_tavily(query, max_results)
            if results:
                logger.info(f"✅ Tavily: {len(results)} results")
                return results
        
        # PRIORITY 2: DuckDuckGo
        results = await self._search_ddg_html(query, max_results)
        if results:
            logger.info(f"✅ DuckDuckGo: {len(results)} results")
            return results
        
        # PRIORITY 3: Wikipedia
        results = await self._search_wikipedia(query)
        if results:
            logger.info(f"✅ Wikipedia: {len(results)} results")
            return results
        
        # FALLBACK
        return self._get_fallback(query)
    
    # ═══════════════════════════════════════════
    # 🚀 TAVILY (AI-Optimized Search)
    # ═══════════════════════════════════════════
    
    async def _search_tavily(self, query: str, max_results: int) -> List[Dict]:
        """Tavily Search - Best for AI/RAG"""
        try:
            # Run in thread (Tavily is sync)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.tavily_client.search(
                    query=query,
                    search_depth="advanced",  # 'basic' or 'advanced'
                    max_results=max_results,
                    include_answer=True,  # Get AI-generated summary
                    include_raw_content=False,
                )
            )
            
            results = []
            
            # Add Tavily's AI answer first (if available)
            if response.get("answer"):
                results.append({
                    "title": "AI-Generated Summary",
                    "snippet": response["answer"],
                    "url": "",
                    "source": "Tavily AI",
                })
            
            # Add web results
            for item in response.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("content", ""),
                    "url": item.get("url", ""),
                    "source": "Tavily",
                    "score": item.get("score", 0),
                })
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Tavily search failed: {e}")
            return []
    
    # ═══════════════════════════════════════════
    # 🦆 DUCKDUCKGO (Fallback)
    # ═══════════════════════════════════════════
    
    async def _search_ddg_html(self, query: str, max_results: int) -> List[Dict]:
        """DuckDuckGo HTML scraping"""
        if not BS4_AVAILABLE:
            return []
        
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True
            ) as client:
                response = await client.post(
                    "https://html.duckduckgo.com/html/",
                    data={"q": query},
                    headers=self.headers
                )
                
                if response.status_code != 200:
                    return []
                
                soup = BeautifulSoup(response.text, 'html.parser')
                results = []
                
                for result_div in soup.find_all('div', class_='result')[:max_results]:
                    try:
                        title_elem = result_div.find('a', class_='result__a')
                        snippet_elem = result_div.find('a', class_='result__snippet')
                        
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            url = title_elem.get('href', '')
                            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''
                            
                            if url.startswith('//'):
                                url = 'https:' + url
                            
                            if len(snippet) < 30:
                                continue
                            
                            results.append({
                                "title": title[:150],
                                "snippet": snippet[:800],
                                "url": url,
                                "source": "DuckDuckGo"
                            })
                    except:
                        continue
                
                return results
                
        except Exception as e:
            logger.error(f"❌ DDG failed: {e}")
            return []
    
    # ═══════════════════════════════════════════
    # 📚 WIKIPEDIA
    # ═══════════════════════════════════════════
    
    async def _search_wikipedia(self, query: str) -> List[Dict]:
        """Wikipedia search"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    "https://en.wikipedia.org/w/api.php",
                    params={
                        "action": "query",
                        "format": "json",
                        "list": "search",
                        "srsearch": query,
                        "srlimit": 3,
                    },
                    headers=self.headers
                )
                
                data = response.json()
                results = []
                
                for item in data.get("query", {}).get("search", []):
                    snippet = re.sub(r'<[^>]+>', '', item.get("snippet", ""))
                    title = item.get("title", "")
                    
                    results.append({
                        "title": title,
                        "snippet": snippet,
                        "url": f"https://en.wikipedia.org/wiki/{quote_plus(title)}",
                        "source": "Wikipedia"
                    })
                
                return results
                
        except Exception as e:
            return []
    
    # ═══════════════════════════════════════════
    # 🆘 FALLBACK
    # ═══════════════════════════════════════════
    
    def _get_fallback(self, query: str) -> List[Dict]:
        """When all search fails"""
        return [{
            "title": "Search Notice",
            "snippet": f"Real-time search for '{query}' is currently limited. AI will provide best answer based on general knowledge.",
            "url": f"https://www.google.com/search?q={quote_plus(query)}",
            "source": "Fallback"
        }]


web_search = WebSearchService()