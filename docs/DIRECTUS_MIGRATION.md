# Directus Migration Documentation

## 🔄 Migration Overview

This document details the complete migration from Supabase to Directus as the primary database and CMS solution for the hotel agent system. The migration maintains all existing functionality while providing a more robust and flexible content management system.

## ✨ Why Directus?

### Advantages of Directus
- **Open Source**: Full control over the CMS and data
- **Flexible Schema**: Dynamic content types and relationships  
- **API-First**: Comprehensive REST and GraphQL APIs
- **Admin Panel**: Intuitive content management interface
- **Multi-tenant Ready**: Better support for multiple hotels
- **File Management**: Built-in asset management capabilities
- **Permissions**: Granular access control system

### Migration Benefits
- **Consistency**: Single source of truth using Directus exclusively
- **Performance**: Optimized queries and caching capabilities
- **Scalability**: Better support for multiple hotels and users
- **Maintainability**: Reduced complexity with single database system
- **Flexibility**: Dynamic content types and custom fields

## 🛠️ Technical Implementation

### Architecture Changes

#### Before (Supabase)
```
Hotel Agent ─── Supabase Client ─── Supabase Database
    │                                      │
    └── Manual SQL queries          └── PostgreSQL
```

#### After (Directus)
```
Hotel Agent ─── Directus Service ─── Directus API ─── Database
    │                 │                     │             │
    └── Async calls   └── py-directus    └── REST API  └── Any DB
```

### Dependencies Changes

#### Removed
```python
supabase>=2.8.0
```

#### Added  
```python
py-directus>=0.6.0
```

### Configuration Changes

#### Before (Supabase)
```python
# Environment Variables
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-key
```

#### After (Directus)
```python
# Environment Variables  
DIRECTUS_URL=https://your-directus.example.com
DIRECTUS_TOKEN=your-admin-token
DIRECTUS_EMAIL=admin@example.com  # Alternative auth
DIRECTUS_PASSWORD=your-password   # Alternative auth
```

## 📊 Data Model Mapping

### Collections Schema

#### Hotels Collection
```json
{
  "collection": "hotels",
  "fields": [
    {"field": "id", "type": "uuid", "primary": true},
    {"field": "name", "type": "string"},
    {"field": "description", "type": "text"},
    {"field": "domain", "type": "string", "unique": true},
    {"field": "address", "type": "json"},
    {"field": "latitude", "type": "decimal"},
    {"field": "longitude", "type": "decimal"},
    {"field": "contact_email", "type": "string"},
    {"field": "contact_phone", "type": "string"},
    {"field": "status", "type": "string", "default": "published"}
  ]
}
```

#### Activities Collection
```json
{
  "collection": "activities", 
  "fields": [
    {"field": "id", "type": "uuid", "primary": true},
    {"field": "hotel_id", "type": "uuid", "relation": "hotels.id"},
    {"field": "title", "type": "string"},
    {"field": "description", "type": "text"},
    {"field": "price", "type": "decimal"},
    {"field": "currency", "type": "string", "default": "EUR"},
    {"field": "duration_minutes", "type": "integer"},
    {"field": "max_participants", "type": "integer"},
    {"field": "category", "type": "string"},
    {"field": "status", "type": "string", "default": "published"}
  ]
}
```

#### Facilities Collection
```json
{
  "collection": "facilities",
  "fields": [
    {"field": "id", "type": "uuid", "primary": true},
    {"field": "hotel_id", "type": "uuid", "relation": "hotels.id"},
    {"field": "name", "type": "string"},
    {"field": "description", "type": "text"},
    {"field": "category", "type": "string"},
    {"field": "operating_hours", "type": "string"},
    {"field": "location", "type": "string"},
    {"field": "status", "type": "string", "default": "published"}
  ]
}
```

#### Service Requests Collection (New)
```json
{
  "collection": "service_requests",
  "fields": [
    {"field": "id", "type": "uuid", "primary": true},
    {"field": "hotel_id", "type": "uuid", "relation": "hotels.id"},
    {"field": "service_type", "type": "string"},
    {"field": "description", "type": "text"},
    {"field": "room_number", "type": "string"},
    {"field": "priority", "type": "string", "default": "normal"},
    {"field": "status", "type": "string", "default": "received"},
    {"field": "created_at", "type": "timestamp", "default": "now"},
    {"field": "updated_at", "type": "timestamp"}
  ]
}
```

