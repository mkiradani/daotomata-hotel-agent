# OpenMeteo Weather Integration

## 🌤️ Overview

The hotel agent system now integrates with the OpenMeteo API to provide real-time weather data and intelligent activity recommendations for guests. This integration is especially important for helping guests plan activities based on current weather conditions.

## ✨ Features

### Real Weather Data
- **Current Conditions**: Temperature, humidity, wind speed, precipitation
- **Weather Codes**: WMO standard weather interpretation codes
- **Extended Info**: UV index, cloud cover, atmospheric pressure
- **Daily Forecasts**: Min/max temperatures, precipitation probability

### Intelligent Activity Recommendations
- **Weather-Based Suggestions**: Activities matched to weather conditions
- **Suitability Assessment**: Excellent, Good, Fair, Poor, Unsuitable ratings
- **Clothing Advice**: Weather-appropriate clothing recommendations
- **Safety Warnings**: UV protection, wind warnings, extreme weather alerts

### Multi-Language Support
- Weather descriptions in multiple languages
- Localized activity suggestions
- Cultural activity preferences

## 🛠️ Technical Implementation

### Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Hotel Agent   │───▶│  Weather Service │───▶│  OpenMeteo API  │
│     Tools       │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Hotel DB      │    │  Activity Logic  │    │  Weather Data   │
│  (Coordinates)  │    │  (Recommendations)│    │   (Real-time)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Components

#### 1. WeatherService (`app/services/weather_service.py`)
- **OpenMeteoClient**: HTTP client for OpenMeteo API
- **WeatherConditions**: Data model for weather information
- **ActivityWeatherAdvice**: Activity recommendations based on weather

#### 2. Enhanced Weather Tool (`app/agents/tools.py`)
- **get_local_weather()**: Main function used by agents
- **_get_hotel_coordinates()**: Hotel coordinate retrieval
- **Activity Integration**: Weather-based activity filtering

#### 3. Data Models
```python
@dataclass
class WeatherConditions:
    temperature: float
    weather_description: str
    precipitation_probability: Optional[int]
    wind_speed: Optional[float]
    humidity: Optional[int]
    uv_index: Optional[float]
    # ... more fields
```

## 🌍 Geographic Coverage

### Coordinate Sources
1. **Database Stored**: Lat/lon coordinates in hotels table
2. **City Mapping**: 50+ major Spanish cities with known coordinates
3. **Fallback System**: Graceful degradation when coordinates unavailable

### Supported Cities
Major Spanish cities are pre-configured with coordinates:
- Madrid, Barcelona, Valencia, Sevilla
- Bilbao, Málaga, Palma, Las Palmas
- And 40+ additional cities

## 📊 Weather-Activity Correlation

### Suitability Levels

| Suitability | Weather Conditions | Activity Recommendations |
|-------------|-------------------|--------------------------|
| **Excellent** | Clear/sunny, 15-30°C, low wind | Beach, sightseeing, outdoor dining |
| **Good** | Partly cloudy, comfortable temp | Walking tours, outdoor markets |
| **Fair** | Light rain, moderate wind | Indoor/outdoor mix, covered activities |
| **Poor** | Heavy rain, strong wind, extreme temp | Indoor activities recommended |
| **Unsuitable** | Storms, severe weather | Stay indoors, safety first |

### Activity Categories

#### ☀️ Sunny Weather Activities
- Beach and swimming activities
- Outdoor dining and terraces
- Walking tours and sightseeing
- Photography excursions
- Outdoor sports and recreation

#### 🌧️ Rainy Weather Activities
- Spa and wellness treatments
- Museums and cultural sites
- Shopping centers and markets
- Cooking classes and workshops
- Indoor entertainment venues

#### ❄️ Cold Weather Activities
- Hot springs and thermal baths
- Cozy restaurants and cafes
- Indoor cultural attractions
- Winter sports (if applicable)
- Warm beverage experiences

## 🔧 Configuration

### Environment Variables
No additional environment variables required - OpenMeteo is free and requires no API key.

### Database Schema
Optional database fields for enhanced functionality:
```sql
ALTER TABLE hotels 
ADD COLUMN latitude DECIMAL(10, 8) NULL,
ADD COLUMN longitude DECIMAL(11, 8) NULL;
```

## 📱 Usage Examples

### Basic Weather Request
```python
# Agent will automatically include weather context
result = await get_local_weather(ctx, hotel_id="madrid_hotel")
```

### Weather with Activity Advice
```python
result = await get_local_weather(
    ctx, 
    hotel_id="barcelona_hotel",
    include_activity_advice=True
)
```

