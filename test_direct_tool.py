"""Test the availability tool directly."""

import asyncio
from datetime import datetime, timedelta
from agents import RunContextWrapper
from app.agents.pms_tools import check_real_room_availability


async def test_direct():
    """Test the tool directly."""
    
    # Create a mock context
    mock_context = type('Context', (), {
        'hotel_id': '2'  # Baberrih Hotel
    })()
    
    # Test dates
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    day_after = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    
    print("Testing direct tool call...")
    print(f"Hotel ID: 2")
    print(f"Check-in: {tomorrow}")
    print(f"Check-out: {day_after}")
    print(f"Guests: 2 adults, 1 child")
    print("\n" + "="*50 + "\n")
    
    try:
        # Call the underlying function of the tool
        # The decorator wraps the function, so we need to access the original
        result = await check_real_room_availability.func(
            RunContextWrapper(mock_context),
            check_in=tomorrow,
            check_out=day_after,
            guests=2,
            children=1,
            hotel_id='2'
        )
        
        print("Result:")
        print(result)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_direct())