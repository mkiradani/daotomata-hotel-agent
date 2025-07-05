# 🤖 Daotomata Hotel Agent - AI Concierge Service

A sophisticated AI concierge system for hotels built with OpenAI Agents SDK and FastAPI. This service provides specialized agents for different hotel operations including booking, concierge services, guest services, and activities coordination.

> **Note**: This repository was extracted from the main [dao-hotel monorepo](https://github.com/mkiradani/dao-hotel) to create a standalone, focused service for the hotel AI agent functionality.

## 🏆 Features

- **Multi-Agent Architecture**: Intelligent triage system with specialized agents
- **OpenAI Integration**: Powered by GPT-4o for natural conversations
- **Multi-Tenant Support**: Designed for multiple hotel properties
- **Real-time Communication**: Fast, async API responses
- **Extensible Tools**: Custom tools for hotel operations

## 🏗️ Architecture

### Multi-Agent System

The bot uses a **triage agent** that routes conversations to specialized agents:

- **🏨 Booking Specialist**: Room reservations, availability checks, rate inquiries
- **🗺️ Hotel Concierge**: Local recommendations, directions, area information  
- **🛎️ Guest Services**: Hotel services, maintenance requests, complaint resolution
- **🎯 Activities Coordinator**: Hotel activities, entertainment, spa services

### Technology Stack

- **OpenAI Agents SDK**: Multi-agent conversation management
- **FastAPI**: High-performance async API framework
- **Supabase**: Multi-tenant database with RLS
- **Pydantic**: Data validation and serialization
- **Redis**: Session management and caching (optional)

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key
- Supabase project credentials

### Environment Setup

1. **Create environment file**:
```bash
cp .env.example .env
```

2. **Configure environment variables**:
```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o

# Supabase Configuration  
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key

# Security
SECRET_KEY=your_secret_key

# Hotel Context (optional)
CURRENT_DOMAIN=demo.daotomata.com
```

### Installation

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Run the development server**:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Docker Deployment

1. **Build the image**:
```bash
docker build -t hotel-bot .
```

2. **Run the container**:
```bash
docker run -p 8000:8000 --env-file .env hotel-bot
```

## 📚 API Documentation

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Core Endpoints

#### Chat API

```http
POST /api/chat/
```

Process a chat message with the AI concierge:

```json
{
  "message": "I'd like to book a room for next weekend",
  "session_id": "optional-session-id",
  "hotel_id": "optional-hotel-id",
  "user_context": {}
}
```

Response:
```json
{
  "message": "I'd be happy to help you book a room! Let me check availability...",
  "session_id": "generated-session-id",
  "agent_used": "booking_specialist",
  "tools_used": ["check_room_availability"],
  "handoff_occurred": true
}
```

#### Hotel Information

```http
GET /api/hotel/info
GET /api/hotel/activities  
GET /api/hotel/facilities
POST /api/hotel/availability
POST /api/hotel/service-request
```

## 🤖 Agent Capabilities

### Booking Specialist

**Capabilities**:
- Check room availability for specific dates
- Provide room type information and amenities
- Assist with booking modifications
- Explain hotel policies

**Tools**:
- `check_room_availability`
- `get_hotel_info`

### Hotel Concierge

**Capabilities**:
- Local restaurant and attraction recommendations
- Transportation and directions
- Weather information
- Cultural insights and events

**Tools**:
- `get_local_weather`
- `get_hotel_info`
- `get_hotel_activities`
- `get_hotel_facilities`

### Guest Services

**Capabilities**:
- Process service requests (housekeeping, room service, maintenance)
- Handle complaints and issues
- Coordinate with hotel departments
- Provide facility information

**Tools**:
- `request_hotel_service`
- `get_hotel_facilities`
- `get_hotel_info`

### Activities Coordinator

**Capabilities**:
- Hotel activities and entertainment
- Spa and wellness services
- Sports and recreational facilities
- Event planning assistance

**Tools**:
- `get_hotel_activities`
- `get_hotel_facilities`
- `get_hotel_info`

## 🔧 Configuration

### Agent Customization

Agents can be customized by modifying `app/agents/hotel_agents.py`:

```python
booking_agent = Agent(
    name="Booking Specialist",
    instructions="Your custom instructions...",
    tools=[check_room_availability, get_hotel_info],
    model="gpt-4o"
)
```

### Tool Development

Create custom tools in `app/agents/tools.py`:

```python
@function_tool
async def custom_tool(ctx: RunContextWrapper[Any], param: str) -> str:
    """Custom tool description."""
    # Tool implementation
    return "Tool result"
```

### Multi-Tenant Support

The system automatically detects the hotel context from:
1. `hotel_id` parameter in requests
2. `CURRENT_DOMAIN` environment variable
3. Domain-based detection from Supabase

## 🧪 Testing

### Manual Testing

Use the test endpoint:
```http
POST /api/chat/test
```

### Integration Testing

```bash
# Test chat functionality
curl -X POST "http://localhost:8000/api/chat/" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, can you help me?"}'

# Test hotel info
curl "http://localhost:8000/api/hotel/info"
```

## 📊 Monitoring

### Health Checks

```http
GET /health
```

Returns:
```json
{
  "status": "healthy",
  "service": "hotel-bot", 
  "version": "1.0.0",
  "openai_model": "gpt-4o",
  "current_domain": "demo.daotomata.com"
}
```

### Logging

The application logs important events and errors. In production, configure structured logging and monitoring.

## 🔒 Security

### Best Practices

- API keys stored in environment variables
- Non-root user in Docker container
- CORS configuration for allowed origins
- Input validation with Pydantic models

### Production Considerations

- Use HTTPS in production
- Implement rate limiting
- Add authentication/authorization
- Monitor API usage and costs
- Set up proper logging and alerting

## 🚀 Deployment

### Production Environment

1. **Set production environment variables**
2. **Use a production WSGI server** (already configured with Uvicorn)
3. **Set up reverse proxy** (Nginx recommended)
4. **Configure monitoring and logging**
5. **Implement backup strategies**

### Scaling

- Use multiple worker processes
- Implement Redis for session storage
- Consider load balancing for high traffic
- Monitor OpenAI API usage and costs

## 🤝 Contributing

1. Follow the existing code structure
2. Add tests for new functionality
3. Update documentation
4. Ensure all agents work with the multi-tenant system

## 📝 License

MIT License - Originally part of the DAO Hotel Multi-Tenant System

## 🔗 Related Repositories

- **[dao-hotel](https://github.com/mkiradani/dao-hotel)**: Main hotel management system (parent repository)
- **[daotomata-stack](https://github.com/mkiradani/daotomata-stack)**: Complete infrastructure stack

## 📜 Migration Notes

This service was extracted from the main dao-hotel monorepo to:

1. **Improve maintainability**: Focused development on AI agent functionality
2. **Enable independent deployment**: Deploy and scale the AI service separately
3. **Facilitate collaboration**: Specialized team can work on AI features
4. **Simplify CI/CD**: Faster build and deployment cycles

### Integration with Main System

This service integrates with the main hotel system through:

- **Supabase Database**: Shared multi-tenant database
- **REST API**: Standardized endpoints for hotel operations
- **Environment Configuration**: Common configuration patterns
