"""Configuration for AI evaluation tests."""

from typing import Dict, List, Any
from pydantic import BaseModel, Field
from datetime import datetime


class HotelConfig(BaseModel):
    """Configuration for a test hotel."""
    
    id: str
    name: str
    city: str
    country: str = "Spain"
    coordinates: tuple[float, float] = (40.4168, -3.7038)  # Default Madrid
    contact_email: str
    contact_phone: str
    description: str = ""
    facilities: List[str] = Field(default_factory=list)
    activities: List[Dict[str, Any]] = Field(default_factory=list)


class ConversationScenario(BaseModel):
    """Configuration for a conversation test scenario."""
    
    scenario_id: str
    hotel_id: str
    title: str
    description: str
    initial_message: str
    expected_tools: List[str] = Field(default_factory=list)
    conversation_flow: List[Dict[str, str]] = Field(default_factory=list)
    success_criteria: List[str] = Field(default_factory=list)
    difficulty_level: str = "medium"  # easy, medium, hard


class EvaluationCriteria(BaseModel):
    """Criteria for evaluating AI responses."""
    
    accuracy_weight: float = 0.3
    helpfulness_weight: float = 0.2
    tool_usage_weight: float = 0.2
    conversation_flow_weight: float = 0.15
    politeness_weight: float = 0.15
    minimum_passing_score: float = 0.75


# Test Hotels Configuration
TEST_HOTELS = [
    HotelConfig(
        id="hotel_madrid_luxury",
        name="Hotel Madrid Palace",
        city="Madrid",
        contact_email="reservas@madridpalace.es",
        contact_phone="+34 91 123 4567",
        description="Luxury 5-star hotel in the heart of Madrid",
        facilities=["spa", "gym", "pool", "restaurant", "bar", "concierge", "wifi", "parking"],
        activities=[
            {
                "title": "City Tour",
                "description": "Guided tour of Madrid's historic center",
                "price": 45.0,
                "duration_minutes": 180,
                "max_participants": 15
            },
            {
                "title": "Flamenco Show",
                "description": "Traditional Spanish flamenco performance with dinner",
                "price": 85.0,
                "duration_minutes": 120,
                "max_participants": 50
            }
        ]
    ),
    HotelConfig(
        id="hotel_barcelona_beach",
        name="Barcelona Beach Resort",
        city="Barcelona",
        coordinates=(41.3851, 2.1734),
        contact_email="info@barcelonabeach.com",
        contact_phone="+34 93 876 5432",
        description="Modern beachfront resort with stunning Mediterranean views",
        facilities=["beach_access", "spa", "pool", "restaurant", "bar", "wifi", "gym"],
        activities=[
            {
                "title": "Beach Volleyball",
                "description": "Fun beach volleyball games",
                "price": 0.0,
                "duration_minutes": 60,
                "max_participants": 12
            },
            {
                "title": "Sailing Experience",
                "description": "Half-day sailing trip along the coast",
                "price": 120.0,
                "duration_minutes": 240,
                "max_participants": 8
            }
        ]
    ),
    HotelConfig(
        id="hotel_sevilla_historic",
        name="Sevilla Heritage Hotel",
        city="Sevilla",
        coordinates=(37.3891, -5.9845),
        contact_email="contacto@sevillaheritage.es",
        contact_phone="+34 95 456 7890",
        description="Historic boutique hotel in Sevilla's old quarter",
        facilities=["patio", "restaurant", "bar", "wifi", "concierge"],
        activities=[
            {
                "title": "Cathedral Tour",
                "description": "Guided visit to Sevilla Cathedral and Giralda",
                "price": 25.0,
                "duration_minutes": 90,
                "max_participants": 20
            },
            {
                "title": "Tapas Walking Tour",
                "description": "Explore the best tapas bars in the historic center",
                "price": 55.0,
                "duration_minutes": 150,
                "max_participants": 12
            }
        ]
    )
]


