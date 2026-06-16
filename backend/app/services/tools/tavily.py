from tavily import TavilyClient
from app.core.config import settings
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class TavilySearchTool:
    """Wrapper for Tavily web search API with graceful fallback when key is missing."""

    def __init__(self):
        self.client: Optional[TavilyClient] = None
        self._init_client()

    def _init_client(self):
        """Initialize Tavily client only if API key is present."""
        api_key = settings.tavily_api_key
        if not api_key:
            logger.warning("TAVILY_API_KEY not set — web search will be unavailable")
            return
        try:
            self.client = TavilyClient(api_key=api_key)
            logger.info("Tavily client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Tavily client: {e}")

    def _unavailable(self, query: str = "") -> Dict[str, Any]:
        return {
            "success": False,
            "query": query,
            "error": "Web search is not configured (missing or invalid TAVILY_API_KEY). Falling back to LLM knowledge.",
            "results": [],
            "answer": "",
        }

    async def search(
        self,
        query: str,
        max_results: int = 5,
        include_answer: bool = True,
    ) -> Dict[str, Any]:
        if not self.client:
            return self._unavailable(query)

        try:
            logger.info(f"Tavily search: {query}")
            response = self.client.search(
                query=query,
                max_results=max_results,
                include_answer=include_answer,
            )
            logger.info(f"Tavily search completed: {len(response.get('results', []))} results")
            return {
                "success": True,
                "query": query,
                "results": response.get("results", []),
                "answer": response.get("answer", ""),
                "raw_response": response,
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Tavily search error: {error_msg}")
            return {
                "success": False,
                "query": query,
                "error": error_msg,
                "results": [],
                "answer": "",
            }

    async def search_with_context(
        self,
        query: str,
        context: Optional[str] = None,
        max_results: int = 5,
    ) -> Dict[str, Any]:
        full_query = f"{query} {context}" if context else query
        return await self.search(full_query, max_results)

    def format_results(self, search_result: Dict[str, Any]) -> str:
        if not search_result["success"]:
            return f"Web search unavailable: {search_result['error']}"

        formatted = f"Search Results for '{search_result['query']}':\n\n"

        if search_result["answer"]:
            formatted += f"Answer: {search_result['answer']}\n\n"

        if search_result["results"]:
            formatted += "Top Results:\n"
            for i, result in enumerate(search_result["results"], 1):
                formatted += f"\n{i}. {result.get('title', 'No title')}\n"
                formatted += f"   URL: {result.get('url', 'No URL')}\n"
                formatted += f"   {result.get('content', 'No content')}\n"
        else:
            formatted += "No results found."

        return formatted


# Global instance
tavily_tool = TavilySearchTool()
