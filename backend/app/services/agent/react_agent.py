from groq import Groq
import logging
from typing import List, Dict, Any, AsyncGenerator, Optional
import asyncio
import re

from app.core.config import settings
from app.services.tools.tavily import tavily_tool
from app.services.tools.google_trends_mcp import google_trends_tool
from app.services.db.supabase_client import supabase_client

logger = logging.getLogger(__name__)

# --- Intent classification keywords ---

_TREND_KEYWORDS = [
    "trending", "trend", "trendy", "viral", "popular", "top searches",
    "what's hot", "most searched", "hot topics", "buzz", "going viral",
    "people are searching", "top topics", "what people are talking about",
]

_SEARCH_KEYWORDS = [
    "latest", "recent", "news", "current", "today", "this week",
    "breaking", "just happened", "right now", "update", "announced",
    "released", "launched", "new development", "what happened",
]


def _classify_intent(query: str) -> str:
    """
    Route the query to the best tool.
    Returns: 'trends' | 'search' | 'general'
    """
    q = query.lower()
    is_trend = any(k in q for k in _TREND_KEYWORDS)
    is_search = any(k in q for k in _SEARCH_KEYWORDS)

    if is_trend and not is_search:
        return "trends"
    if is_search:
        # search is more general-purpose; wins when both signals present
        return "search"
    return "general"


# --- System prompts per intent ---

_BASE = "You are a helpful AI assistant."

_PROMPTS = {
    "trends": _BASE + """

You have access to Google Trends to find what topics are trending right now.

To use it, respond exactly with:
ACTION: Google_Trends_MCP
INPUT: US

After receiving the tool result, synthesize it into a clear, helpful answer.
If the tool fails or returns no data, answer using your own knowledge and say so.""",

    "search": _BASE + """

You have access to a web search tool for current, real-time information.

To use it, respond exactly with:
ACTION: Tavily_Search
INPUT: <your specific search query here>

After receiving the results, synthesize them into a clear, helpful answer.
If the search fails, answer using your own knowledge and say so.""",

    "general": _BASE + " Answer the user's question directly and helpfully using your knowledge.",
}


class ReActAgent:
    """ReAct agent with intent-based tool routing."""

    def __init__(self):
        self.max_iterations = settings.agent_max_iterations
        self.timeout = settings.agent_timeout
        self.model_name = "llama-3.3-70b-versatile"
        self.temperature = 0.7

    def _call_groq(self, messages: List[Dict[str, str]]) -> str:
        """Synchronous Groq API call."""
        client = Groq(api_key=settings.groq_api_key)
        try:
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=1024,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise

    def _parse_action(self, text: str) -> Optional[Dict[str, str]]:
        """Parse ACTION / INPUT from agent response."""
        action_match = re.search(r'ACTION:\s*(\w+)', text, re.IGNORECASE)
        if not action_match:
            return None
        tool_name = action_match.group(1)
        input_match = re.search(r'INPUT:\s*(.+?)(?:\n|$)', text, re.IGNORECASE | re.DOTALL)
        tool_input = input_match.group(1).strip() if input_match else ""
        return {"tool": tool_name, "input": tool_input}

    async def _invoke_tool(self, tool_name: str, tool_input: str) -> str:
        """Invoke the selected tool and return a formatted string."""
        try:
            if tool_name == "Tavily_Search":
                logger.info(f"Invoking Tavily_Search: {tool_input}")
                result = await tavily_tool.search(tool_input, max_results=5)
                return tavily_tool.format_results(result)

            elif tool_name == "Google_Trends_MCP":
                logger.info(f"Invoking Google_Trends_MCP: {tool_input}")
                result = await google_trends_tool.get_trending_terms()
                return google_trends_tool.format_trends(result)

            else:
                return f"Unknown tool: {tool_name}"

        except Exception as e:
            logger.error(f"Tool error ({tool_name}): {e}")
            return f"Tool error: {e}. I'll answer from my knowledge instead."

    async def process_message(
        self,
        user_message: str,
        conversation_id: str,
        user_id: str,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process a user message with intent-aware tool routing."""
        try:
            yield {"event": "loading", "data": {"status": "Agent is thinking..."}}

            # 1. Classify intent BEFORE any LLM call
            intent = _classify_intent(user_message)
            logger.info(f"Intent classified as '{intent}' for query: {user_message[:60]}")

            # 2. Emit which tool (if any) will be used
            tool_display = {
                "trends": ("Google_Trends_MCP", "Google Trends"),
                "search": ("Tavily_Search", "Web Search"),
                "general": (None, None),
            }
            tool_id, tool_name = tool_display[intent]
            if tool_id:
                yield {
                    "event": "tool_selected",
                    "data": {"tool": tool_id, "tool_name": tool_name},
                }

            # 3. Load conversation history
            messages_data = supabase_client.get_recent_messages(
                conversation_id, user_id, limit=10
            )
            messages = [{"role": "system", "content": _PROMPTS[intent]}]
            for msg in messages_data:
                messages.append({"role": msg["role"], "content": msg["content"]})
            messages.append({"role": "user", "content": user_message})

            # 4. For general intent — skip ReAct loop entirely
            if intent == "general":
                yield {"event": "responding", "data": {"status": "Generating response..."}}
                final_response = await asyncio.wait_for(
                    asyncio.to_thread(self._call_groq, messages),
                    timeout=self.timeout,
                )
            else:
                # 5. ReAct loop — but the prompt only mentions one tool
                final_response = None
                for iteration in range(1, self.max_iterations + 1):
                    logger.info(f"ReAct iteration {iteration}/{self.max_iterations}")
                    yield {"event": "responding", "data": {"status": "Generating response..."}}

                    response = await asyncio.wait_for(
                        asyncio.to_thread(self._call_groq, messages),
                        timeout=self.timeout,
                    )

                    action = self._parse_action(response)
                    if action:
                        yield {
                            "event": "tool_activity",
                            "data": {
                                "tool": action["tool"],
                                "status": "started",
                                "message": f"Using {tool_name}...",
                            },
                        }
                        tool_result = await self._invoke_tool(action["tool"], action["input"])
                        yield {
                            "event": "tool_activity",
                            "data": {"tool": action["tool"], "status": "completed"},
                        }
                        messages.append({"role": "assistant", "content": response})
                        messages.append({"role": "user", "content": f"Tool result:\n{tool_result}"})
                    else:
                        final_response = response
                        break

                if final_response is None:
                    logger.warning("Max iterations reached — using last response")
                    final_response = response

            # 6. Stream response tokens
            yield {"event": "streaming", "data": {"status": "Streaming response..."}}
            for token in final_response.split():
                yield {"event": "token", "data": {"token": token + " "}}

            # 7. Persist message
            supabase_client.save_message(
                conversation_id=conversation_id,
                user_id=user_id,
                role="assistant",
                content=final_response,
            )

            yield {"event": "done", "data": {"message_id": "generated"}}

        except asyncio.TimeoutError:
            logger.error(f"Agent timed out after {self.timeout}s")
            yield {"event": "error", "data": {"error": "Request timed out"}}
        except Exception as e:
            logger.error(f"Agent error: {e}", exc_info=True)
            yield {"event": "error", "data": {"error": str(e)}}

    async def health_check(self) -> bool:
        try:
            return await google_trends_tool.health_check()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


# Global instance
react_agent = ReActAgent()
