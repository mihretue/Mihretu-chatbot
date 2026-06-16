import logging
import asyncio
from typing import Dict, Any

from app.core.config import settings

logger = logging.getLogger(__name__)


class GoogleTrendsMCPTool:
    """Google Trends via SerpAPI with graceful fallback when unavailable."""

    def _get_client(self):
        """Return SerpAPI GoogleSearch class, or None if key not configured."""
        if not settings.serpapi_key:
            return None
        try:
            from serpapi import GoogleSearch
            return GoogleSearch
        except ImportError:
            logger.error("google-search-results package not installed")
            return None

    def _fetch_trending(self, geo: str) -> Dict[str, Any]:
        """Synchronous SerpAPI call for trending searches."""
        GoogleSearch = self._get_client()
        if not GoogleSearch:
            return {"success": False, "error": "SerpAPI key not configured"}

        params = {
            "engine": "google_trends_trending_now",
            "geo": geo,
            "api_key": settings.serpapi_key,
        }
        result = GoogleSearch(params).get_dict()

        if "error" in result:
            return {"success": False, "error": result["error"]}

        trending = result.get("trending_searches", [])
        trends = [
            {"keyword": item.get("query", ""), "rank": idx + 1}
            for idx, item in enumerate(trending)
        ]
        return {"success": True, "geo": geo, "trends": trends}

    def _fetch_related_queries(self, keyword: str, max_results: int) -> Dict[str, Any]:
        """Synchronous SerpAPI call for related queries."""
        GoogleSearch = self._get_client()
        if not GoogleSearch:
            return {"success": False, "keyword": keyword, "error": "SerpAPI key not configured"}

        params = {
            "engine": "google_trends",
            "q": keyword,
            "data_type": "RELATED_QUERIES",
            "api_key": settings.serpapi_key,
        }
        result = GoogleSearch(params).get_dict()

        if "error" in result:
            return {"success": False, "keyword": keyword, "error": result["error"]}

        top = result.get("related_queries", {}).get("top", [])
        articles = [
            {
                "title": f"Trending: {item.get('query', '')}",
                "url": f"https://trends.google.com/trends/explore?q={item.get('query', '')}",
                "summary": f"Interest: {item.get('value', 'N/A')}",
            }
            for item in top[:max_results]
        ]
        return {"success": True, "keyword": keyword, "articles": articles}

    async def get_trending_terms(self, geo: str = "US") -> Dict[str, Any]:
        """Get trending terms — SerpAPI with graceful fallback."""
        if not settings.serpapi_key:
            logger.warning("SERPAPI_KEY not set — Google Trends unavailable")
            return {
                "success": False,
                "error": "Google Trends is not configured (missing SERPAPI_KEY). Falling back to LLM knowledge.",
                "trends": [],
            }
        try:
            logger.info(f"Fetching trending terms via SerpAPI for geo={geo}")
            result = await asyncio.to_thread(self._fetch_trending, geo)
            if result["success"]:
                logger.info(f"Fetched {len(result['trends'])} trends")
            else:
                logger.warning(f"SerpAPI trends failed: {result.get('error')}")
            return result
        except Exception as e:
            logger.error(f"Trends error: {e}")
            return {"success": False, "error": str(e), "trends": []}

    async def get_news_by_keyword(self, keyword: str, max_results: int = 5) -> Dict[str, Any]:
        """Get related queries for a keyword — SerpAPI with graceful fallback."""
        if not settings.serpapi_key:
            logger.warning("SERPAPI_KEY not set — Google Trends unavailable")
            return {
                "success": False,
                "keyword": keyword,
                "error": "Google Trends is not configured (missing SERPAPI_KEY). Falling back to LLM knowledge.",
                "articles": [],
            }
        try:
            logger.info(f"Fetching related queries via SerpAPI for keyword={keyword}")
            result = await asyncio.to_thread(self._fetch_related_queries, keyword, max_results)
            if result["success"]:
                logger.info(f"Fetched {len(result['articles'])} related queries")
            else:
                logger.warning(f"SerpAPI related queries failed: {result.get('error')}")
            return result
        except Exception as e:
            logger.error(f"News error: {e}")
            return {"success": False, "keyword": keyword, "error": str(e), "articles": []}

    def format_trends(self, trends_result: Dict[str, Any]) -> str:
        """Format trending terms for agent consumption."""
        if not trends_result["success"]:
            return f"Google Trends unavailable: {trends_result['error']}"

        formatted = f"Google Trends ({trends_result['geo']}):\n\n"
        for i, trend in enumerate(trends_result["trends"][:10], 1):
            formatted += f"{i}. {trend.get('keyword', '')} (Rank: {trend.get('rank', i)})\n"
        return formatted or "No trends data available."

    def format_news(self, news_result: Dict[str, Any]) -> str:
        """Format related queries for agent consumption."""
        if not news_result["success"]:
            return f"Google Trends unavailable: {news_result['error']}"

        formatted = f"Related searches for '{news_result['keyword']}':\n\n"
        for i, article in enumerate(news_result["articles"][:5], 1):
            formatted += f"{i}. {article.get('title', '')}\n"
            if article.get("summary"):
                formatted += f"   {article['summary']}\n"
            if article.get("url"):
                formatted += f"   URL: {article['url']}\n"
            formatted += "\n"
        return formatted or "No related searches found."

    async def health_check(self) -> bool:
        """Returns True if SerpAPI key is configured, False otherwise."""
        if not settings.serpapi_key:
            logger.warning("Google Trends health check: SERPAPI_KEY not set")
            return False
        return True


# Global instance
google_trends_tool = GoogleTrendsMCPTool()
