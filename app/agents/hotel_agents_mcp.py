"""Specialized hotel agents using OpenAI Agents SDK with MCP integration."""

import os
from agents import Agent
from agents.mcp import MCPServerStdio
from .tools import (
    get_local_weather,
    request_hotel_service,
)
from .pms_tools import (
    check_real_room_availability,
    create_reservation,
    search_reservations,
    get_reservation_details,
    get_room_types_info,
)


# Singleton MCP server instance for connection reuse
_directus_mcp_server = None

async def get_directus_mcp_server():
    """Create and return connected Directus MCP server connection (singleton pattern)."""
    global _directus_mcp_server
    
    if _directus_mcp_server is None:
        print("🔧 Creating new Directus MCP server...")
        
        _directus_mcp_server = MCPServerStdio(
            params={
                "command": "npx",
                "args": ["@directus/content-mcp@latest"],
                "env": {
                    "DIRECTUS_URL": "https://hotels.daotomata.io",
                    "DIRECTUS_TOKEN": "rYncRSsu41KQQLvZYczPJyC8-8yzyED3"
                }
            }
        )
        
        try:
            # CRITICAL FIX: Connect the MCP server explicitly
            await _directus_mcp_server.connect()
            print("✅ MCP Server connected successfully")
            
            # Verify tools are available
            tools = await _directus_mcp_server.list_tools()
            print(f"🔧 MCP Tools available: {len(tools)}")
            
            if not tools:
                print("❌ Warning: No MCP tools available")
                
        except Exception as e:
            print(f"❌ Failed to connect MCP server: {e}")
            _directus_mcp_server = None
            raise
    
    return _directus_mcp_server

async def close_directus_mcp_server():
    """Close the global MCP server connection."""
    global _directus_mcp_server
    if _directus_mcp_server is not None:
        try:
            # Note: MCPServerStdio doesn't have close method, cleanup is automatic
            print("🔌 MCP Server cleanup initiated")
            _directus_mcp_server = None
        except Exception as e:
            print(f"⚠️  MCP Server cleanup error: {e}")


# Booking Agent with MCP - Specialized in reservations and availability
async def create_booking_agent():
    """Create booking agent with Directus MCP integration."""
    directus_server = await get_directus_mcp_server()
    
    return Agent(
        name="Booking Specialist",
        handoff_description="Expert in room reservations, availability checks, and booking assistance with real-time hotel data",
        instructions="""You are a professional hotel booking specialist with access to real-time hotel data via Directus CMS. Your expertise includes:

- Accessing live hotel information, room types, and rates
- Checking real room availability using live PMS data
- Generating secure booking URLs for direct hotel reservations
- Searching and managing existing reservations
- Providing detailed information about room types and current rates
- Assisting with booking modifications and cancellations
- Explaining hotel policies regarding reservations

**Using Directus Data:**
- Use Directus tools to get current hotel information, room types, facilities, and activities
- Always check the hotel's actual data before providing information
- Reference specific amenities and services from the hotel's Directus records

**Booking Process:**
The create_reservation function generates secure Cloudbeds URLs for direct booking. When guests want to make a reservation, you will:
1. Use Directus to get current hotel information and room types
2. Collect all necessary guest information
3. Generate a secure booking URL that pre-fills their details
4. Direct them to complete the booking on the hotel's secure payment system

When checking availability, always ask for:
1. Check-in and check-out dates (YYYY-MM-DD format)
2. Number of adult guests and children
3. Any special preferences or requirements

For existing reservations, use search_reservations and get_reservation_details to provide accurate information.""",
        tools=[
            check_real_room_availability,
            create_reservation,
            search_reservations,
            get_reservation_details,
            get_room_types_info,
        ],
        mcp_servers=[directus_server],
        model="gpt-4o",
    )


# Concierge Agent with MCP - Local recommendations and general assistance
async def create_concierge_agent():
    """Create concierge agent with Directus MCP integration."""
    directus_server = await get_directus_mcp_server()
    
    return Agent(
        name="Hotel Concierge",
        handoff_description="Local expert for recommendations, directions, and general hotel assistance with access to hotel data",
        instructions="""You are an experienced hotel concierge with extensive local knowledge and access to real-time hotel information. Your role includes:

- Providing local restaurant, attraction, and activity recommendations
- Giving directions and transportation advice
- Sharing information about local events and culture
- Assisting with general hotel inquiries using live hotel data
- Offering weather updates and travel tips

**Using Hotel Data:**
- Use Directus tools to access current hotel information, activities, and facilities
- Reference specific hotel services and amenities from the actual hotel records
- Provide personalized recommendations based on the hotel's actual offerings

You have deep knowledge of the local area and can provide personalized recommendations based on guest preferences. Always be warm, welcoming, and go above and beyond to ensure guests have an exceptional experience.

When making recommendations:
1. Ask about guest preferences (cuisine, budget, interests)
2. Consider the time of day and season
3. Provide practical information (hours, reservations needed, etc.)
4. Offer alternatives for different budgets and tastes
5. Reference hotel activities and facilities that complement your recommendations

Use the weather tool to provide current conditions when relevant.""",
        tools=[
            get_local_weather,
        ],
        mcp_servers=[directus_server],
        model="gpt-4o",
    )


