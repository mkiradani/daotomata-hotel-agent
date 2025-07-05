"""Hotel-specific tools for OpenAI Agents."""

import asyncio
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from agents import function_tool, RunContextWrapper
from supabase import create_client, Client

from ..config import settings
from ..models import (
    RoomAvailability,
    AvailabilityResponse,
    ActivityInfo,
    FacilityInfo,
    HotelInfo,
)


# Initialize Supabase client
supabase: Client = create_client(settings.supabase_url, settings.supabase_key)


@function_tool
async def get_hotel_info(
    ctx: RunContextWrapper[Any], hotel_id: Optional[str] = None
) -> str:
    """Get information about the hotel including amenities, policies, and contact details.

    Args:
        hotel_id: The hotel ID. If not provided, uses the current hotel context.
    """
    try:
        # Use hotel_id from context if not provided
        if not hotel_id and hasattr(ctx.context, "hotel_id"):
            hotel_id = ctx.context.hotel_id

        if not hotel_id:
            return "Hotel ID not available in context."

        # Fetch hotel information from Supabase
        response = supabase.table("hotels").select("*").eq("id", hotel_id).execute()

        if not response.data:
            return f"Hotel with ID {hotel_id} not found."

        hotel_data = response.data[0]

        # Format hotel information
        info = f"**{hotel_data['name']}**\n\n"

        if hotel_data.get("description"):
            info += f"Description: {hotel_data['description']}\n\n"

        if hotel_data.get("address"):
            address = hotel_data["address"]
            info += f"Address: {address.get('street', '')}, {address.get('city', '')}, {address.get('country', '')}\n\n"

        if hotel_data.get("contact_email"):
            info += f"Email: {hotel_data['contact_email']}\n"

        if hotel_data.get("contact_phone"):
            info += f"Phone: {hotel_data['contact_phone']}\n\n"

        return info

    except Exception as e:
        return f"Error retrieving hotel information: {str(e)}"


@function_tool
async def check_room_availability(
    ctx: RunContextWrapper[Any],
    check_in: str,
    check_out: str,
    guests: int = 2,
    hotel_id: Optional[str] = None,
) -> str:
    """Check room availability for given dates.

    Args:
        check_in: Check-in date in YYYY-MM-DD format
        check_out: Check-out date in YYYY-MM-DD format
        guests: Number of guests (default: 2)
        hotel_id: The hotel ID. If not provided, uses the current hotel context.
    """
    try:
        # Parse dates
        check_in_date = datetime.strptime(check_in, "%Y-%m-%d").date()
        check_out_date = datetime.strptime(check_out, "%Y-%m-%d").date()

        # Validate dates
        if check_in_date <= date.today():
            return "Check-in date must be in the future."

        if check_out_date <= check_in_date:
            return "Check-out date must be after check-in date."

        nights = (check_out_date - check_in_date).days

        # Use hotel_id from context if not provided
        if not hotel_id and hasattr(ctx.context, "hotel_id"):
            hotel_id = ctx.context.hotel_id

        # Mock room availability (in real implementation, this would check PMS)
        available_rooms = [
            {
                "room_type": "Standard Room",
                "available": True,
                "price_per_night": 120.0,
                "total_price": 120.0 * nights,
                "amenities": ["WiFi", "Air Conditioning", "TV", "Private Bathroom"],
            },
            {
                "room_type": "Deluxe Room",
                "available": True,
                "price_per_night": 180.0,
                "total_price": 180.0 * nights,
                "amenities": [
                    "WiFi",
                    "Air Conditioning",
                    "TV",
                    "Private Bathroom",
                    "Balcony",
                    "Mini Bar",
                ],
            },
            {
                "room_type": "Suite",
                "available": guests <= 4,
                "price_per_night": 350.0,
                "total_price": 350.0 * nights,
                "amenities": [
                    "WiFi",
                    "Air Conditioning",
                    "TV",
                    "Private Bathroom",
                    "Balcony",
                    "Mini Bar",
                    "Living Area",
                    "Kitchen",
                ],
            },
        ]

        # Format response
        response = f"**Room Availability**\n"
        response += f"Check-in: {check_in}\n"
        response += f"Check-out: {check_out}\n"
        response += f"Nights: {nights}\n"
        response += f"Guests: {guests}\n\n"

        for room in available_rooms:
            status = "✅ Available" if room["available"] else "❌ Not Available"
            response += f"**{room['room_type']}** - {status}\n"
            if room["available"]:
                response += f"Price: €{room['price_per_night']}/night (Total: €{room['total_price']})\n"
                response += f"Amenities: {', '.join(room['amenities'])}\n"
            response += "\n"

        return response

    except ValueError:
        return "Invalid date format. Please use YYYY-MM-DD format."
    except Exception as e:
        return f"Error checking availability: {str(e)}"


