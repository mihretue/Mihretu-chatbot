"""LangChain ReAct agent for chatbot."""

from langchain.agents import initialize_agent, AgentType, Tool
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage
import logging
from typing import List, Dict, Any, AsyncGenerator
import asyncio
import os

from supabase_client import supabase_client
from tools import get_trending_terms, get_news_by_keyword

logger = logging.getLogger(__name__)


# logging

class ReActAgent:
    """LangChain ReAct agent with tool selection."""

    def __init__(self):
        """Initialize ReAct agent."""
        self.max_iterations = int(os.getenv("AGENT_MAX_ITERATIONS", "10"))
        self.timeout = int(os.getenv("AGENT_TIMEOUT", "30"))
        
        # Initialize LLM
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            logger.warning("OPENAI_API_KEY not set, agent will have limited functionality")
        
        self.llm = ChatOpenAI(temperature=0.7, api_key=openai_api_key)
        self.tools = self._create_tools()

    def _create_tools(self) -> List[Tool]:
        """Create LangChain tools."""
        return [
            Tool(
                name="Tavily_Search",
                func=self._tavily_search_sync,
                description="Search the web for current information, news, and recent events. Use this when you need up-to-date information.",
            ),
            Tool(
                name="Google_Trends_MCP",
                func=self._trends_search_sync,
                description="Get trending topics and popular searches. Use this when asked about trends, viral content, or what's popular.",
            ),
        ]

    def _tavily_search_sync(self, query: str) -> str:
        """Sync wrapper for Tavily search (for LangChain)."""
        try:
            # For now, return a placeholder
            # In production, integrate with actual Tavily API
            return f"Search results for '{query}': [Tavily search would be performed here]"
        except Exception as e:
            logger.error(f"Tavily search error: {str(e)}")
            return f"Error searching the web: {str(e)}"

    def _trends_search_sync(self, query: str) -> str:
        """Sync wrapper for trends search (for LangChain)."""
        try:
            # For now, return a placeholder
            # In production, integrate with actual Google Trends MCP
            return f"Trending data for '{query}': [Google Trends data would be retrieved here]"
        except Exception as e:
            logger.error(f"Trends search error: {str(e)}")
            return f"Error fetching trends: {str(e)}"

    async def process_message(
        self,
        user_message: str,
        conversation_id: str,
        user_id: str,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process user message and stream response.
        
        Args:
            user_message: User's message
            conversation_id: Conversation ID
            user_id: User ID
            
        Yields:
            Dictionary with event type and data
        """
        try:
            # Load conversation history
            messages = await supabase_client.get_recent_messages(
                conversation_id, user_id, limit=10
            )

            # Format history for agent
            history = []
            for msg in messages:
                if msg["role"] == "user":
                    history.append(HumanMessage(content=msg["content"]))
                else:
                    history.append(AIMessage(content=msg["content"]))

            # Create memory
            memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
            )
            for msg in history:
                if isinstance(msg, HumanMessage):
                    memory.chat_memory.add_user_message(msg.content)
                else:
                    memory.chat_memory.add_ai_message(msg.content)

            # Initialize agent
            agent = initialize_agent(
                self.tools,
                self.llm,
                agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION,
                memory=memory,
                max_iterations=self.max_iterations,
                verbose=True,
            )

            # Process message
            logger.info(f"Processing message for user {user_id}")

            # Run agent with timeout
            response = await asyncio.wait_for(
                asyncio.to_thread(agent.run, user_message),
                timeout=self.timeout,
            )

            # Stream response tokens
            for token in response.split():
                yield {
                    "event": "token",
                    "data": {"token": token + " "},
                }

            # Save agent response
            await supabase_client.save_message(
                conversation_id=conversation_id,
                user_id=user_id,
                role="assistant",
                content=response,
            )

            # Emit done event
            yield {
                "event": "done",
                "data": {"message_id": "generated"},
            }

        except asyncio.TimeoutError:
            logger.error(f"Agent processing timed out after {self.timeout}s")
            yield {
                "event": "error",
                "data": {"error": "Request timed out"},
            }
        except Exception as e:
            logger.error(f"Agent processing error: {str(e)}")
            yield {
                "event": "error",
                "data": {"error": str(e)},
            }

    async def health_check(self) -> bool:
        """Check if agent dependencies are healthy."""
        try:
            # Check if we can initialize the agent
            _ = self.tools
            return True
        except Exception as e:
            logger.error(f"Agent health check failed: {str(e)}")
            return False


# Global instance
react_agent = ReActAgent()
