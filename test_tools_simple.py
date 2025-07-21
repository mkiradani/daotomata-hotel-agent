#!/usr/bin/env python3
"""
Simple test for tool functionality without full agent integration.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
current_file = Path(__file__).resolve()
project_root = current_file.parent
sys.path.insert(0, str(project_root))

# Mock context for tools
class MockContext:
    def __init__(self, hotel_id: str):
        self.hotel_id = hotel_id

class MockRunContextWrapper:
    def __init__(self, hotel_id: str):
        self.context = MockContext(hotel_id)

async def test_individual_tools():
    """Test individual tools with mock context."""
    
    print("🔧 Testing Hotel Agent Tools")
    print("="*40)
    
    # Setup mock context
    hotel_id = "hotel_madrid_luxury"
    ctx = MockRunContextWrapper(hotel_id)
    
    print(f"Hotel ID: {hotel_id}")
    print(f"Context type: {type(ctx)}")
    
    # Import tools
    from app.agents import tools
    
    # Test get_hotel_info
    print("\n1️⃣ Testing get_hotel_info...")
    try:
        # Get the actual function from the FunctionTool
        tool = tools.get_hotel_info
        print(f"   Tool type: {type(tool)}")
        
        # For OpenAI Agents SDK tools, we use on_invoke_tool
        result = await tool.on_invoke_tool(ctx)
            
        print(f"✅ get_hotel_info result: {result[:150]}...")
        
    except Exception as e:
        print(f"❌ get_hotel_info failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test check_room_availability
    print("\n2️⃣ Testing check_room_availability...")
    try:
        from datetime import date, timedelta
        
        tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        next_week = (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        tool = tools.check_room_availability
        result = await tool.on_invoke_tool(ctx, tomorrow, next_week, 2)
            
        print(f"✅ check_room_availability result: {result[:150]}...")
        
    except Exception as e:
        print(f"❌ check_room_availability failed: {e}")
    
    # Test request_hotel_service
    print("\n3️⃣ Testing request_hotel_service...")
    try:
        tool = tools.request_hotel_service
        result = await tool.on_invoke_tool(
            ctx,
            service_type="housekeeping",
            description="Need extra towels", 
            room_number="315",
            priority="normal"
        )
            
        print(f"✅ request_hotel_service result: {result[:150]}...")
        
    except Exception as e:
        print(f"❌ request_hotel_service failed: {e}")
    
    print("\n" + "="*40)
    print("🎉 Tool testing completed!")
    
    return True

if __name__ == "__main__":
    result = asyncio.run(test_individual_tools())
    if result:
        print("✅ Tool tests completed!")
        sys.exit(0)
    else:
        print("❌ Tool tests failed!")
        sys.exit(1)