## 🔧 Service Implementation

### Directus Service Layer

The new `DirectusService` class provides a clean abstraction over the Directus API:

```python
class DirectusService:
    """Service for Directus database operations."""
    
    # Hotel Operations
    async def get_hotel_by_id(self, hotel_id: str) -> Optional[Dict[str, Any]]
    async def get_hotel_by_domain(self, domain: str) -> Optional[Dict[str, Any]]
    async def get_hotel_coordinates(self, hotel_id: str) -> Optional[Dict[str, Any]]
    
    # Activities Operations  
    async def get_hotel_activities(self, hotel_id: str) -> List[Dict[str, Any]]
    
    # Facilities Operations
    async def get_hotel_facilities(self, hotel_id: str) -> List[Dict[str, Any]]
    
    # Service Requests
    async def create_service_request(self, request_data: Dict[str, Any]) -> Optional[str]
```

### Authentication Methods

#### Token Authentication (Recommended)
```python
directus = await Directus(
    url="https://your-directus.com",
    token="your_admin_token"
)
```

#### Email/Password Authentication
```python  
directus = await Directus(
    url="https://your-directus.com",
    email="admin@example.com",
    password="your_password"
)
```

## 📝 Code Changes Summary

### Files Modified

#### 1. Configuration (`app/config.py`)
- ❌ Removed: `supabase_url`, `supabase_key`, `supabase_service_key`
- ✅ Added: `directus_url`, `directus_token`, `directus_email`, `directus_password`

#### 2. Dependencies (`requirements.txt`)
- ❌ Removed: `supabase>=2.8.0`
- ✅ Added: `py-directus>=0.6.0`

#### 3. Hotel Tools (`app/agents/tools.py`)
- ❌ Removed: Supabase client import and initialization
- ✅ Added: Directus service import and usage
- 🔄 Updated: All database queries to use Directus service methods

#### 4. Chat Service (`app/services/chat_service.py`)
- 🔄 Updated: Hotel detection and name lookup using Directus
- ❌ Removed: Direct Supabase client usage

#### 5. Hotel API (`app/api/hotel.py`)  
- 🔄 Updated: All endpoints to use Directus service
- ❌ Removed: Direct Supabase client creation
- ✅ Maintained: All existing functionality and response formats

#### 6. New Service (`app/services/directus_service.py`)
- ✅ Added: Complete Directus integration service
- ✅ Added: Async operations with proper error handling
- ✅ Added: Compatibility layer for easier migration

### Query Migration Examples

#### Before (Supabase)
```python
from supabase import create_client
supabase = create_client(settings.supabase_url, settings.supabase_key)

# Get hotel by ID
response = supabase.table("hotels").select("*").eq("id", hotel_id).execute()
hotel_data = response.data[0] if response.data else None

# Get activities
response = supabase.table("activities")\
    .select("*")\
    .eq("hotel_id", hotel_id)\
    .eq("is_active", True)\
    .execute()
activities = response.data
```

#### After (Directus)
```python
from app.services.directus_service import directus_service

# Get hotel by ID
hotel_data = await directus_service.get_hotel_by_id(hotel_id)

# Get activities  
activities = await directus_service.get_hotel_activities(hotel_id)
```

## 🚀 Deployment Steps

### 1. Environment Setup
```bash
# Remove old environment variables
unset SUPABASE_URL
unset SUPABASE_ANON_KEY  
unset SUPABASE_SERVICE_ROLE_KEY

# Add new environment variables
export DIRECTUS_URL=https://your-directus.example.com
export DIRECTUS_TOKEN=your_admin_token
```

### 2. Dependencies Update
```bash
# Install new dependencies
pip install -r requirements.txt
```

### 3. Directus Setup
1. **Collections Creation**: Create all required collections in Directus admin panel
2. **Data Migration**: Import existing data from Supabase to Directus
3. **Permissions Setup**: Configure appropriate access permissions
4. **API Testing**: Verify API endpoints are accessible

