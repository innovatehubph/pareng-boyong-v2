"""
Knowledge Base Tool for Pareng Boyong
AI-powered website crawler and knowledge retrieval system
Uses n8n workflow for crawling and local storage for knowledge management
"""

import os
import json
import glob
import hashlib
import requests
from datetime import datetime
from typing import Optional, List, Dict, Any
from python.helpers.tool import Tool, Response


class KnowledgeBase(Tool):
    """
    AI Agent Knowledge Base - Crawl websites and query stored knowledge.
    
    Actions:
    - crawl: Crawl a website and add to knowledge base
    - search: Search knowledge base for relevant information
    - list: List all knowledge base sources
    - get: Get full content from a specific source
    - delete: Remove a source from knowledge base
    - stats: Show knowledge base statistics
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # n8n configuration
        self.n8n_base_url = os.environ.get("N8N_BASE_URL", "http://localhost:5678")
        self.n8n_api_key = os.environ.get("N8N_API_KEY", "")
        self.n8n_webhook_url = os.environ.get(
            "N8N_CRAWLER_WEBHOOK", 
            f"{self.n8n_base_url}/webhook/crawl-kb"
        )
        
        # Knowledge base storage
        self.kb_dir = os.environ.get("KNOWLEDGE_BASE_DIR", "/app/knowledge/scraped")
        self.index_file = os.path.join(self.kb_dir, "index.json")
        
        # Ensure directory exists
        os.makedirs(self.kb_dir, exist_ok=True)
        
        # Load or create index
        self.index = self._load_index()

    def _load_index(self) -> Dict[str, Any]:
        """Load knowledge base index."""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, "r") as f:
                    return json.load(f)
            except:
                pass
        return {"sources": {}, "updated": None}

    def _save_index(self):
        """Save knowledge base index."""
        self.index["updated"] = datetime.now().isoformat()
        with open(self.index_file, "w") as f:
            json.dump(self.index, f, indent=2)

    def _url_to_id(self, url: str) -> str:
        """Convert URL to unique ID."""
        return hashlib.md5(url.encode()).hexdigest()[:12]

    async def execute(self, **kwargs) -> Response:
        action = self.args.get("action", "search").lower()
        
        actions = {
            "crawl": self._crawl,
            "search": self._search,
            "query": self._search,  # Alias
            "list": self._list_sources,
            "get": self._get_source,
            "delete": self._delete_source,
            "stats": self._get_stats,
            "refresh": self._refresh_source,
        }
        
        if action not in actions:
            return Response(
                message=f"Unknown action: {action}\n\nAvailable actions:\n"
                        f"- crawl: Crawl a website (url, deep=true/false)\n"
                        f"- search: Search knowledge base (query)\n"
                        f"- list: List all sources\n"
                        f"- get: Get content from source (source_id or url)\n"
                        f"- delete: Remove source (source_id or url)\n"
                        f"- stats: Show statistics\n"
                        f"- refresh: Re-crawl a source (source_id or url)",
                break_loop=False
            )
        
        try:
            return await actions[action]()
        except Exception as e:
            return Response(
                message=f"Knowledge Base Error: {str(e)}",
                break_loop=False
            )

    async def _crawl(self) -> Response:
        """Crawl a website and add to knowledge base."""
        url = self.args.get("url", "")
        deep = self.args.get("deep", False)
        
        if not url:
            return Response(
                message="Error: 'url' is required for crawling.\n\n"
                        "Example: knowledge_base action=crawl url=https://example.com deep=true",
                break_loop=False
            )
        
        # Normalize URL
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        self.log.update(progress=f"🕷️ Starting crawl of {url}...")
        
        # Try n8n webhook first
        try:
            response = requests.post(
                self.n8n_webhook_url,
                json={"url": url, "deep": deep},
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                # Store the crawled data
                source_id = self._url_to_id(url)
                
                self.index["sources"][source_id] = {
                    "url": url,
                    "title": result.get("title", "Unknown"),
                    "pageCount": result.get("pageCount", 1),
                    "crawledAt": datetime.now().isoformat(),
                    "file": result.get("savedTo", f"{source_id}.json")
                }
                self._save_index()
                
                return Response(
                    message=f"✅ **Website Crawled Successfully!**\n\n"
                            f"- **URL:** {url}\n"
                            f"- **Title:** {result.get('title', 'Unknown')}\n"
                            f"- **Pages:** {result.get('pageCount', 1)}\n"
                            f"- **Source ID:** `{source_id}`\n\n"
                            f"Use `knowledge_base action=search query=\"your question\"` to query this knowledge.",
                    break_loop=False
                )
        except requests.exceptions.RequestException as e:
            self.log.update(progress=f"n8n webhook failed, using fallback crawler...")
        
        # Fallback: Direct crawling
        return await self._direct_crawl(url, deep)

    async def _direct_crawl(self, url: str, deep: bool = False) -> Response:
        """Fallback direct crawling without n8n."""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            # Try to install
            import subprocess
            subprocess.run(["pip", "install", "beautifulsoup4"], capture_output=True)
            from bs4 import BeautifulSoup
        
        response = requests.get(url, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (compatible; ParengBoyongBot/1.0)"
        })
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove unwanted elements
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        
        title = soup.title.string if soup.title else "Untitled"
        
        # Get main content
        content = ""
        for selector in ["main", "article", ".content", "#content"]:
            main = soup.select_one(selector)
            if main:
                content = main.get_text(separator=" ", strip=True)
                break
        
        if not content:
            content = soup.body.get_text(separator=" ", strip=True) if soup.body else ""
        
        # Clean content
        content = " ".join(content.split())[:50000]
        
        # Save to knowledge base
        source_id = self._url_to_id(url)
        kb_data = {
            "source": url,
            "title": title,
            "crawledAt": datetime.now().isoformat(),
            "pageCount": 1,
            "pages": [{
                "url": url,
                "title": title,
                "content": content,
                "wordCount": len(content.split())
            }]
        }
        
        kb_file = os.path.join(self.kb_dir, f"{source_id}.json")
        with open(kb_file, "w") as f:
            json.dump(kb_data, f, indent=2)
        
        self.index["sources"][source_id] = {
            "url": url,
            "title": title,
            "pageCount": 1,
            "crawledAt": datetime.now().isoformat(),
            "file": f"{source_id}.json"
        }
        self._save_index()
        
        return Response(
            message=f"✅ **Website Crawled (Direct)!**\n\n"
                    f"- **URL:** {url}\n"
                    f"- **Title:** {title}\n"
                    f"- **Words:** {len(content.split()):,}\n"
                    f"- **Source ID:** `{source_id}`",
            break_loop=False
        )

    async def _search(self) -> Response:
        """Search the knowledge base."""
        query = self.args.get("query", self.args.get("q", ""))
        limit = int(self.args.get("limit", 5))
        source_id = self.args.get("source_id", self.args.get("source", ""))
        
        if not query:
            return Response(
                message="Error: 'query' is required for searching.\n\n"
                        "Example: knowledge_base action=search query=\"How to configure X\"",
                break_loop=False
            )
        
        results = []
        query_terms = query.lower().split()
        
        # Determine which files to search
        if source_id:
            files = [os.path.join(self.kb_dir, f"{source_id}.json")]
        else:
            files = glob.glob(os.path.join(self.kb_dir, "*.json"))
            files = [f for f in files if not f.endswith("index.json")]
        
        for kb_file in files:
            if not os.path.exists(kb_file):
                continue
                
            try:
                with open(kb_file, "r") as f:
                    kb_data = json.load(f)
                
                for page in kb_data.get("pages", []):
                    content = page.get("content", "").lower()
                    title = page.get("title", "").lower()
                    
                    # Simple relevance scoring
                    score = 0
                    for term in query_terms:
                        score += content.count(term) + (title.count(term) * 3)
                    
                    if score > 0:
                        # Extract relevant snippet
                        snippet = self._extract_snippet(page.get("content", ""), query_terms)
                        results.append({
                            "source": kb_data.get("source", "unknown"),
                            "title": page.get("title", "Untitled"),
                            "url": page.get("url", ""),
                            "snippet": snippet,
                            "score": score
                        })
            except Exception as e:
                continue
        
        # Sort by relevance
        results.sort(key=lambda x: x["score"], reverse=True)
        results = results[:limit]
        
        if not results:
            return Response(
                message=f"No results found for: \"{query}\"\n\n"
                        f"Try different keywords or crawl more sources with:\n"
                        f"`knowledge_base action=crawl url=https://example.com`",
                break_loop=False
            )
        
        # Format results
        output = f"🔍 **Search Results for:** \"{query}\"\n\n"
        for i, r in enumerate(results, 1):
            output += f"**{i}. {r['title']}**\n"
            output += f"   Source: {r['url']}\n"
            output += f"   > {r['snippet']}\n\n"
        
        output += f"*Found {len(results)} relevant result(s)*"
        
        return Response(message=output, break_loop=False)

    def _extract_snippet(self, content: str, query_terms: List[str], max_len: int = 300) -> str:
        """Extract relevant snippet around query terms."""
        content_lower = content.lower()
        
        # Find best position
        best_pos = 0
        best_score = 0
        
        for i in range(0, len(content) - 100, 50):
            window = content_lower[i:i+300]
            score = sum(window.count(term) for term in query_terms)
            if score > best_score:
                best_score = score
                best_pos = i
        
        # Extract snippet
        start = max(0, best_pos - 50)
        snippet = content[start:start + max_len]
        
        # Clean up
        if start > 0:
            snippet = "..." + snippet[snippet.find(" ")+1:]
        if start + max_len < len(content):
            snippet = snippet[:snippet.rfind(" ")] + "..."
        
        return snippet

    async def _list_sources(self) -> Response:
        """List all knowledge base sources."""
        if not self.index["sources"]:
            return Response(
                message="📚 **Knowledge Base is empty**\n\n"
                        "Add sources with:\n"
                        "`knowledge_base action=crawl url=https://example.com`",
                break_loop=False
            )
        
        output = "📚 **Knowledge Base Sources:**\n\n"
        
        for sid, info in self.index["sources"].items():
            output += f"- **{info.get('title', 'Untitled')}**\n"
            output += f"  ID: `{sid}` | Pages: {info.get('pageCount', 1)}\n"
            output += f"  URL: {info.get('url', 'N/A')}\n"
            output += f"  Crawled: {info.get('crawledAt', 'N/A')[:10]}\n\n"
        
        output += f"*Total: {len(self.index['sources'])} source(s)*"
        
        return Response(message=output, break_loop=False)

    async def _get_source(self) -> Response:
        """Get full content from a specific source."""
        source_id = self.args.get("source_id", self.args.get("id", self.args.get("url", "")))
        
        if not source_id:
            return Response(
                message="Error: 'source_id' or 'url' is required.\n\n"
                        "Use `knowledge_base action=list` to see available sources.",
                break_loop=False
            )
        
        # Handle URL input
        if source_id.startswith(("http://", "https://")):
            source_id = self._url_to_id(source_id)
        
        kb_file = os.path.join(self.kb_dir, f"{source_id}.json")
        
        if not os.path.exists(kb_file):
            return Response(
                message=f"Source not found: {source_id}\n\n"
                        f"Use `knowledge_base action=list` to see available sources.",
                break_loop=False
            )
        
        with open(kb_file, "r") as f:
            kb_data = json.load(f)
        
        # Format output
        output = f"📄 **{kb_data.get('title', 'Untitled')}**\n\n"
        output += f"Source: {kb_data.get('source', 'N/A')}\n"
        output += f"Crawled: {kb_data.get('crawledAt', 'N/A')}\n"
        output += f"Pages: {kb_data.get('pageCount', 1)}\n\n"
        output += "---\n\n"
        
        for page in kb_data.get("pages", [])[:3]:  # Limit to first 3 pages
            output += f"### {page.get('title', 'Page')}\n"
            content = page.get("content", "")[:2000]
            if len(page.get("content", "")) > 2000:
                content += "...\n\n*(Content truncated)*"
            output += f"{content}\n\n"
        
        return Response(message=output, break_loop=False)

    async def _delete_source(self) -> Response:
        """Delete a source from knowledge base."""
        source_id = self.args.get("source_id", self.args.get("id", self.args.get("url", "")))
        
        if not source_id:
            return Response(
                message="Error: 'source_id' or 'url' is required.",
                break_loop=False
            )
        
        # Handle URL input
        if source_id.startswith(("http://", "https://")):
            source_id = self._url_to_id(source_id)
        
        if source_id not in self.index["sources"]:
            return Response(
                message=f"Source not found: {source_id}",
                break_loop=False
            )
        
        # Remove file
        kb_file = os.path.join(self.kb_dir, f"{source_id}.json")
        if os.path.exists(kb_file):
            os.remove(kb_file)
        
        # Remove from index
        title = self.index["sources"][source_id].get("title", "Unknown")
        del self.index["sources"][source_id]
        self._save_index()
        
        return Response(
            message=f"🗑️ Deleted source: **{title}** (`{source_id}`)",
            break_loop=False
        )

    async def _get_stats(self) -> Response:
        """Get knowledge base statistics."""
        total_sources = len(self.index["sources"])
        total_pages = sum(s.get("pageCount", 1) for s in self.index["sources"].values())
        total_words = 0
        
        for sid in self.index["sources"]:
            kb_file = os.path.join(self.kb_dir, f"{sid}.json")
            if os.path.exists(kb_file):
                try:
                    with open(kb_file, "r") as f:
                        kb_data = json.load(f)
                    for page in kb_data.get("pages", []):
                        total_words += page.get("wordCount", 0)
                except:
                    pass
        
        output = "📊 **Knowledge Base Statistics**\n\n"
        output += f"- **Sources:** {total_sources}\n"
        output += f"- **Total Pages:** {total_pages}\n"
        output += f"- **Total Words:** {total_words:,}\n"
        output += f"- **Last Updated:** {self.index.get('updated', 'Never')[:19] if self.index.get('updated') else 'Never'}\n"
        output += f"- **Storage:** {self.kb_dir}\n"
        
        return Response(message=output, break_loop=False)

    async def _refresh_source(self) -> Response:
        """Re-crawl a source."""
        source_id = self.args.get("source_id", self.args.get("id", self.args.get("url", "")))
        
        if not source_id:
            return Response(message="Error: 'source_id' or 'url' is required.", break_loop=False)
        
        # Handle URL input
        url = source_id
        if not url.startswith(("http://", "https://")):
            if source_id in self.index["sources"]:
                url = self.index["sources"][source_id]["url"]
            else:
                return Response(message=f"Source not found: {source_id}", break_loop=False)
        
        self.args["url"] = url
        self.args["deep"] = self.args.get("deep", False)
        return await self._crawl()
