### knowledge_base:
**WEBSITE CRAWLER AND KNOWLEDGE RETRIEVAL** - Crawl websites and query stored knowledge.
Use this tool to build a knowledge base from websites and search it for information.

**Actions:**
- `crawl` - Scrape a website and add to knowledge base
- `search` / `query` - Search knowledge base for information
- `list` - List all crawled sources
- `get` - Get full content from a source
- `delete` - Remove a source
- `stats` - Show knowledge base statistics
- `refresh` - Re-crawl a source

---

### Crawl a website:
~~~json
{
    "thoughts": ["User wants to add this documentation to the knowledge base"],
    "headline": "Crawling website for knowledge base",
    "tool_name": "knowledge_base",
    "tool_args": {
        "action": "crawl",
        "url": "https://docs.example.com",
        "deep": false
    }
}
~~~

### Search knowledge base:
~~~json
{
    "thoughts": ["User is asking about something that might be in our knowledge base"],
    "headline": "Searching knowledge base",
    "tool_name": "knowledge_base",
    "tool_args": {
        "action": "search",
        "query": "how to integrate payments"
    }
}
~~~

### List all sources:
~~~json
{
    "thoughts": ["Checking what sources are in the knowledge base"],
    "headline": "Listing knowledge base sources",
    "tool_name": "knowledge_base",
    "tool_args": {
        "action": "list"
    }
}
~~~

### Get full content:
~~~json
{
    "thoughts": ["Need to read the full content from this source"],
    "headline": "Getting full source content",
    "tool_name": "knowledge_base",
    "tool_args": {
        "action": "get",
        "source_id": "abc123"
    }
}
~~~

### Show statistics:
~~~json
{
    "thoughts": ["Checking knowledge base statistics"],
    "headline": "Getting KB stats",
    "tool_name": "knowledge_base",
    "tool_args": {
        "action": "stats"
    }
}
~~~

---

**Notes:**
- Best for documentation sites and server-rendered pages
- JavaScript-heavy sites may have limited content
- Use `deep=true` for recursive crawling (follows links)
