"""Test to understand Cloudbeds API response structure for room rates."""

import asyncio
from app.services.cloudbeds_service import CloudbedsService


async def test_availability_response():
    """Test the availability check to understand the response structure."""
    service = CloudbedsService()
    
    # Test with a real request
    result = await service.check_availability(
        hotel_id=1,
        check_in="2024-02-20",
        check_out="2024-02-23",  # 3 nights
        adults=2,
        children=0
    )
    
    print("=== Availability Response ===")
    print(f"Success: {result.get('available')}")
    
    if result.get('rooms'):
        print(f"\nNumber of nights: {result.get('nights')}")
        print("\nRoom details:")
        for room in result['rooms']:
            print(f"\nRoom Type: {room['roomTypeName']}")
            print(f"  - roomRate (from API): {room['roomRate']}")
            print(f"  - totalRate (calculated): {room['totalRate']}")
            print(f"  - Currency: {room['currency']}")
            
            # Calculate what the per-night rate would be
            if result.get('nights') and room['totalRate'] > 0:
                per_night = room['roomRate'] / result['nights']
                print(f"  - Calculated per-night rate: {per_night:.2f}")
                print(f"  - Is roomRate the total? {room['roomRate'] == room['totalRate'] / result['nights']}")
    else:
        print(f"Error or no rooms: {result}")


async def test_api_documentation():
    """Show what we expect from the Cloudbeds API."""
    print("\n=== Cloudbeds API Documentation ===")
    print("According to Cloudbeds API docs:")
    print("- roomRate: The rate for the entire stay (not per night)")
    print("- The API returns the total price for all requested nights")
    print("- To get per-night rate, divide roomRate by number of nights")


if __name__ == "__main__":
    asyncio.run(test_availability_response())
    asyncio.run(test_api_documentation())