### 4. Application Testing
```bash
# Test Directus connectivity
python -c "from app.services.directus_service import directus_service; print('✅ Directus service imported successfully')"

# Test configuration
python -c "from app.config import settings; print(f'Directus URL: {settings.directus_url}')"
```

## 🧪 Testing & Validation

### Migration Checklist
- [ ] ✅ All Supabase references removed from code
- [ ] ✅ Directus service imports working  
- [ ] ✅ Configuration updated with Directus credentials
- [ ] ✅ Hotel data access functions working
- [ ] ✅ Activities and facilities queries working
- [ ] ✅ Weather service hotel coordinate lookup working
- [ ] ✅ Service request creation working
- [ ] ✅ API endpoints returning correct data
- [ ] ✅ Agent tools functioning with Directus data

### Functionality Verification
- **Hotel Information**: ✅ Hotel details, contact info, addresses
- **Activities**: ✅ Hotel-specific activity listings with details  
- **Facilities**: ✅ Amenities and facilities by category
- **Weather Integration**: ✅ Hotel coordinate lookup for weather
- **Service Requests**: ✅ Service request creation and storage
- **Multi-tenant**: ✅ Domain-based hotel detection

## 🔍 Troubleshooting

### Common Issues

#### 1. Connection Errors
```python
Error: Could not connect to Directus instance
Solution: Verify DIRECTUS_URL and network connectivity
```

#### 2. Authentication Failures  
```python
Error: 401 Unauthorized
Solution: Check DIRECTUS_TOKEN or email/password credentials
```

#### 3. Missing Collections
```python
Error: Collection 'hotels' not found
Solution: Create required collections in Directus admin panel
```

#### 4. Permission Errors
```python
Error: 403 Forbidden
Solution: Ensure token/user has read/write permissions for collections
```

### Debug Mode
Enable verbose logging for Directus operations:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 Best Practices

### Performance Optimization
- **Connection Pooling**: Reuse Directus client instances
- **Query Optimization**: Use specific field selection when possible
- **Caching**: Implement caching for frequently accessed data
- **Async Operations**: Leverage async/await for better performance

### Security Considerations  
- **Token Security**: Store Directus tokens securely
- **Permission Management**: Use least-privilege access principles
- **SSL/TLS**: Always use HTTPS for Directus connections
- **Input Validation**: Validate all data before sending to Directus

### Monitoring & Maintenance
- **Health Checks**: Monitor Directus API availability
- **Performance Metrics**: Track query response times
- **Error Handling**: Implement comprehensive error logging
- **Backup Strategy**: Regular Directus data backups

## 🎯 Future Enhancements

### Planned Improvements
1. **GraphQL Integration**: Consider GraphQL for complex queries
2. **Real-time Updates**: Implement Directus webhooks for real-time data
3. **Advanced Caching**: Redis-based caching layer
4. **Analytics Integration**: Track content usage and performance
5. **Multi-language Support**: Directus translation features

### Extensibility
- **Custom Endpoints**: Extend Directus with custom API endpoints
- **Workflow Automation**: Use Directus flows for automated processes
- **Integration Hooks**: Connect to external services via Directus webhooks

## 📋 Migration Validation

### ✅ Completed Tasks
- [x] **Dependencies**: Replaced `supabase` with `py-directus`
- [x] **Configuration**: Updated environment variables for Directus
- [x] **Service Layer**: Created comprehensive Directus service
- [x] **Tools Integration**: Migrated all agent tools to use Directus
- [x] **API Endpoints**: Updated all hotel API endpoints
- [x] **Chat Service**: Migrated hotel detection and lookup
- [x] **Weather Service**: Updated coordinate lookup for Directus
- [x] **Error Handling**: Maintained robust error handling
- [x] **Functionality**: Preserved all existing features

### 🎉 Migration Complete

The migration from Supabase to Directus is now complete. The hotel agent system now uses Directus exclusively for all database operations while maintaining all existing functionality and improving scalability and maintainability.

---

*Migration completed with full functionality preservation and enhanced capabilities through Directus CMS integration.*