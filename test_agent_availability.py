"""Test the hotel agent's availability check functionality."""

import asyncio
from datetime import datetime, timedelta
from openai import AsyncOpenAI
from agents import Swarm
from app.agents.hotel_agents import triage_agent


async def test_agent_availability():
    """Test the hotel agent's ability to check availability."""
    
    # Initialize OpenAI client
    client = AsyncOpenAI()
    
    # Initialize swarm with the triage agent
    swarm = Swarm(client=client)
    
    # Test hotel context (Baberrih Hotel)
    test_context = {
        "hotel_id": "2",  # Baberrih Hotel
        "hotel_name": "Baberrih Hotel"
    }
    
    # Test dates
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    day_after = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    
    print("Testing Hotel Agent Availability Check...")
    print(f"Hotel: {test_context['hotel_name']} (ID: {test_context['hotel_id']})")
    print(f"Check-in: {tomorrow}")
    print(f"Check-out: {day_after}")
    print("\n" + "="*50 + "\n")
    
    # Run the agent
    stream = swarm.run(
        agent=triage_agent,
        context=test_context,
        stream=True,
        messages=[{
            "role": "user",
            "content": f"Do you have any rooms available for tomorrow ({tomorrow})? I need a room for 2 adults."
        }]
    )
    
    # Process the stream
    async for chunk in stream:
        if chunk.data is not None:
            print(chunk.data, end="", flush=True)
    
    print("\n\n" + "="*50 + "\n")
    
    # Test with specific dates
    print("Testing with specific dates...")
    
    stream = swarm.run(
        agent=triage_agent,
        context=test_context,
        stream=True,
        messages=[{
            "role": "user",
            "content": f"I need a room from {tomorrow} to {day_after} for 2 adults and 1 child. Can you check availability?"
        }]
    )
    
    async for chunk in stream:
        if chunk.data is not None:
            print(chunk.data, end="", flush=True)
    
    print("\n\n✅ Agent test completed!")


if __name__ == "__main__":
    import os
    
    # Ensure we have the OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Please set OPENAI_API_KEY environment variable")
        exit(1)
    
    asyncio.run(test_agent_availability())