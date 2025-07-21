"""Hotel-specific tools for OpenAI Agents."""

import asyncio
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from agents import function_tool, RunContextWrapper

from ..config import settings
from ..models import (
    RoomAvailability,
    AvailabilityResponse,
    ActivityInfo,
    FacilityInfo,
    HotelInfo,
)
from ..services.directus_service import directus_service


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

        # Fetch hotel information from Directus
        hotel_data = await directus_service.get_hotel_by_id(hotel_id)

        if not hotel_data:
            return f"Hotel with ID {hotel_id} not found."

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

        # Fetch activities from Directus
        activities = await directus_service.get_hotel_activities(hotel_id)

        if not activities:
            return "No activities found for this hotel."

        activities_text = "**Available Activities & Experiences**\n\n"

        for activity in activities:
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

        # Fetch facilities from Directus
        facilities = await directus_service.get_hotel_facilities(hotel_id)

        if not facilities:
            return "No facilities found for this hotel."

        facilities_text = "**Hotel Facilities & Amenities**\n\n"

        # Group facilities by category
        categories = {}
        for facility in facilities:
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


async def _get_hotel_coordinates(hotel_id: str) -> Optional[tuple[float, float, str]]:
    """Get hotel coordinates and city from hotel_id.
    
    Returns:
        Tuple of (latitude, longitude, city_name) or None if not found
    """
    try:
        # Get hotel coordinates from Directus
        hotel_data = await directus_service.get_hotel_coordinates(hotel_id)
        
        if not hotel_data:
            return None
        
        # If we have stored coordinates, use them
        if hotel_data.get("latitude") and hotel_data.get("longitude"):
            city = "Hotel Location"
            if hotel_data.get("address") and isinstance(hotel_data["address"], dict):
                city = hotel_data["address"].get("city", hotel_data.get("name", "Hotel Location"))
            
            return (
                float(hotel_data["latitude"]), 
                float(hotel_data["longitude"]), 
                city
            )
        
        # If no coordinates but we have an address, try to extract city
        if hotel_data.get("address") and isinstance(hotel_data["address"], dict):
            address = hotel_data["address"]
            city = address.get("city", hotel_data.get("name", "Hotel Location"))
            
            # For now, return some default coordinates for major cities
            # In a real implementation, you would use a geocoding service
            city_coordinates = {
                "madrid": (40.4168, -3.7038),
                "barcelona": (41.3851, 2.1734),
                "valencia": (39.4699, -0.3763),
                "sevilla": (37.3891, -5.9845),
                "bilbao": (43.2630, -2.9350),
                "málaga": (36.7213, -4.4217),
                "palma": (39.5696, 2.6502),
                "las palmas": (28.1248, -15.4300),
                "alicante": (38.3452, -0.4810),
                "córdoba": (37.8882, -4.7794),
                "valladolid": (41.6523, -4.7245),
                "vigo": (42.2406, -8.7207),
                "gijón": (43.5322, -5.6611),
                "hospitalet": (41.3598, 2.1074),
                "vitoria": (42.8467, -2.6716),
                "granada": (37.1773, -3.5986),
                "oviedo": (43.3614, -5.8593),
                "badalona": (41.4509, 2.2487),
                "cartagena": (37.6056, -0.9868),
                "terrassa": (41.5640, 2.0110),
                "jerez": (36.6868, -6.1362),
                "sabadell": (41.5431, 2.1090),
                "móstoles": (40.3217, -3.8647),
                "santa cruz": (28.4636, -16.2518),
                "pamplona": (42.8125, -1.6458),
                "almería": (36.8381, -2.4597),
                "fuenlabrada": (40.2842, -3.7938),
                "leganés": (40.3167, -3.7667),
                "donostia": (43.3183, -1.9812),
                "burgos": (42.3439, -3.6969),
                "albacete": (38.9942, -1.8564),
                "getafe": (40.3058, -3.7327),
                "castellón": (39.9864, -0.0513),
                "alcorcón": (40.3459, -3.8248),
                "logroño": (42.4627, -2.4449),
                "badajoz": (38.8794, -6.9706),
                "salamanca": (40.9651, -5.6640),
                "huelva": (37.2614, -6.9447),
                "marbella": (36.5108, -4.8850),
                "tarragona": (41.1189, 1.2445),
                "león": (42.6026, -5.5706),
                "cadiz": (36.5297, -6.2920),
                "dos hermanas": (37.2820, -5.9200),
                "parla": (40.2367, -3.7683),
                "torrejón": (40.4562, -3.4825),
                "alcalá": (40.4823, -3.3656),
                "reus": (41.1558, 1.1074),
                "ourense": (42.3397, -7.8642),
                "lugo": (43.0096, -7.5569),
                "santiago": (42.8805, -8.5456),
                "cáceres": (39.4753, -6.3724),
            }
            
            city_key = city.lower()
            if city_key in city_coordinates:
                lat, lon = city_coordinates[city_key]
                return (lat, lon, city)
        
        return None
        
    except Exception as e:
        print(f"Error getting hotel coordinates: {e}")
        return None


