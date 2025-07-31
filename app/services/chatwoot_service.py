"""Service for interacting with the Chatwoot API."""

import asyncio
import httpx
import logging
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from ..config import settings

# Configure logger with enhanced debugging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Add handler if not already present
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


@dataclass
class ChatwootConfig:
    """Configuration for Chatwoot API access."""
    
    base_url: str
    api_access_token: str
    account_id: int
    inbox_id: Optional[int] = None


@dataclass
class ChatwootMessage:
    """Represents a message in Chatwoot."""
    
    conversation_id: int
    content: str
    message_type: str = "outgoing"  # "incoming" or "outgoing"
    private: bool = False
    content_type: str = "text"  # "text", "input_select", "cards", "form"


class ChatwootService:
    """Service for handling Chatwoot API interactions."""
    
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.configs: Dict[str, ChatwootConfig] = {}
    
    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()
    
    def add_hotel_config(self, hotel_id: str, config: ChatwootConfig):
        """Add Chatwoot configuration for a specific hotel."""
        self.configs[hotel_id] = config
        logger.info(f"🏨 Added Chatwoot config for hotel {hotel_id}: {config.base_url}")
    
    def get_hotel_config(self, hotel_id: str) -> Optional[ChatwootConfig]:
        """Get Chatwoot configuration for a hotel."""
        return self.configs.get(hotel_id)
    
    async def send_message(
        self,
        hotel_id: str,
        conversation_id: int,
        content: str,
        message_type: str = "outgoing",
        private: bool = False
    ) -> Dict[str, Any]:
        """
        Send a message to a Chatwoot conversation.
        
        Args:
            hotel_id: Hotel identifier
            conversation_id: Chatwoot conversation ID
            content: Message content to send
            message_type: "outgoing" (from bot) or "incoming" (from user)
            private: Whether this is a private note (not visible to customer)
        
        Returns:
            API response from Chatwoot or error details
        """
        config = self.get_hotel_config(hotel_id)
        if not config:
            logger.error(f"❌ No Chatwoot config found for hotel {hotel_id}")
            return {
                "success": False,
                "error": f"No Chatwoot configuration found for hotel {hotel_id}",
                "hotel_id": hotel_id
            }
        
        url = f"{config.base_url}/api/v1/accounts/{config.account_id}/conversations/{conversation_id}/messages"
        
        headers = {
            "Content-Type": "application/json",
            "api_access_token": config.api_access_token
        }
        
        payload = {
            "content": content,
            "message_type": message_type,
            "private": private
        }
        
        try:
            logger.info(f"📤 Sending message to Chatwoot conversation {conversation_id} for hotel {hotel_id}")
            logger.info(f"🌐 URL: {url}")
            logger.info(f"🔑 Headers: api_access_token={config.api_access_token[:10]}...")
            logger.info(f"📋 Payload: {json.dumps(payload, indent=2)}")
            
            response = await self.http_client.post(
                url,
                json=payload,
                headers=headers
            )
            
            logger.info(f"📥 Chatwoot API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Message sent successfully to conversation {conversation_id}")
                logger.info(f"📄 Chatwoot Response: {json.dumps(result, indent=2)}")
                
                return {
                    "success": True,
                    "message_id": result.get("id"),
                    "conversation_id": conversation_id,
                    "hotel_id": hotel_id,
                    "content": content,
                    "sent_at": datetime.now().isoformat()
                }
            else:
                error_text = response.text
                logger.error(f"❌ Failed to send message: {response.status_code}")
                logger.error(f"📝 Error details: {error_text}")
                logger.error(f"🌐 Failed URL: {url}")
                logger.error(f"🔑 Failed with token: {config.api_access_token[:10]}...")
                
                return {
                    "success": False,
                    "error": f"Chatwoot API error: {response.status_code}",
                    "error_details": error_text,
                    "hotel_id": hotel_id,
                    "conversation_id": conversation_id
                }
                
        except httpx.TimeoutException:
            logger.error(f"⏰ Timeout sending message to Chatwoot for hotel {hotel_id}")
            return {
                "success": False,
                "error": "Request timeout",
                "hotel_id": hotel_id,
                "conversation_id": conversation_id
            }
        except Exception as e:
            logger.error(f"💥 Unexpected error sending message: {str(e)}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "hotel_id": hotel_id,
                "conversation_id": conversation_id
            }
    
    async def get_conversation(self, hotel_id: str, conversation_id: int) -> Dict[str, Any]:
        """Get conversation details from Chatwoot."""
        config = self.get_hotel_config(hotel_id)
        if not config:
            return {
                "success": False,
                "error": f"No Chatwoot configuration found for hotel {hotel_id}"
            }
        
        url = f"{config.base_url}/api/v1/accounts/{config.account_id}/conversations/{conversation_id}"
        
        headers = {
            "Content-Type": "application/json",
            "api_access_token": config.api_access_token
        }
        
        try:
            response = await self.http_client.get(url, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Retrieved conversation {conversation_id} for hotel {hotel_id}")
                return {
                    "success": True,
                    "conversation": result,
                    "hotel_id": hotel_id
                }
            else:
                error_text = await response.atext()
                logger.error(f"❌ Failed to get conversation: {response.status_code} - {error_text}")
                return {
                    "success": False,
                    "error": f"Chatwoot API error: {response.status_code}",
                    "error_details": error_text
                }
                
        except Exception as e:
            logger.error(f"💥 Error getting conversation: {str(e)}")
            return {
                "success": False,
                "error": f"Error: {str(e)}"
            }
    
    async def mark_conversation_resolved(self, hotel_id: str, conversation_id: int) -> Dict[str, Any]:
        """Mark a conversation as resolved in Chatwoot."""
        config = self.get_hotel_config(hotel_id)
        if not config:
            return {
                "success": False,
                "error": f"No Chatwoot configuration found for hotel {hotel_id}"
            }
        
        url = f"{config.base_url}/api/v1/accounts/{config.account_id}/conversations/{conversation_id}/toggle_status"
        
        headers = {
            "Content-Type": "application/json",
            "api_access_token": config.api_access_token
        }
        
        payload = {
            "status": "resolved"
        }
        
        try:
            response = await self.http_client.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                logger.info(f"✅ Marked conversation {conversation_id} as resolved for hotel {hotel_id}")
                return {
                    "success": True,
                    "conversation_id": conversation_id,
                    "status": "resolved",
                    "hotel_id": hotel_id
                }
            else:
                error_text = await response.atext()
                logger.error(f"❌ Failed to resolve conversation: {response.status_code} - {error_text}")
                return {
                    "success": False,
                    "error": f"Chatwoot API error: {response.status_code}",
                    "error_details": error_text
                }
                
        except Exception as e:
            logger.error(f"💥 Error resolving conversation: {str(e)}")
            return {
                "success": False,
                "error": f"Error: {str(e)}"
            }
    
    async def mark_conversation_open(self, hotel_id: str, conversation_id: int) -> Dict[str, Any]:
        """
        Mark a conversation as open in Chatwoot for human agent assignment.
        This will trigger automatic assignment to available agents.
        """
        config = self.get_hotel_config(hotel_id)
        if not config:
            return {
                "success": False,
                "error": f"No Chatwoot configuration found for hotel {hotel_id}"
            }
        
        url = f"{config.base_url}/api/v1/accounts/{config.account_id}/conversations/{conversation_id}/toggle_status"
        
        headers = {
            "Content-Type": "application/json",
            "api_access_token": config.api_access_token
        }
        
        payload = {
            "status": "open"
        }
        
        try:
            logger.info(f"🔓 Marking conversation {conversation_id} as open for hotel {hotel_id}")
            response = await self.http_client.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Marked conversation {conversation_id} as open for hotel {hotel_id}")
                logger.info(f"📄 Status change result: {result}")
                return {
                    "success": True,
                    "conversation_id": conversation_id,
                    "status": "open",
                    "hotel_id": hotel_id,
                    "response": result
                }
            else:
                error_text = response.text
                logger.error(f"❌ Failed to mark conversation as open: {response.status_code} - {error_text}")
                return {
                    "success": False,
                    "error": f"Chatwoot API error: {response.status_code}",
                    "error_details": error_text,
                    "hotel_id": hotel_id,
                    "conversation_id": conversation_id
                }
                
        except Exception as e:
            logger.error(f"💥 Error marking conversation as open: {str(e)}")
            return {
                "success": False,
                "error": f"Error: {str(e)}",
                "hotel_id": hotel_id,
                "conversation_id": conversation_id
            }
    
    async def send_private_note(
        self,
        hotel_id: str,
        conversation_id: int,
        content: str
    ) -> Dict[str, Any]:
        """
        Send a private note to a Chatwoot conversation (only visible to agents).
        This is a convenience method that calls send_message with private=True.
        """
        return await self.send_message(
            hotel_id=hotel_id,
            conversation_id=conversation_id,
            content=content,
            message_type="outgoing",
            private=True
        )
    
    async def get_conversation_status(self, hotel_id: str, conversation_id: int) -> Dict[str, Any]:
        """Get current status of a conversation."""
        conversation_result = await self.get_conversation(hotel_id, conversation_id)
        
        if conversation_result.get("success"):
            conversation_data = conversation_result.get("conversation", {})
            status = conversation_data.get("status", "unknown")
            assignee = conversation_data.get("assignee")
            
            return {
                "success": True,
                "status": status,
                "assignee": assignee,
                "conversation_id": conversation_id,
                "hotel_id": hotel_id
            }
        else:
            return conversation_result


# Global Chatwoot service instance
chatwoot_service = ChatwootService()


async def initialize_chatwoot_configs():
    """Initialize Chatwoot configurations for all hotels from Directus."""
    logger.info("🏨 Initializing Chatwoot configurations for all hotels...")
    
    try:
        from .directus_service import directus_service
        
        # Get all hotels with Chatwoot configurations
        hotels_with_chatwoot = await directus_service.get_hotels_with_chatwoot_config()
        logger.info(f"🔍 Found {len(hotels_with_chatwoot)} hotels with potential Chatwoot config")
        
        for hotel in hotels_with_chatwoot:
            hotel_id = hotel.get("id")
            
            # Read Chatwoot fields directly from the hotel object
            base_url = hotel.get("chatwoot_base_url")
            # Check both possible field names for API token
            api_token = hotel.get("chatwoot_api_token") or hotel.get("chatwoot_api_access_token")
            account_id = hotel.get("chatwoot_account_id")
            
            # Validate required fields
            if base_url and api_token and account_id:
                config = ChatwootConfig(
                    base_url=base_url,
                    api_access_token=api_token,
                    account_id=account_id,
                    inbox_id=hotel.get("chatwoot_inbox_id")  # Optional field
                )
                
                # Convert hotel_id to string when adding config
                chatwoot_service.add_hotel_config(str(hotel_id), config)
                logger.info(f"✅ Initialized Chatwoot config for hotel {hotel_id}")
                logger.info(f"   Base URL: {config.base_url}")
                logger.info(f"   Account ID: {config.account_id}")
                logger.info(f"   Token: {config.api_access_token[:10]}...")
            else:
                logger.warning(f"⚠️ Incomplete Chatwoot config for hotel {hotel_id}")
                logger.warning(f"   Base URL: {base_url or 'NOT SET'}")
                logger.warning(f"   API Token: {'SET' if api_token else 'NOT SET'}")
                logger.warning(f"   Account ID: {account_id or 'NOT SET'}")
                logger.warning(f"   Raw hotel data: {json.dumps(hotel, indent=2)}")
                
    except Exception as e:
        logger.error(f"❌ Failed to initialize Chatwoot configs: {str(e)}")
        import traceback
        logger.error(f"📚 Traceback: {traceback.format_exc()}")


# Note: All Chatwoot configurations must come from Directus per hotel
# There is no global/default configuration in a multi-tenant system