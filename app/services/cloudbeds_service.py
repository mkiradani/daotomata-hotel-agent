"""Cloudbeds API service for room availability and reservations."""

import os
import httpx
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from app.services.directus_service import DirectusService
from app.config import settings


class CloudbedsService:
    """Service for interacting with Cloudbeds API."""
    
    def __init__(self):
        self.directus_service = DirectusService()
        self.base_url = "https://api.cloudbeds.com/api/v1.3"
        
    async def get_hotel_credentials(self, hotel_id: int) -> Dict[str, str]:
        """Get Cloudbeds credentials for a specific hotel from Directus."""
        try:
            # Use httpx directly for reliability
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {settings.directus_token}"
                }
                
                url = f"{settings.directus_url}/items/hotels/{hotel_id}"
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    hotel = data.get("data", {})
                    
                    return {
                        "client_id": hotel.get("cloudbeds_client_id"),
                        "client_secret": hotel.get("cloudbeds_client_secret"),
                        "api_key": hotel.get("cloudbeds_api_key"),
                        "property_id": hotel.get("cloudbeds_property_id"),
                        "booking_url_id": hotel.get("cloudbeds_booking_url_id"),
                    }
                else:
                    print(f"Hotel {hotel_id} not found or error: {response.status_code}")
                    return {}
                    
        except Exception as e:
            print(f"Error getting hotel credentials: {e}")
            return {}
    
    async def check_availability(
        self,
        hotel_id: int,
        check_in: str,
        check_out: str,
        adults: int = 2,
        children: int = 0,
        rooms: int = 1
    ) -> Dict[str, Any]:
        """Check room availability using Cloudbeds API."""
        try:
            # Get hotel credentials
            credentials = await self.get_hotel_credentials(hotel_id)
            if not credentials.get("api_key"):
                return {
                    "available": False,
                    "error": "Cloudbeds API not configured for this hotel"
                }
            
            # Parse dates
            check_in_date = datetime.strptime(check_in, "%Y-%m-%d").date()
            check_out_date = datetime.strptime(check_out, "%Y-%m-%d").date()
            
            # Validate dates
            if check_in_date <= date.today():
                return {
                    "available": False,
                    "error": "Check-in date must be in the future"
                }
            
            if check_out_date <= check_in_date:
                return {
                    "available": False,
                    "error": "Check-out date must be after check-in date"
                }
            
            # Call Cloudbeds API to get available room types
            params = {
                "propertyIDs": credentials.get("property_id", ""),
                "startDate": check_in,
                "endDate": check_out,
                "adults": str(adults),
                "children": str(children) if children > 0 else "0",
                "rooms": str(rooms)
            }
            
            headers = {
                "Authorization": f"Bearer {credentials['api_key']}",
                "Content-Type": "application/json",
                "x-property-id": credentials.get("property_id", "")
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/getAvailableRoomTypes",
                    params=params,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("success") and data.get("data"):
                        available_rooms = []
                        nights = (check_out_date - check_in_date).days
                        
                        # Process each property in the response
                        for property_data in data["data"]:
                            if property_data.get("propertyRooms"):
                                for room in property_data["propertyRooms"]:
                                    if room.get("roomsAvailable", 0) > 0:
                                        available_rooms.append({
                                            "roomTypeID": room.get("roomTypeID"),
                                            "roomTypeName": room.get("roomTypeName"),
                                            "roomsAvailable": room.get("roomsAvailable"),
                                            "maxGuests": room.get("maxGuests"),
                                            "roomRate": float(room.get("roomRate", 0)),
                                            "totalRate": float(room.get("roomRate", 0)) * nights if room.get("roomRate") else 0,
                                            "currency": property_data.get("propertyCurrency", {}).get("currencyCode", "EUR")
                                        })
                        
                        return {
                            "available": len(available_rooms) > 0,
                            "check_in": check_in,
                            "check_out": check_out,
                            "nights": nights,
                            "adults": adults,
                            "children": children,
                            "rooms": available_rooms,
                            "total_rooms_available": len(available_rooms),
                            "hotel_id": hotel_id,
                            "booking_url": self.build_booking_url(
                                credentials.get("booking_url_id", ""),
                                check_in,
                                check_out,
                                adults,
                                children
                            )
                        }
                    else:
                        return {
                            "available": False,
                            "error": "No rooms available for the selected dates"
                        }
                else:
                    # If API call fails, fallback to booking URL
                    booking_url = self.build_booking_url(
                        credentials.get("booking_url_id", ""),
                        check_in,
                        check_out,
                        adults,
                        children
                    )
                    
                    nights = (check_out_date - check_in_date).days
                    
                    return {
                        "available": True,
                        "check_in": check_in,
                        "check_out": check_out,
                        "nights": nights,
                        "adults": adults,
                        "children": children,
                        "booking_url": booking_url,
                        "message": "Unable to check real-time availability. Please use the booking link to check availability and complete your reservation.",
                        "hotel_id": hotel_id
                    }
            
        except Exception as e:
            return {
                "available": False,
                "error": f"Error checking availability: {str(e)}"
            }
    
    def build_booking_url(
        self,
        booking_url_id: str,
        check_in: str,
        check_out: str,
        adults: int = 1,
        children: int = 0,
        currency: str = "eur"
    ) -> str:
        """Build Cloudbeds URL for hotel reservations redirect."""
        if not booking_url_id:
            return ""
            
        base_url = "https://hotels.cloudbeds.com/en/reservas"
        
        # Build query parameters
        params = {
            "checkin": check_in,
            "checkout": check_out,
            "adults": str(adults),
            "kids": str(children),
            "currency": currency.lower()
        }
        
        # Convert params to query string
        query_string = "&".join([f"{key}={value}" for key, value in params.items()])
        
        return f"{base_url}/{booking_url_id}?{query_string}"
    
    async def get_currency_settings(self, hotel_id: int) -> Dict[str, Any]:
        """Get currency settings and exchange rates for a hotel.
        
        Args:
            hotel_id: The hotel ID
            
        Returns:
            Dict containing currency settings including:
            - default: Default currency ISO code
            - acceptable: List of acceptable currency ISO codes
            - format: Currency formatting settings
            - rates: Exchange rates (fixed rates configured by property)
        """
        try:
            # Get hotel credentials
            credentials = await self.get_hotel_credentials(hotel_id)
            if not credentials.get("api_key"):
                return {
                    "success": False,
                    "error": "Cloudbeds API not configured for this hotel"
                }
            
            # Prepare request
            params = {
                "propertyID": credentials.get("property_id", "")
            }
            
            headers = {
                "Authorization": f"Bearer {credentials['api_key']}",
                "Content-Type": "application/json"
            }
            
            # Make API request
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/getCurrencySettings",
                    params=params,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("success"):
                        return {
                            "success": True,
                            "data": data.get("data", {})
                        }
                    else:
                        return {
                            "success": False,
                            "error": data.get("message", "Failed to get currency settings")
                        }
                else:
                    return {
                        "success": False,
                        "error": f"API error: HTTP {response.status_code}"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Error getting currency settings: {str(e)}"
            }