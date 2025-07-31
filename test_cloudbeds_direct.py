"""Test Cloudbeds API directly."""

import asyncio
from datetime import datetime, timedelta
from app.services.cloudbeds_service import CloudbedsService


async def test_cloudbeds_direct():
    """Test Cloudbeds service directly."""
    
    service = CloudbedsService()
    hotel_id = 2  # Baberrih Hotel
    
    # Test dates - tomorrow as requested by user
    check_in = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    check_out = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    
    print("Testing Cloudbeds API directly...")
    print(f"Hotel ID: {hotel_id}")
    print(f"Check-in: {check_in}")
    print(f"Check-out: {check_out}")
    print(f"Guests: 2 adults, 0 children")
    print("\n" + "="*50 + "\n")
    
    try:
        # Test availability
        result = await service.check_availability(
            hotel_id=hotel_id,
            check_in=check_in,
            check_out=check_out,
            adults=2,
            children=0,
            rooms=1
        )
        
        print("Result:")
        if result.get("error"):
            print(f"Error: {result['error']}")
        elif result.get("available"):
            print(f"✅ Available: {result['total_rooms_available']} room types found")
            print(f"Nights: {result['nights']}")
            print(f"Booking URL: {result['booking_url']}")
            
            if result.get("rooms"):
                print("\nAvailable rooms:")
                for room in result["rooms"]:
                    print(f"- {room['roomTypeName']}")
                    print(f"  Price: {room['currency']} {room['roomRate']}/night")
                    print(f"  Total: {room['currency']} {room['totalRate']}")
                    print(f"  Available: {room['roomsAvailable']} units")
                    print(f"  Max guests: {room['maxGuests']}")
                    print()
        else:
            print("No availability")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_cloudbeds_direct())