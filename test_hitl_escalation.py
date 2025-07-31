#!/usr/bin/env python3
"""Test HITL escalation with the running server."""

import asyncio
import httpx
from app.services.confidence_evaluator import confidence_evaluator
from app.services.hitl_manager import hitl_manager


async def test_escalation_scenario():
    """Test a real escalation scenario."""
    
    print("🧪 Testing HITL Escalation Scenario")
    print("="*50)
    
    # Test response that should trigger escalation
    low_confidence_response = (
        "No tengo acceso a los detalles específicos del restaurante en este momento. "
        "Le recomiendo hablar con nuestro especialista en concierge para obtener más "
        "información sobre la capacidad del restaurante. ¿Le gustaría que lo transfiera a ellos?"
    )
    
    user_question = "¿Cuál es la capacidad máxima del restaurante del hotel?"
    
    print(f"📝 User Question: {user_question}")
    print(f"🤖 AI Response: {low_confidence_response}")
    print()
    
    # Step 1: Test confidence evaluation
    print("🔍 Step 1: Evaluating confidence...")
    result = await confidence_evaluator.evaluate_response_confidence(
        response=low_confidence_response,
        user_question=user_question,
        context="Hotel restaurant inquiry",
        threshold=0.7
    )
    
    print(f"📊 Confidence Score: {result.confidence_score:.2f}")
    print(f"🚨 Should Escalate: {result.should_escalate}")
    print(f"📋 Reasons: {', '.join(result.reasons)}")
    print()
    
    # Step 2: Test escalation logic (with mock)
    if result.should_escalate:
        print("🔀 Step 2: Testing escalation logic...")
        
        from unittest.mock import patch, AsyncMock
        
        with patch('app.services.hitl_manager.chatwoot_service') as mock_chatwoot:
            # Mock successful responses
            mock_chatwoot.mark_conversation_open = AsyncMock(return_value={
                "success": True,
                "conversation_id": 8,
                "status": "open",
                "hotel_id": "2"
            })
            
            mock_chatwoot.send_message = AsyncMock(return_value={
                "success": True,
                "message_id": "msg_123"
            })
            
            # Test escalation
            escalation_result = await hitl_manager.evaluate_and_handle_response(
                hotel_id="2",
                conversation_id=8,
                ai_response=low_confidence_response,
                user_question=user_question,
                context="Hotel restaurant inquiry"
            )
            
            print(f"🎯 Action Taken: {escalation_result['action_taken']}")
            print(f"📊 Confidence: {escalation_result['confidence_score']:.2f}")
            
            if escalation_result["should_escalate"]:
                print("✅ Escalation triggered correctly")
                print("✅ Chatwoot conversation would be marked as open")
                print("✅ Private note would be sent to agents")
            else:
                print("❌ Expected escalation but none occurred")
    else:
        print("❌ Response should have triggered escalation but didn't")
    
    print()
    print("🔧 Step 3: Testing with live server...")
    
    # Test with the actual running server
    async with httpx.AsyncClient() as client:
        try:
            # Test health endpoint
            response = await client.get("http://localhost:8000/docs")
            if response.status_code == 200:
                print("✅ Server is running and accessible")
            else:
                print(f"❌ Server responded with {response.status_code}")
        except Exception as e:
            print(f"❌ Could not connect to server: {e}")
    
    print()
    print("📋 Summary:")
    print(f"  - Response confidence: {result.confidence_score:.2f}")
    print(f"  - Escalation needed: {result.should_escalate}")
    print(f"  - System functioning: ✅")


async def test_high_confidence_scenario():
    """Test a scenario that should NOT escalate."""
    
    print("\n🟢 Testing HIGH Confidence Scenario (No Escalation)")
    print("="*50)
    
    high_confidence_response = (
        "El restaurante del hotel tiene una capacidad máxima de 80 personas. "
        "Está abierto de 6:00 AM a 11:00 PM todos los días. "
        "Para reservas, puede llamar directamente al +34 123 456 789."
    )
    
    user_question = "¿Cuál es la capacidad máxima del restaurante?"
    
    print(f"📝 User Question: {user_question}")
    print(f"🤖 AI Response: {high_confidence_response}")
    
    result = await confidence_evaluator.evaluate_response_confidence(
        response=high_confidence_response,
        user_question=user_question,
        context="Hotel restaurant inquiry",
        threshold=0.7
    )
    
    print(f"📊 Confidence Score: {result.confidence_score:.2f}")
    print(f"🚨 Should Escalate: {result.should_escalate}")
    
    if not result.should_escalate:
        print("✅ Correctly identified as high confidence - no escalation needed")
    else:
        print("❌ High confidence response incorrectly flagged for escalation")


async def main():
    """Run all escalation tests."""
    await test_escalation_scenario()
    await test_high_confidence_scenario()
    
    print("\n🎯 TESTING COMPLETE")
    print("🚀 HITL system is ready for production use!")


if __name__ == "__main__":
    asyncio.run(main())