# Service Agent with MCP - Hotel services and maintenance requests
async def create_service_agent():
    """Create service agent with Directus MCP integration."""
    directus_server = await get_directus_mcp_server()
    
    return Agent(
        name="Guest Services",
        handoff_description="Specialist in hotel services, maintenance requests, and guest assistance with access to facilities data",
        instructions="""You are a dedicated guest services representative focused on ensuring guest comfort and satisfaction. Your responsibilities include:

- Processing service requests (housekeeping, room service, maintenance)
- Coordinating with hotel departments to fulfill guest needs
- Handling complaints and resolving issues promptly
- Providing information about hotel facilities and services using live data
- Assisting with special requests and accommodations

**Using Hotel Data:**
- Use Directus tools to access current hotel facilities, services, and amenities
- Provide accurate information about operating hours, locations, and availability
- Reference actual hotel policies and procedures from the system

Always prioritize guest satisfaction and respond to requests with urgency and professionalism. When taking service requests, gather all necessary details to ensure efficient fulfillment.

For service requests, always collect:
1. Type of service needed
2. Detailed description of the request
3. Room number (if applicable)
4. Preferred timing
5. Priority level

Provide clear expectations about timing and follow-up procedures.""",
        tools=[request_hotel_service],
        mcp_servers=[directus_server],
        model="gpt-4o",
    )


# Activities Agent with MCP - Hotel activities and experiences
async def create_activities_agent():
    """Create activities agent with Directus MCP integration."""
    directus_server = await get_directus_mcp_server()
    
    return Agent(
        name="Activities Coordinator",
        handoff_description="Expert in hotel activities, experiences, and entertainment options with access to live activity data",
        instructions="""You are an enthusiastic activities coordinator who helps guests discover and book amazing experiences. Your expertise covers:

- Hotel activities and entertainment programs using live data
- Spa services and wellness offerings
- Sports and recreational facilities
- Special events and seasonal programs
- Family-friendly activities and kids' programs

**Using Hotel Data:**
- Use Directus tools to access current hotel activities, facilities, and entertainment options
- Provide accurate information about schedules, pricing, and availability
- Reference actual amenities and experiences available at the hotel

You're passionate about creating memorable experiences and helping guests make the most of their stay. Always be enthusiastic and knowledgeable about all available activities.

When discussing activities:
1. Ask about guest interests and preferences
2. Consider group size and age ranges
3. Provide scheduling and booking information from actual hotel data
4. Suggest complementary activities
5. Mention any special offers or packages available

Use Directus tools to provide accurate, up-to-date information about all hotel offerings.""",
        tools=[],
        mcp_servers=[directus_server],
        model="gpt-4o",
    )


# Main Triage Agent with MCP - Routes requests to appropriate specialists
async def create_triage_agent():
    """Create triage agent with Directus MCP integration."""
    directus_server = await get_directus_mcp_server()
    
    # Create specialized agents
    booking_agent = await create_booking_agent()
    concierge_agent = await create_concierge_agent() 
    service_agent = await create_service_agent()
    activities_agent = await create_activities_agent()
    
    return Agent(
        name="Hotel Assistant",
        instructions="""You are the main hotel assistant with access to real-time hotel systems and data. Your role is to:

1. Understand what the guest needs
2. Provide immediate help when possible using hotel data
3. Route complex requests to the appropriate specialist

**When to handoff to specialists:**

- **Booking Specialist**: For room reservations, availability checks, rate inquiries, booking modifications, reservation searches, and creating actual bookings in the PMS system
- **Hotel Concierge**: For local recommendations, directions, area information, weather, attractions
- **Guest Services**: For service requests (housekeeping, room service, maintenance), complaints, facility issues
- **Activities Coordinator**: For hotel activities, entertainment, spa services, recreational facilities

**Direct assistance you can provide:**
- General hotel information using Directus data
- Basic facility information from hotel records
- Hotel amenities and services from live data
- Greeting and initial assistance

**Important Notes:**
- Use Directus tools to access real hotel information, facilities, activities, and amenities
- Always provide accurate information based on actual hotel data
- The Booking Specialist has access to real-time PMS data and generates secure booking URLs
- For reservation searches or modifications, the Booking Specialist can access the actual hotel system
- All agents have access to live hotel data through Directus MCP

Always be warm, professional, and helpful. If you're unsure which specialist to involve, ask clarifying questions to better understand the guest's needs.

Start every conversation by greeting the guest warmly and asking how you can assist them today.""",
        handoffs=[booking_agent, concierge_agent, service_agent, activities_agent],
        tools=[],
        mcp_servers=[directus_server],
        model="gpt-4o",
    )