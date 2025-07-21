"""Weather service using OpenMeteo API."""

import asyncio
import httpx
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from ..config import settings


class WeatherCode(Enum):
    """WMO Weather interpretation codes."""
    
    CLEAR_SKY = 0
    MAINLY_CLEAR = 1
    PARTLY_CLOUDY = 2
    OVERCAST = 3
    FOG = 45
    DEPOSITING_RIME_FOG = 48
    DRIZZLE_LIGHT = 51
    DRIZZLE_MODERATE = 53
    DRIZZLE_DENSE = 55
    FREEZING_DRIZZLE_LIGHT = 56
    FREEZING_DRIZZLE_DENSE = 57
    RAIN_SLIGHT = 61
    RAIN_MODERATE = 63
    RAIN_HEAVY = 65
    FREEZING_RAIN_LIGHT = 66
    FREEZING_RAIN_HEAVY = 67
    SNOW_SLIGHT = 71
    SNOW_MODERATE = 73
    SNOW_HEAVY = 75
    SNOW_GRAINS = 77
    RAIN_SHOWERS_SLIGHT = 80
    RAIN_SHOWERS_MODERATE = 81
    RAIN_SHOWERS_VIOLENT = 82
    SNOW_SHOWERS_SLIGHT = 85
    SNOW_SHOWERS_HEAVY = 86
    THUNDERSTORM = 95
    THUNDERSTORM_SLIGHT_HAIL = 96
    THUNDERSTORM_HEAVY_HAIL = 99


@dataclass
class WeatherConditions:
    """Weather conditions data structure."""
    
    temperature: float
    temperature_min: Optional[float] = None
    temperature_max: Optional[float] = None
    apparent_temperature: Optional[float] = None
    humidity: Optional[int] = None
    precipitation_probability: Optional[int] = None
    precipitation_amount: Optional[float] = None
    wind_speed: Optional[float] = None
    wind_direction: Optional[int] = None
    wind_gusts: Optional[float] = None
    weather_code: int = 0
    weather_description: str = "Clear sky"
    cloud_cover: Optional[int] = None
    uv_index: Optional[float] = None
    visibility: Optional[float] = None
    pressure: Optional[float] = None
    is_day: bool = True
    city: str = "Unknown Location"
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now(timezone.utc)


class ActivitySuitability(Enum):
    """Activity suitability based on weather conditions."""
    
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    UNSUITABLE = "unsuitable"


@dataclass
class ActivityWeatherAdvice:
    """Weather advice for activities."""
    
    outdoor_suitability: ActivitySuitability
    indoor_recommendation: bool
    advice: str
    recommended_activities: list[str]
    avoid_activities: list[str]
    clothing_advice: str


