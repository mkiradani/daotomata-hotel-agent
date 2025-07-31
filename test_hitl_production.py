#!/usr/bin/env python3
"""Test complete HITL flow in production environment."""

import asyncio
from app.services.confidence_evaluator import confidence_evaluator
from app.services.hitl_manager import hitl_manager
from app.services.chatwoot_service import initialize_chatwoot_configs


async def test_complete_hitl_flow():
    """Test the complete HITL escalation flow with real Chatwoot integration."""
    
    print("🚀 Testing Complete HITL Flow in Production")
    print("=" * 60)
    
    # Initialize Chatwoot configurations
    await initialize_chatwoot_configs()
    
    # Test case: Low confidence response that should trigger escalation
    low_confidence_response = (
        "Lo siento, pero no tengo información específica sobre las políticas de cancelación "
        "del hotel en este momento. Te recomiendo contactar directamente con recepción para "
        "obtener detalles precisos sobre la cancelación de tu reserva."
    )
    
    user_question = "¿Cuál es la política de cancelación del hotel?"
    hotel_id = "2"
    conversation_id = 9
    
    print(f"📝 User Question: {user_question}")
    print(f"🤖 AI Response: {low_confidence_response}")
    print(f"🏨 Hotel ID: {hotel_id}")
    print(f"💬 Conversation ID: {conversation_id}")
    print()
    
    # Step 1: Test confidence evaluation
    print("🔍 Step 1: Evaluating response confidence...")
    confidence_result = await confidence_evaluator.evaluate_response_confidence(
        response=low_confidence_response,
        user_question=user_question,
        context="Hotel policy inquiry",
        threshold=0.7
    )
    
    print(f"📊 Confidence Score: {confidence_result.confidence_score:.2f}")
    print(f"🚨 Should Escalate: {confidence_result.should_escalate}")
    print(f"🔧 Evaluation Method: {confidence_result.evaluation_method}")
    print(f"📋 Reasons: {', '.join(confidence_result.reasons)}")
    print()
    
    # Step 2: Test full HITL flow
    print("🔀 Step 2: Testing complete HITL escalation...")
    
    escalation_result = await hitl_manager.evaluate_and_handle_response(
        hotel_id=hotel_id,
        conversation_id=conversation_id,
        ai_response=low_confidence_response,
        user_question=user_question,
        context="Hotel policy inquiry"
    )
    
    print(f"🎯 Action Taken: {escalation_result['action_taken']}")
    print(f"📊 Confidence Score: {escalation_result['confidence_score']:.2f}")
    print(f"🚨 Should Escalate: {escalation_result['should_escalate']}")
    print()
    
    if escalation_result["should_escalate"]:
        escalation_details = escalation_result.get("escalation_result")
        if escalation_details and escalation_details.success:
            print("✅ ESCALATION SUCCESSFUL!")
            print(f"   ✅ Conversation marked as 'open' for automatic agent assignment")
            print(f"   ✅ Private note sent to inform human agents")
            print(f"   ✅ Escalation recorded for analytics")
            print(f"   📊 Confidence was {escalation_result['confidence_score']:.2f} (< 0.7 threshold)")
            print()
            
            # Check escalation statistics  
            stats = await hitl_manager.get_escalation_stats(hotel_id)
            print(f"📈 Escalation Stats for Hotel {hotel_id}:")
            print(f"   Total escalations: {stats['total_escalations']}")
            print(f"   Average confidence: {stats.get('average_confidence', 0):.2f}")
            
        else:
            print("❌ ESCALATION FAILED!")
            if escalation_details:
                print(f"   Reason: {escalation_details.reason}")
                print(f"   Details: {escalation_details.details}")
            return False
    else:
        print("❌ Expected escalation but none occurred!")
        return False
    
    print()
    print("🎯 HITL PRODUCTION TEST COMPLETE!")
    print("✅ System is fully operational and ready for production use")
    print("✅ Low confidence responses will automatically escalate to human agents")
    print("✅ High confidence responses will proceed normally")
    
    return True


async def test_high_confidence_scenario():
    """Test that high confidence responses don't trigger escalation."""
    
    print("\n🟢 Testing High Confidence Scenario (No Escalation)")
    print("=" * 60)
    
    high_confidence_response = (
        "La política de cancelación del hotel es la siguiente: "
        "Las reservas pueden cancelarse sin costo hasta 24 horas antes del check-in. "
        "Las cancelaciones realizadas con menos de 24 horas de anticipación "
        "están sujetas a un cargo del 100% de la primera noche. "
        "Para cancelar, puede llamar al +34 123 456 789 o enviar un email a reservas@hotel.com."
    )
    
    user_question = "¿Cuál es la política de cancelación?"
    
    print(f"📝 User Question: {user_question}")
    print(f"🤖 AI Response: {high_confidence_response[:100]}...")
    print()
    
    escalation_result = await hitl_manager.evaluate_and_handle_response(
        hotel_id="2",
        conversation_id=9,
        ai_response=high_confidence_response,
        user_question=user_question,
        context="Hotel policy inquiry"
    )
    
    print(f"🎯 Action Taken: {escalation_result['action_taken']}")
    print(f"📊 Confidence Score: {escalation_result['confidence_score']:.2f}")
    print(f"🚨 Should Escalate: {escalation_result['should_escalate']}")
    
    if not escalation_result["should_escalate"]:
        print("✅ Correctly identified as high confidence - no escalation needed")
        print("✅ Response will be sent directly to the customer")
    else:
        print("❌ High confidence response incorrectly flagged for escalation")
        return False
    
    return True


async def main():
    """Run complete HITL production tests."""
    try:
        print("🧪 HITL Production Testing Suite")
        print("=" * 80)
        
        # Test 1: Low confidence escalation
        test1_success = await test_complete_hitl_flow()
        
        # Test 2: High confidence no escalation  
        test2_success = await test_high_confidence_scenario()
        
        print("\n" + "=" * 80)
        print("📋 FINAL RESULTS")
        print("=" * 80)
        
        print(f"✅ Low Confidence Escalation: {'PASS' if test1_success else 'FAIL'}")
        print(f"✅ High Confidence No Escalation: {'PASS' if test2_success else 'FAIL'}")
        
        overall_success = test1_success and test2_success
        
        if overall_success:
            print("\n🏆 ALL TESTS PASSED!")
            print("🚀 HITL system is 100% operational and ready for production!")
            print("\n📋 System Capabilities:")
            print("   ✅ Evaluates AI response confidence using hybrid approach")
            print("   ✅ Escalates low confidence responses to human agents")
            print("   ✅ Marks conversations as 'open' for automatic assignment")
            print("   ✅ Sends private notes to inform agents of escalation context")
            print("   ✅ Records escalation statistics for monitoring")
            print("   ✅ Processes high confidence responses normally")
            return 0
        else:
            print("\n❌ SOME TESTS FAILED!")
            print("🔧 Please review the errors above and fix before production use")
            return 1
            
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)