### Sample Response
```
**Current Weather in Madrid**

🌡️ **Temperature**: 25.3°C (High: 28.1°C, Low: 18.2°C)
🌤️ **Conditions**: Clear sky
💧 **Humidity**: 27%
💨 **Wind**: 1.4 km/h
☀️ **UV Index**: 7.2 (High - use sun protection)

**🎯 Activity Recommendations**
Overall suitability: Excellent
Advice: Perfect weather for outdoor activities! Great time to explore.

✅ **Recommended**: Beach activities, Swimming, Sightseeing tours, Outdoor dining
❌ **Avoid**: None

👕 **Clothing**: Light, breathable clothing recommended. Sunscreen and hat for UV protection.
```

## 🎯 Activity Integration

### Context-Aware Recommendations
The weather system integrates with the hotel's activity database to provide contextual recommendations:

1. **Filter Activities**: Remove weather-inappropriate activities
2. **Enhance Descriptions**: Add weather context to activity descriptions
3. **Alternative Suggestions**: Suggest indoor alternatives during bad weather
4. **Safety Considerations**: Include weather-related safety advice

### Seasonal Adaptations
- **Summer**: Focus on cooling activities, sun protection, hydration
- **Winter**: Emphasize warm indoor activities, appropriate clothing
- **Rainy Season**: Prioritize covered and indoor venues
- **Windy Conditions**: Avoid boat trips, outdoor dining with umbrellas

## 🚨 Error Handling

### Fallback Hierarchy
1. **OpenMeteo API**: Primary real-time weather source
2. **Coordinate Fallback**: Use city-based coordinates if hotel coords missing  
3. **General Advice**: Provide general activity guidance if API fails
4. **Hotel Staff**: Direct guests to concierge for current conditions

### Error Scenarios
- **API Failure**: Graceful fallback with general recommendations
- **Invalid Coordinates**: Use city mapping or provide generic advice
- **Network Issues**: Cached data when available, otherwise fallback
- **Timeout**: Quick response with backup information

## 📈 Performance

### Optimization Features
- **Fast Response**: OpenMeteo API typically responds in <100ms
- **Async Processing**: Non-blocking weather requests
- **Error Resilience**: Multiple fallback levels
- **Coordinate Caching**: Hotel coordinates cached after first lookup

### Rate Limits
OpenMeteo provides generous free limits:
- 10,000 API calls per day
- 5,000 calls per hour
- 600 calls per minute

## 🧪 Testing

### Test Coverage
- **API Integration**: Real OpenMeteo API calls
- **Weather-Activity Logic**: Activity recommendation algorithms
- **Error Handling**: Fallback behavior verification
- **Coordinate Resolution**: Hotel location resolution

### Test Execution
```bash
python test_openmeteo_integration.py
```

## 🔮 Future Enhancements

### Planned Features
1. **Weather Forecasts**: 7-day weather predictions
2. **Hourly Updates**: More granular weather timing
3. **Severe Weather Alerts**: Emergency weather notifications
4. **Seasonal Recommendations**: Long-term activity planning
5. **Personal Preferences**: User-specific weather tolerance
6. **Multi-Language**: Localized weather descriptions

### Advanced Integration
- **Calendar Integration**: Weather-based event planning
- **Notification System**: Proactive weather updates
- **Analytics**: Weather impact on guest satisfaction
- **Predictive Recommendations**: ML-based activity suggestions

## 📋 Best Practices

### For Hotel Staff
- Verify hotel coordinates are accurate in database
- Keep activity database updated with weather suitability flags
- Train staff on weather-activity correlation system
- Monitor guest feedback on weather recommendations

### For Developers
- Always handle API failures gracefully
- Cache weather data appropriately (15-30 minutes)
- Validate coordinates before API calls
- Log API errors for monitoring
- Test with various weather conditions

## 🎉 Benefits

### For Guests
- **Accurate Planning**: Real-time weather for activity decisions
- **Safety**: Weather-based safety recommendations
- **Comfort**: Appropriate clothing and preparation advice
- **Experience**: Better activity matching to weather conditions

### For Hotels
- **Guest Satisfaction**: Better recommendations lead to happier guests
- **Operational Efficiency**: Reduced guest complaints about weather
- **Competitive Advantage**: Advanced concierge-level service
- **Data Insights**: Weather impact on guest activities and satisfaction

---

*OpenMeteo Integration v1.0 - Implemented with real-time weather data and intelligent activity recommendations for enhanced guest experience.*