class OpenMeteoClient:
    """Client for OpenMeteo weather API."""
    
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    TIMEOUT = 10.0
    
    # Weather code descriptions
    WEATHER_DESCRIPTIONS = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail"
    }
    
    def __init__(self):
        self.client = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.client = httpx.AsyncClient(timeout=self.TIMEOUT)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()
    
    async def get_current_weather(
        self, 
        latitude: float, 
        longitude: float,
        city: str = "Unknown Location"
    ) -> WeatherConditions:
        """Get current weather conditions."""
        try:
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "current": [
                    "temperature_2m",
                    "apparent_temperature", 
                    "relative_humidity_2m",
                    "is_day",
                    "precipitation",
                    "weather_code",
                    "cloud_cover",
                    "pressure_msl",
                    "wind_speed_10m",
                    "wind_direction_10m",
                    "wind_gusts_10m"
                ],
                "daily": [
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_probability_max",
                    "uv_index_max"
                ],
                "timezone": "auto",
                "forecast_days": 1
            }
            
            if not self.client:
                self.client = httpx.AsyncClient(timeout=self.TIMEOUT)
            
            response = await self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Extract current weather
            current = data.get("current", {})
            daily = data.get("daily", {})
            
            weather_code = current.get("weather_code", 0)
            
            return WeatherConditions(
                temperature=current.get("temperature_2m", 20.0),
                temperature_min=daily.get("temperature_2m_min", [None])[0],
                temperature_max=daily.get("temperature_2m_max", [None])[0],
                apparent_temperature=current.get("apparent_temperature"),
                humidity=current.get("relative_humidity_2m"),
                precipitation_probability=daily.get("precipitation_probability_max", [None])[0],
                precipitation_amount=current.get("precipitation", 0.0),
                wind_speed=current.get("wind_speed_10m"),
                wind_direction=current.get("wind_direction_10m"),
                wind_gusts=current.get("wind_gusts_10m"),
                weather_code=weather_code,
                weather_description=self.WEATHER_DESCRIPTIONS.get(weather_code, "Unknown"),
                cloud_cover=current.get("cloud_cover"),
                uv_index=daily.get("uv_index_max", [None])[0],
                pressure=current.get("pressure_msl"),
                is_day=bool(current.get("is_day", 1)),
                city=city
            )
            
        except Exception as e:
            print(f"Error fetching weather from OpenMeteo: {e}")
            # Return fallback weather data
            return WeatherConditions(
                temperature=20.0,
                weather_description="Weather data unavailable",
                city=city
            )
    
    def get_activity_advice(self, weather: WeatherConditions) -> ActivityWeatherAdvice:
        """Get activity recommendations based on weather conditions."""
        
        # Determine outdoor suitability
        outdoor_suitability = self._assess_outdoor_suitability(weather)
        
        # Generate recommendations
        recommended_activities = self._get_recommended_activities(weather)
        avoid_activities = self._get_activities_to_avoid(weather)
        clothing_advice = self._get_clothing_advice(weather)
        advice = self._generate_general_advice(weather, outdoor_suitability)
        
        return ActivityWeatherAdvice(
            outdoor_suitability=outdoor_suitability,
            indoor_recommendation=outdoor_suitability in [
                ActivitySuitability.POOR, 
                ActivitySuitability.UNSUITABLE
            ],
            advice=advice,
            recommended_activities=recommended_activities,
            avoid_activities=avoid_activities,
            clothing_advice=clothing_advice
        )
    
    def _assess_outdoor_suitability(self, weather: WeatherConditions) -> ActivitySuitability:
        """Assess how suitable the weather is for outdoor activities."""
        
        # Heavy precipitation
        if weather.precipitation_amount and weather.precipitation_amount > 5.0:
            return ActivitySuitability.UNSUITABLE
        
        # Thunderstorms
        if weather.weather_code in [95, 96, 99]:
            return ActivitySuitability.UNSUITABLE
        
        # Heavy rain or snow
        if weather.weather_code in [65, 67, 75, 82, 86]:
            return ActivitySuitability.POOR
        
        # Light to moderate rain or snow
        if weather.weather_code in [61, 63, 71, 73, 80, 81, 85]:
            return ActivitySuitability.FAIR
        
        # Extreme temperatures
        if weather.temperature < -5 or weather.temperature > 38:
            return ActivitySuitability.POOR
        
        # Very high wind speeds
        if weather.wind_speed and weather.wind_speed > 25:
            return ActivitySuitability.FAIR
        
        # High precipitation probability
        if weather.precipitation_probability and weather.precipitation_probability > 70:
            return ActivitySuitability.FAIR
        
        # Clear or partly cloudy conditions
        if weather.weather_code in [0, 1, 2]:
            return ActivitySuitability.EXCELLENT
        
        # Default to good for other conditions
        return ActivitySuitability.GOOD
    
    def _get_recommended_activities(self, weather: WeatherConditions) -> list[str]:
        """Get recommended activities based on weather."""
        activities = []
        
        # Sunny and warm
        if weather.weather_code in [0, 1] and weather.temperature > 18:
            activities.extend([
                "Beach activities", "Swimming", "Sightseeing tours", 
                "Outdoor dining", "Walking tours", "Photography"
            ])
        
        # Partly cloudy, good for most outdoor activities
        if weather.weather_code in [1, 2] and weather.temperature > 10:
            activities.extend([
                "City walks", "Museum visits", "Shopping", 
                "Hiking", "Outdoor markets"
            ])
        
        # Cold but clear
        if weather.weather_code in [0, 1, 2] and weather.temperature < 10:
            activities.extend([
                "Hot drinks at cafes", "Indoor attractions", 
                "Shopping malls", "Cultural sites"
            ])
        
        # Rainy weather
        if weather.weather_code in range(51, 90):
            activities.extend([
                "Spa treatments", "Indoor museums", "Shopping centers",
                "Restaurant experiences", "Cooking classes", "Wellness activities"
            ])
        
        # Snow
        if weather.weather_code in [71, 73, 75, 77, 85, 86]:
            activities.extend([
                "Winter sports", "Hot springs", "Cozy restaurants",
                "Indoor entertainment", "Warm beverages"
            ])
        
        return activities[:6]  # Limit to 6 suggestions
    
    def _get_activities_to_avoid(self, weather: WeatherConditions) -> list[str]:
        """Get activities to avoid based on weather."""
        avoid = []
        
        # Heavy rain/storms
        if weather.weather_code in [65, 67, 82, 95, 96, 99]:
            avoid.extend(["Beach activities", "Outdoor dining", "Hiking", "Walking tours"])
        
        # Snow/freezing conditions
        if weather.weather_code in [71, 73, 75, 77, 85, 86] or weather.temperature < 0:
            avoid.extend(["Swimming", "Beach activities", "Long outdoor walks"])
        
        # High wind
        if weather.wind_speed and weather.wind_speed > 20:
            avoid.extend(["Boat trips", "Outdoor dining", "Beach umbrellas"])
        
        # Extreme heat
        if weather.temperature > 35:
            avoid.extend(["Intensive outdoor activities", "Long hikes", "Midday sightseeing"])
        
        return avoid[:4]  # Limit to 4 suggestions
    
    def _get_clothing_advice(self, weather: WeatherConditions) -> str:
        """Get clothing recommendations based on weather."""
        advice_parts = []
        
        # Temperature-based advice
        if weather.temperature < 5:
            advice_parts.append("Wear warm layers, winter coat, gloves, and hat")
        elif weather.temperature < 15:
            advice_parts.append("Dress in layers with a jacket or sweater")
        elif weather.temperature < 25:
            advice_parts.append("Light jacket or sweater for comfort")
        else:
            advice_parts.append("Light, breathable clothing recommended")
        
        # Precipitation advice
        if weather.precipitation_probability and weather.precipitation_probability > 50:
            advice_parts.append("Bring waterproof jacket and umbrella")
        
        # Wind advice
        if weather.wind_speed and weather.wind_speed > 15:
            advice_parts.append("Windproof outer layer recommended")
        
        # Sun protection
        if weather.uv_index and weather.uv_index > 6:
            advice_parts.append("Sunscreen and hat for UV protection")
        
        return ". ".join(advice_parts) + "."
    
    def _generate_general_advice(
        self, 
        weather: WeatherConditions, 
        suitability: ActivitySuitability
    ) -> str:
        """Generate general weather advice."""
        
        if suitability == ActivitySuitability.EXCELLENT:
            return "Perfect weather for outdoor activities! Great time to explore."
        
        elif suitability == ActivitySuitability.GOOD:
            return "Good weather conditions with comfortable temperatures."
        
        elif suitability == ActivitySuitability.FAIR:
            advice = "Weather is acceptable for outdoor activities with some caution. "
            if weather.precipitation_probability and weather.precipitation_probability > 50:
                advice += "Watch for possible rain. "
            if weather.wind_speed and weather.wind_speed > 15:
                advice += "Be prepared for windy conditions. "
            return advice.strip()
        
        elif suitability == ActivitySuitability.POOR:
            return "Weather conditions are challenging. Indoor activities recommended."
        
        else:  # UNSUITABLE
            return "Weather conditions are not suitable for outdoor activities. Stay indoors and enjoy indoor attractions."


# Global weather service instance
weather_service = OpenMeteoClient()