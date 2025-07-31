"""Test the Cloudbeds availability integration."""

import asyncio
from datetime import datetime, timedelta
from app.services.cloudbeds_service import CloudbedsService
from app.services.directus_service import DirectusService


async def test_availability():
    """Test checking availability through the Cloudbeds service."""
    print("Testing Cloudbeds availability integration...")
    
    # Initialize services
    cloudbeds_service = CloudbedsService()
    directus_service = DirectusService()
    
    # Get a test hotel (Baberrih Hotel has Cloudbeds credentials)
    hotel_id = 2  # Baberrih Hotel
    
    # Test dates (tomorrow and day after)
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    day_after = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    
    print(f"\nTesting availability for hotel ID: {hotel_id}")
    print(f"Check-in: {tomorrow}")
    print(f"Check-out: {day_after}")
    print(f"Guests: 2 adults, 0 children")
    
    # Test 1: Get hotel credentials
    print("\n1. Getting hotel credentials from Directus...")
    credentials = await cloudbeds_service.get_hotel_credentials(hotel_id)
    print(f"   - Client ID: {'✓' if credentials.get('client_id') else '✗'}")
    print(f"   - Client Secret: {'✓' if credentials.get('client_secret') else '✗'}")
    print(f"   - API Key: {'✓' if credentials.get('api_key') else '✗'}")
    print(f"   - Property ID: {credentials.get('property_id', 'Not found')}")
    print(f"   - Booking URL ID: {credentials.get('booking_url_id', 'Not found')}")
    
    # Test 2: Check availability
    print("\n2. Checking availability...")
    result = await cloudbeds_service.check_availability(
        hotel_id=hotel_id,
        check_in=tomorrow,
        check_out=day_after,
        adults=2,
        children=0
    )
    
    if result.get("error"):
        print(f"   ✗ Error: {result['error']}")
    elif result.get("available"):
        print(f"   ✓ Availability check successful!")
        print(f"   - Booking URL generated: {result['booking_url']}")
        print(f"   - Nights: {result['nights']}")
        if result.get("rooms"):
            print(f"   - Available rooms: {result['total_rooms_available']}")
            for room in result['rooms'][:3]:  # Show first 3 rooms
                print(f"     • {room['roomTypeName']}: {room['currency']} {room['roomRate']}/night")
        elif result.get("message"):
            print(f"   - Message: {result['message']}")
    else:
        print("   ✗ No availability information")
    
    # Test 3: Test with invalid dates
    print("\n3. Testing with invalid dates (past date)...")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    result = await cloudbeds_service.check_availability(
        hotel_id=hotel_id,
        check_in=yesterday,
        check_out=tomorrow,
        adults=2,
        children=0
    )
    
    if result.get("error"):
        print(f"   ✓ Correctly caught error: {result['error']}")
    else:
        print("   ✗ Should have returned an error for past date")
    
    # Test 4: Test booking URL builder
    print("\n4. Testing booking URL builder...")
    booking_url = cloudbeds_service.build_booking_url(
        booking_url_id="lmKzDQ",
        check_in=tomorrow,
        check_out=day_after,
        adults=2,
        children=1,
        currency="eur"
    )
    print(f"   Generated URL: {booking_url}")
    
    print("\n✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(test_availability())