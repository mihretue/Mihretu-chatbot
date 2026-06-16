from supabase import create_client, Client
from app.core.config import settings
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Wrapper for Supabase client operations."""

    def __init__(self):
        """Initialize Supabase client with two connections:
        - auth_client: anon key for auth operations (sign up, sign in)
        - client: service role key for DB operations (bypasses RLS)
        """
        self.auth_client: Client = create_client(
            settings.supabase_url,
            settings.supabase_key,
        )
        service_key = settings.supabase_service_key or settings.supabase_key
        if not settings.supabase_service_key:
            logger.warning("SUPABASE_SERVICE_KEY not set — DB operations will use anon key and may fail due to RLS")
        self.client: Client = create_client(
            settings.supabase_url,
            service_key,
        )

    def create_user(self, email: str, password: str) -> Dict[str, Any]:
        """Create a new user in Supabase Auth."""
        try:
            response = self.auth_client.auth.sign_up({
                "email": email,
                "password": password,
            })
            logger.info(f"User created: {email}")
            return {
                "user": response.user,
                "session": response.session,
            }
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise

    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user with email and password."""
        try:
            logger.info(f"[AUTH] Starting authentication for email: {email}")
            
            response = self.auth_client.auth.sign_in_with_password({
                "email": email,
                "password": password,
            })
            
            logger.info(f"[AUTH] Response received from Supabase")
            logger.info(f"[AUTH] Response type: {type(response)}")
            
            user = response.user
            session = response.session
            
            logger.info(f"[AUTH] User object: {user}")
            logger.info(f"[AUTH] User ID: {user.id if user else 'None'}")
            logger.info(f"[AUTH] Session object: {session}")
            logger.info(f"[AUTH] Session type: {type(session)}")
            
            if session:
                logger.info(f"[AUTH] Session access_token exists: {bool(session.access_token)}")
                logger.info(f"[AUTH] Session token_type: {session.token_type}")
            else:
                logger.warning(f"[AUTH] Session is None!")
            
            logger.info(f"User authenticated: {email}")
            
            result = {
                "user": user,
                "session": session,
            }
            
            return result
        except Exception as e:
            logger.error(f"[AUTH] Error authenticating user: {str(e)}")
            logger.error(f"[AUTH] Error type: {type(e)}")
            import traceback
            logger.error(f"[AUTH] Traceback: {traceback.format_exc()}")
            raise

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            response = self.auth_client.auth.admin.get_user(user_id)
            return response.user
        except Exception as e:
            logger.error(f"Error getting user: {str(e)}")
            return None

    def create_conversation(
        self, user_id: str, title: str
    ) -> Dict[str, Any]:
        """Create a new conversation."""
        try:
            response = self.client.table("conversations").insert({
                "user_id": user_id,
                "title": title,
            }).execute()
            logger.info(f"Conversation created: {response.data[0]['id']}")
            return response.data[0]
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            raise

    def get_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all conversations for a user."""
        try:
            response = self.client.table("conversations").select("*").eq(
                "user_id", user_id
            ).order("updated_at", desc=True).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error getting conversations: {str(e)}")
            return []

    def get_conversation(
        self, conversation_id: str, user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a specific conversation."""
        try:
            response = self.client.table("conversations").select("*").eq(
                "id", conversation_id
            ).eq("user_id", user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error getting conversation: {str(e)}")
            return None

    def save_message(
        self,
        conversation_id: str,
        user_id: str,
        role: str,
        content: str,
        tool_calls: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Save a message to the database."""
        try:
            response = self.client.table("messages").insert({
                "conversation_id": conversation_id,
                "user_id": user_id,
                "role": role,
                "content": content,
                "tool_calls": tool_calls,
            }).execute()
            logger.info(f"Message saved: {response.data[0]['id']}")
            return response.data[0]
        except Exception as e:
            logger.error(f"Error saving message: {str(e)}")
            raise

    def get_messages(
        self, conversation_id: str, user_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get messages for a conversation."""
        try:
            response = self.client.table("messages").select("*").eq(
                "conversation_id", conversation_id
            ).eq("user_id", user_id).order(
                "created_at", desc=False
            ).limit(limit).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error getting messages: {str(e)}")
            return []

    def get_recent_messages(
        self, conversation_id: str, user_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent messages for a conversation (for agent context)."""
        try:
            response = self.client.table("messages").select("*").eq(
                "conversation_id", conversation_id
            ).eq("user_id", user_id).order(
                "created_at", desc=True
            ).limit(limit).execute()
            # Reverse to get chronological order
            return list(reversed(response.data))
        except Exception as e:
            logger.error(f"Error getting recent messages: {str(e)}")
            return []


# Global instance
supabase_client = SupabaseClient()