# Test Scenarios Configuration
TEST_SCENARIOS = [
    ConversationScenario(
        scenario_id="basic_info_inquiry",
        hotel_id="hotel_madrid_luxury",
        title="Basic Hotel Information Inquiry",
        description="Guest asks for basic hotel information and amenities",
        initial_message="Hi! Can you tell me about your hotel and what amenities you have?",
        expected_tools=["get_hotel_info", "get_hotel_facilities"],
        conversation_flow=[
            {"role": "user", "content": "Hi! Can you tell me about your hotel and what amenities you have?"},
            {"role": "assistant", "content": "[Expected: Hotel info with amenities list]"},
            {"role": "user", "content": "That sounds great! Do you have a spa and fitness center?"},
            {"role": "assistant", "content": "[Expected: Specific facility details]"}
        ],
        success_criteria=[
            "Provides hotel name and description",
            "Lists main amenities and facilities",
            "Uses get_hotel_info tool",
            "Uses get_hotel_facilities tool",
            "Responds politely and professionally"
        ]
    ),
    ConversationScenario(
        scenario_id="availability_check",
        hotel_id="hotel_barcelona_beach",
        title="Room Availability Check",
        description="Guest inquires about room availability for specific dates",
        initial_message="I'm planning to visit Barcelona next month. Do you have any rooms available from March 15th to March 18th for 2 guests?",
        expected_tools=["check_room_availability"],
        conversation_flow=[
            {"role": "user", "content": "I'm planning to visit Barcelona next month. Do you have any rooms available from March 15th to March 18th for 2 guests?"},
            {"role": "assistant", "content": "[Expected: Availability check results]"},
            {"role": "user", "content": "What about prices? And do the rooms have sea views?"},
            {"role": "assistant", "content": "[Expected: Pricing and room details]"}
        ],
        success_criteria=[
            "Checks availability for correct dates",
            "Uses check_room_availability tool",
            "Provides pricing information",
            "Mentions room amenities",
            "Offers helpful booking guidance"
        ]
    ),
    ConversationScenario(
        scenario_id="weather_and_activities",
        hotel_id="hotel_sevilla_historic",
        title="Weather and Activity Planning",
        description="Guest asks about weather and local activities",
        initial_message="What's the weather like in Sevilla this week? I'm looking for some outdoor activities to do during my stay.",
        expected_tools=["get_local_weather", "get_hotel_activities"],
        conversation_flow=[
            {"role": "user", "content": "What's the weather like in Sevilla this week? I'm looking for some outdoor activities to do during my stay."},
            {"role": "assistant", "content": "[Expected: Weather info with activity recommendations]"},
            {"role": "user", "content": "Perfect! Can you book the cathedral tour for me?"},
            {"role": "assistant", "content": "[Expected: Booking guidance or service request]"}
        ],
        success_criteria=[
            "Provides current weather information",
            "Uses get_local_weather tool",
            "Lists available activities",
            "Uses get_hotel_activities tool",
            "Gives weather-appropriate activity advice"
        ]
    ),
    ConversationScenario(
        scenario_id="service_request",
        hotel_id="hotel_madrid_luxury",
        title="Hotel Service Request",
        description="Guest requests hotel services like housekeeping or room service",
        initial_message="Hi, I'm in room 315 and I need some extra towels. Also, could you arrange for late checkout tomorrow?",
        expected_tools=["request_hotel_service"],
        conversation_flow=[
            {"role": "user", "content": "Hi, I'm in room 315 and I need some extra towels. Also, could you arrange for late checkout tomorrow?"},
            {"role": "assistant", "content": "[Expected: Service requests processed]"},
            {"role": "user", "content": "Thank you! About what time can I expect the towels?"},
            {"role": "assistant", "content": "[Expected: Time estimate and confirmation]"}
        ],
        success_criteria=[
            "Processes multiple service requests",
            "Uses request_hotel_service tool",
            "Provides service confirmation",
            "Gives time estimates",
            "Professional service attitude"
        ]
    ),
    ConversationScenario(
        scenario_id="complex_multi_tool",
        hotel_id="hotel_barcelona_beach",
        title="Complex Multi-Tool Scenario",
        description="Guest asks for comprehensive assistance requiring multiple tools",
        initial_message="I'm arriving tomorrow for a 3-day stay. Can you check the weather, suggest activities, and tell me about your spa services? Also, I might need room service for breakfast.",
        expected_tools=["get_local_weather", "get_hotel_activities", "get_hotel_facilities", "request_hotel_service"],
        conversation_flow=[
            {"role": "user", "content": "I'm arriving tomorrow for a 3-day stay. Can you check the weather, suggest activities, and tell me about your spa services? Also, I might need room service for breakfast."},
            {"role": "assistant", "content": "[Expected: Comprehensive response covering all requests]"},
            {"role": "user", "content": "Great! The sailing experience sounds amazing. How do I book it?"},
            {"role": "assistant", "content": "[Expected: Booking assistance]"}
        ],
        success_criteria=[
            "Uses multiple tools appropriately",
            "Provides weather information",
            "Lists relevant activities",
            "Describes spa services",
            "Addresses room service inquiry",
            "Maintains conversational flow",
            "Prioritizes information effectively"
        ],
        difficulty_level="hard"
    )
]


# Evaluation configuration
EVALUATION_CONFIG = EvaluationCriteria()

# Available tools list for testing
AVAILABLE_TOOLS = [
    "get_hotel_info",
    "check_room_availability", 
    "get_hotel_activities",
    "get_hotel_facilities",
    "get_local_weather",
    "request_hotel_service"
]