@function_tool
async def get_local_weather(
    ctx: RunContextWrapper[Any], 
    city: Optional[str] = None,
    hotel_id: Optional[str] = None,
    include_activity_advice: bool = True
) -> str:
    """Get current weather information for the hotel location using OpenMeteo API.

    Args:
        city: City name. If not provided, uses the hotel's location.
        hotel_id: The hotel ID. If not provided, uses the current hotel context.
        include_activity_advice: Whether to include activity recommendations based on weather.
    """
    try:
        from ..services.weather_service import weather_service
        
        # Use hotel_id from context if not provided
        if not hotel_id and hasattr(ctx.context, "hotel_id"):
            hotel_id = ctx.context.hotel_id

        # Try to get coordinates and city from hotel_id
        coordinates = None
        if hotel_id:
            coordinates = await _get_hotel_coordinates(hotel_id)
        
        # If we have coordinates, use OpenMeteo API
        if coordinates:
            latitude, longitude, city_name = coordinates
            
            async with weather_service as client:
                weather = await client.get_current_weather(latitude, longitude, city_name)
                
                # Format weather response
                response = f"**Current Weather in {weather.city}**\n\n"
                response += f"🌡️ **Temperature**: {weather.temperature:.1f}°C"
                
                if weather.temperature_min is not None and weather.temperature_max is not None:
                    response += f" (High: {weather.temperature_max:.1f}°C, Low: {weather.temperature_min:.1f}°C)"
                
                response += f"\n🌤️ **Conditions**: {weather.weather_description}"
                
                if weather.precipitation_probability:
                    response += f"\n🌧️ **Rain Chance**: {weather.precipitation_probability}%"
                
                if weather.humidity:
                    response += f"\n💧 **Humidity**: {weather.humidity}%"
                
                if weather.wind_speed:
                    response += f"\n💨 **Wind**: {weather.wind_speed:.1f} km/h"
                    if weather.wind_gusts and weather.wind_gusts > weather.wind_speed * 1.3:
                        response += f" (gusts up to {weather.wind_gusts:.1f} km/h)"
                
                if weather.cloud_cover:
                    response += f"\n☁️ **Cloud Cover**: {weather.cloud_cover}%"
                
                if weather.uv_index:
                    response += f"\n☀️ **UV Index**: {weather.uv_index:.1f}"
                    if weather.uv_index > 6:
                        response += " (High - use sun protection)"
                    elif weather.uv_index > 3:
                        response += " (Moderate)"
                
                # Add activity advice if requested
                if include_activity_advice:
                    advice = weather_service.get_activity_advice(weather)
                    
                    response += f"\n\n**🎯 Activity Recommendations**\n"
                    response += f"Overall suitability: {advice.outdoor_suitability.value.title()}\n"
                    response += f"Advice: {advice.advice}\n"
                    
                    if advice.recommended_activities:
                        response += f"\n✅ **Recommended**: {', '.join(advice.recommended_activities[:4])}"
                    
                    if advice.avoid_activities:
                        response += f"\n❌ **Avoid**: {', '.join(advice.avoid_activities[:3])}"
                    
                    response += f"\n\n👕 **Clothing**: {advice.clothing_advice}"
                
                return response
                
        else:
            # Fallback: try to get city from hotel if no coordinates
            if not city and hotel_id:
                try:
                    hotel_data = await directus_service.get_hotel_coordinates(hotel_id)
                    if hotel_data:
                        if hotel_data.get("address") and isinstance(hotel_data["address"], dict):
                            city = hotel_data["address"].get("city", hotel_data.get("name", "Hotel Location"))
                        else:
                            city = hotel_data.get("name", "Hotel Location")
                except Exception:
                    city = "Hotel Location"
            
            if not city:
                city = "Hotel Location"

            # Return fallback message when no coordinates available
            return f"""**Weather Information for {city}**

🌡️ Weather data is temporarily unavailable, but here are some general recommendations:

**🎯 Activity Planning Tips:**
• Check local weather apps for current conditions
• Indoor activities are always available (museums, shopping, spa)
• Hotel concierge can provide real-time weather updates
• Most outdoor activities in the area are enjoyable year-round

**👕 General Clothing Advice:**
• Dress in comfortable layers
• Bring a light jacket for evening
• Comfortable walking shoes recommended
• Sun protection for outdoor activities

For the most current weather conditions, please ask our concierge staff or check a local weather app."""

    except Exception as e:
        return f"Error retrieving weather information: {str(e)}"


@function_tool
async def request_hotel_service(
    ctx: RunContextWrapper[Any],
    service_type: str,
    description: str,
    room_number: Optional[str] = None,
    priority: str = "normal",
    hotel_id: Optional[str] = None,
) -> str:
    """Request a hotel service (housekeeping, room service, maintenance, etc.).

    Args:
        service_type: Type of service (housekeeping, room_service, maintenance, concierge, etc.)
        description: Detailed description of the service request
        room_number: Room number if applicable
        priority: Priority level (low, normal, high, urgent)
        hotel_id: The hotel ID. If not provided, uses the current hotel context.
    """
    try:
        # Use hotel_id from context if not provided
        if not hotel_id and hasattr(ctx.context, "hotel_id"):
            hotel_id = ctx.context.hotel_id

        # Generate a mock service request ID
        import uuid
        
        request_id = str(uuid.uuid4())[:8]

        # In a real implementation, this would create a service request in the PMS
        # and associate it with the specific hotel_id
        try:
            if hotel_id:
                # Store service request in database associated with hotel
                request_data = {
                    "id": request_id,
                    "hotel_id": hotel_id,
                    "service_type": service_type,
                    "description": description,
                    "room_number": room_number,
                    "priority": priority,
                    "status": "received",
                    "created_at": datetime.now().isoformat(),
                }
                
                # Save service request to Directus
                await directus_service.create_service_request(request_data)
        except Exception as e:
            print(f"Could not store service request in database: {e}")

        response = f"**Service Request Submitted**\n\n"
        response += f"Request ID: {request_id}\n"
        response += f"Service Type: {service_type.title()}\n"
        response += f"Description: {description}\n"

        if room_number:
            response += f"Room Number: {room_number}\n"

        if hotel_id:
            response += f"Hotel ID: {hotel_id}\n"

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
