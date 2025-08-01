"""Directus service for database operations."""

import asyncio
import logging
import json
from typing import Optional, Dict, Any, List
import httpx

from ..config import settings

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Using httpx directly instead of py_directus due to compatibility issues
try:
    # Try to import py_directus for future use
    from py_directus import Directus, F
    PY_DIRECTUS_AVAILABLE = True
except ImportError:
    # Fallback: Define dummy classes
    class Directus:
        pass
    class F:
        pass
    PY_DIRECTUS_AVAILABLE = False


class DirectusService:
    """Service for Directus database operations."""
    
    def __init__(self):
        self._client: Optional[Directus] = None
    
    async def get_client(self) -> Directus:
        """Get or create Directus client."""
        if self._client is None:
            try:
                # Prefer token authentication if available
                if settings.directus_token:
                    self._client = await Directus(
                        url=settings.directus_url,
                        token=settings.directus_token
                    )
                elif settings.directus_email and settings.directus_password:
                    self._client = await Directus(
                        url=settings.directus_url,
                        email=settings.directus_email,
                        password=settings.directus_password
                    )
                else:
                    raise ValueError("Directus authentication credentials not provided")
            except Exception as e:
                print(f"Error connecting to Directus: {e}")
                raise
        
        return self._client
    
    async def close(self):
        """Close Directus client connection."""
        if self._client:
            await self._client.close()
            self._client = None
    
    # Hotel Operations
    async def get_hotel_by_id(self, hotel_id: str) -> Optional[Dict[str, Any]]:
        """Get hotel by ID."""
        try:
            client = await self.get_client()
            result = await client.collection("hotels").filter(id=hotel_id).read()
            
            if result and len(result) > 0:
                return result[0]
            return None
        except Exception as e:
            print(f"Error getting hotel by ID {hotel_id}: {e}")
            return None
    
    async def get_hotel_by_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        """Get hotel by domain."""
        try:
            client = await self.get_client()
            result = await client.collection("hotels").filter(domain=domain).read()
            
            if result and len(result) > 0:
                return result[0]
            return None
        except Exception as e:
            print(f"Error getting hotel by domain {domain}: {e}")
            return None
    
    async def get_hotel_coordinates(self, hotel_id: str) -> Optional[Dict[str, Any]]:
        """Get hotel coordinates and location info."""
        try:
            client = await self.get_client()
            result = await client.collection("hotels").filter(id=hotel_id).read()
            
            if result and len(result) > 0:
                hotel = result[0]
                return {
                    "latitude": hotel.get("latitude"),
                    "longitude": hotel.get("longitude"),
                    "address": hotel.get("address"),
                    "name": hotel.get("name")
                }
            return None
        except Exception as e:
            print(f"Error getting hotel coordinates for {hotel_id}: {e}")
            return None
    
    async def get_hotel_name(self, hotel_id: str) -> Optional[str]:
        """Get hotel name by ID."""
        try:
            client = await self.get_client()
            result = await client.collection("hotels").filter(id=hotel_id).read()
            
            if result and len(result) > 0:
                return result[0].get("name")
            return None
        except Exception as e:
            print(f"Error getting hotel name for {hotel_id}: {e}")
            return None
    
    async def get_hotels_with_chatwoot_config(self) -> List[Dict[str, Any]]:
        """Get all hotels that have Chatwoot configuration."""
        # Use httpx directly for reliability
        async with httpx.AsyncClient() as http_client:
            try:
                headers = {
                    "Authorization": f"Bearer {settings.directus_token}"
                }
                
                # Query hotels with chatwoot fields
                url = f"{settings.directus_url}/items/hotels"
                params = {
                    "fields": "id,name,domain,chatwoot_base_url,chatwoot_api_token,chatwoot_api_access_token,chatwoot_account_id",
                    # Filter for hotels that have at least the base URL configured
                    "filter[chatwoot_base_url][_nnull]": "true"
                }
                
                response = await http_client.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    hotels = data.get("data", [])
                    logger.info(f"🏨 Found {len(hotels)} hotels with Chatwoot config")
                    
                    # Log each hotel's config for debugging
                    for hotel in hotels:
                        logger.info(f"Hotel {hotel.get('id')} - {hotel.get('name')}:")
                        logger.info(f"  Base URL: {hotel.get('chatwoot_base_url')}")
                        logger.info(f"  API Token: {'SET' if hotel.get('chatwoot_api_token') else 'NOT SET'}")
                        logger.info(f"  Account ID: {hotel.get('chatwoot_account_id')}")
                        logger.info(f"  Website Token: {hotel.get('chatwoot_website_token') or 'Not set'}")
                    
                    return hotels
                else:
                    logger.error(f"❌ Error fetching hotels: {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    return []
                    
            except Exception as e:
                logger.error(f"❌ Error getting hotels with Chatwoot config: {e}")
                import traceback
                logger.error(f"📚 Traceback: {traceback.format_exc()}")
                return []
    
    # Activities Operations
    async def get_hotel_activities(self, hotel_id: str) -> List[Dict[str, Any]]:
        """Get activities for a hotel."""
        try:
            client = await self.get_client()
            result = await client.collection("activities").filter(
                F(hotel_id=hotel_id) & F(status="published")
            ).read()
            
            return result or []
        except Exception as e:
            print(f"Error getting activities for hotel {hotel_id}: {e}")
            return []
    
    # Facilities Operations
    async def get_hotel_facilities(self, hotel_id: str) -> List[Dict[str, Any]]:
        """Get facilities for a hotel."""
        try:
            client = await self.get_client()
            result = await client.collection("facilities").filter(
                F(hotel_id=hotel_id) & F(status="published")
            ).read()
            
            return result or []
        except Exception as e:
            print(f"Error getting facilities for hotel {hotel_id}: {e}")
            return []
    
    # Service Requests Operations
    async def create_service_request(self, request_data: Dict[str, Any]) -> Optional[str]:
        """Create a service request."""
        try:
            client = await self.get_client()
            result = await client.collection("service_requests").create(request_data)
            
            if result:
                return result.get("id")
            return None
        except Exception as e:
            print(f"Error creating service request: {e}")
            return None
    
    # Generic Operations
    async def query_collection(
        self, 
        collection: str, 
        filters: Optional[Dict[str, Any]] = None,
        fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Generic query operation for any collection."""
        try:
            client = await self.get_client()
            query = client.collection(collection)
            
            # Apply filters if provided
            if filters:
                for key, value in filters.items():
                    if isinstance(value, dict) and "_eq" in value:
                        # Handle Directus-style filters
                        query = query.filter(**{key: value["_eq"]})
                    else:
                        query = query.filter(**{key: value})
            
            # Apply field selection if provided
            if fields:
                query = query.fields(*fields)
            
            result = await query.read()
            return result or []
        except Exception as e:
            print(f"Error querying collection {collection}: {e}")
            return []


# Global Directus service instance
directus_service = DirectusService()


# Context manager for automatic cleanup
class DirectusContext:
    """Context manager for Directus operations."""
    
    def __init__(self):
        self.service = DirectusService()
    
    async def __aenter__(self):
        return self.service
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.service.close()


# Compatibility layer to ease migration
class SupabaseCompatibilityLayer:
    """Compatibility layer to mimic Supabase table operations."""
    
    def __init__(self, directus_service: DirectusService):
        self.directus_service = directus_service
    
    def table(self, table_name: str):
        """Create table query builder."""
        return DirectusTableQuery(self.directus_service, table_name)


class DirectusTableQuery:
    """Query builder that mimics Supabase table operations."""
    
    def __init__(self, directus_service: DirectusService, table_name: str):
        self.directus_service = directus_service
        self.table_name = table_name
        self._filters = {}
        self._fields = []
    
    def select(self, fields: str = "*") -> "DirectusTableQuery":
        """Select fields (compatibility method)."""
        if fields != "*":
            self._fields = [f.strip() for f in fields.split(",")]
        return self
    
    def eq(self, column: str, value: Any) -> "DirectusTableQuery":
        """Add equality filter."""
        self._filters[column] = {"_eq": value}
        return self
    
    async def execute(self) -> Dict[str, Any]:
        """Execute the query."""
        try:
            result = await self.directus_service.query_collection(
                self.table_name,
                filters=self._filters,
                fields=self._fields if self._fields else None
            )
            
            # Return in Supabase-like format
            return {
                "data": result,
                "error": None
            }
        except Exception as e:
            return {
                "data": None,
                "error": str(e)
            }


# Create compatibility instance
def create_directus_client() -> SupabaseCompatibilityLayer:
    """Create a Directus client with Supabase-like interface."""
    return SupabaseCompatibilityLayer(directus_service)