@function_tool
async def get_hotel_activities(
    ctx: RunContextWrapper[Any], hotel_id: Optional[str] = None
) -> str:
    """Get list of available hotel activities and experiences.

    Args:
        hotel_id: The hotel ID. If not provided, uses the current hotel context.
    """
    try:
        # Use hotel_id from context if not provided
        if not hotel_id and hasattr(ctx.context, "hotel_id"):
            hotel_id = ctx.context.hotel_id

        if not hotel_id:
            return "Hotel ID not available in context."

        # Fetch activities from Supabase
        response = (
            supabase.table("activities")
            .select("*")
            .eq("hotel_id", hotel_id)
            .eq("is_active", True)
            .execute()
        )

        if not response.data:
            return "No activities found for this hotel."

        activities_text = "**Available Activities & Experiences**\n\n"

        for activity in response.data:
            activities_text += f"**{activity['title']}**\n"

            if activity.get("description"):
                activities_text += f"{activity['description']}\n"

            if activity.get("price"):
                currency = activity.get("currency", "EUR")
                activities_text += f"Price: {currency} {activity['price']}\n"

            if activity.get("duration_minutes"):
                hours = activity["duration_minutes"] // 60
                minutes = activity["duration_minutes"] % 60
                duration = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
                activities_text += f"Duration: {duration}\n"

            if activity.get("max_participants"):
                activities_text += f"Max participants: {activity['max_participants']}\n"

            activities_text += "\n"

        return activities_text

    except Exception as e:
        return f"Error retrieving activities: {str(e)}"


@function_tool
async def get_hotel_facilities(
    ctx: RunContextWrapper[Any], hotel_id: Optional[str] = None
) -> str:
    """Get list of hotel facilities and amenities.

    Args:
        hotel_id: The hotel ID. If not provided, uses the current hotel context.
    """
    try:
        # Use hotel_id from context if not provided
        if not hotel_id and hasattr(ctx.context, "hotel_id"):
            hotel_id = ctx.context.hotel_id

        if not hotel_id:
            return "Hotel ID not available in context."

        # Fetch facilities from Supabase
        response = (
            supabase.table("facilities")
            .select("*")
            .eq("hotel_id", hotel_id)
            .eq("is_active", True)
            .execute()
        )

        if not response.data:
            return "No facilities found for this hotel."

        facilities_text = "**Hotel Facilities & Amenities**\n\n"

        # Group facilities by category
        categories = {}
        for facility in response.data:
            category = facility.get("category", "General")
            if category not in categories:
                categories[category] = []
            categories[category].append(facility)

        for category, facilities in categories.items():
            facilities_text += f"**{category}**\n"
            for facility in facilities:
                facilities_text += f"• {facility['name']}"
                if facility.get("description"):
                    facilities_text += f" - {facility['description']}"
                facilities_text += "\n"
            facilities_text += "\n"

        return facilities_text

    except Exception as e:
        return f"Error retrieving facilities: {str(e)}"


@function_tool
async def get_local_weather(
    ctx: RunContextWrapper[Any], city: Optional[str] = None
) -> str:
    """Get current weather information for the hotel location.

    Args:
        city: City name. If not provided, uses the hotel's location.
    """
    try:
        # In a real implementation, this would call a weather API
        # For now, return mock weather data
        if not city:
            city = "Hotel Location"

        import random

        weather_conditions = ["sunny", "partly cloudy", "cloudy", "light rain", "clear"]
        temperature = random.randint(15, 28)
        condition = random.choice(weather_conditions)

        return f"**Current Weather in {city}**\n\nTemperature: {temperature}°C\nCondition: {condition.title()}\nHumidity: {random.randint(40, 80)}%\nWind: {random.randint(5, 20)} km/h"

    except Exception as e:
        return f"Error retrieving weather information: {str(e)}"


@function_tool
async def request_hotel_service(
    ctx: RunContextWrapper[Any],
    service_type: str,
    description: str,
    room_number: Optional[str] = None,
    priority: str = "normal",
) -> str:
    """Request a hotel service (housekeeping, room service, maintenance, etc.).

    Args:
        service_type: Type of service (housekeeping, room_service, maintenance, concierge, etc.)
        description: Detailed description of the service request
        room_number: Room number if applicable
        priority: Priority level (low, normal, high, urgent)
    """
    try:
        # Generate a mock service request ID
        import uuid

        request_id = str(uuid.uuid4())[:8]

        # In a real implementation, this would create a service request in the PMS
        response = f"**Service Request Submitted**\n\n"
        response += f"Request ID: {request_id}\n"
        response += f"Service Type: {service_type.title()}\n"
        response += f"Description: {description}\n"

        if room_number:
            response += f"Room Number: {room_number}\n"

        response += f"Priority: {priority.title()}\n"
        response += f"Status: Received\n"

        # Estimate completion time based on service type
        if service_type.lower() in ["housekeeping", "maintenance"]:
            response += f"Estimated completion: Within 2-4 hours\n"
        elif service_type.lower() == "room_service":
            response += f"Estimated completion: Within 30-45 minutes\n"
        else:
            response += f"Estimated completion: Within 1-2 hours\n"

        response += "\nYou will be notified when the service is completed. Thank you!"

        return response

    except Exception as e:
        return f"Error submitting service request: {str(e)}"
