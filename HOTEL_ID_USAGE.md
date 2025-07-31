# Hotel ID Usage Documentation

## Overview
The hotel bot system uses `hotel_id` as the primary key for all hotel-specific data queries from Directus. This ID is passed via URL parameters and is essential for providing contextual responses.

## Data Flow

### 1. Hotel ID Reception
- **Source**: URL parameter in the request
- **Field**: `request.hotel_id`
- **Example**: `/chat?hotel_id=1`

### 2. Session Context
When a new session is created, the `hotel_id` is stored in the `HotelContext`:
```python
HotelContext(
    hotel_id=hotel_id,
    session_id=session_id,
    conversation_history=[]
)
```

### 3. Automatic Hotel Information Loading
Upon session creation, the system automatically loads:
- Hotel basic info from `hotels` collection
- Contact methods from `contact_methods` collection
- All filtered by `hotel_id`

### 4. Available Collections Using hotel_id

All these collections have a `hotel_id` field for filtering:

1. **hotels** - Basic hotel information
   - name, contact_email, contact_phone_calls, logo, theme

2. **contact_methods** - Multiple contact options
   - phone, email, whatsapp contacts for different departments

3. **guest_services** - Available services
   - spa, room service, concierge, etc.

4. **activities** - Hotel activities
   - descriptions, schedules, age restrictions

5. **facilities** - Hotel facilities
   - gym, pool, meeting rooms, etc.

6. **rooms** - Room types and amenities
   - descriptions, bed configurations, amenities

7. **dishes** - Restaurant menu items
   - ingredients, dietary options, prices

8. **restaurant** - Restaurant information
   - descriptions, photos, operating hours

9. **galleries** - Photo galleries
   - categorized hotel photos

10. **transportation** - Transport options
    - types, costs, schedules, travel times

11. **local_places** - Nearby attractions
    - categories, distances, prices, hours

12. **ai_knowledge** - Custom knowledge base
    - hotel-specific information for AI responses

13. **social_profiles** - Social media links
    - Instagram, Facebook, etc.

14. **website_text** - Website content
    - testimonials, descriptions

15. **hotel_info** - Additional hotel details
    - logo, location

## Usage in Agents

The agents receive the `hotel_id` through the context and should use it in all Directus queries:

```python
# Example query with hotel_id filter
result = await mcp_server.call_tool(
    "mcp__directus__read-items",
    {
        "collection": "guest_services",
        "query": {
            "filter": {"hotel_id": {"_eq": int(hotel_id)}},
            "fields": ["name", "description", "price"]
        }
    }
)
```

## Error Handling

When errors occur, the system uses the cached hotel contact information to provide relevant contact details in error messages, ensuring users always have a way to reach the specific hotel they're interacting with.

## Cache Strategy

Hotel information is cached per `hotel_id` to reduce API calls:
- Cache key: `hotel_id`
- Cache contents: name, phone, email, support hours, all contacts
- Cache duration: Session lifetime

## Important Notes

1. **Always use hotel_id in queries** - Never query collections without filtering by hotel_id
2. **Type conversion** - Ensure hotel_id is converted to int when querying Directus
3. **Fallback values** - Have sensible defaults if hotel data cannot be loaded
4. **Multi-hotel support** - The system supports multiple hotels simultaneously through different sessions