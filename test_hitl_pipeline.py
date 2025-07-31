#!/usr/bin/env python3
"""Test HITL pipeline to identify where escalation is failing."""

import asyncio
from app.services.confidence_evaluator import confidence_evaluator
from app.services.hitl_manager import hitl_manager
from app.services.chatwoot_service import initialize_chatwoot_configs


async def test_hitl_pipeline_step_by_step():
    """Test each step of the HITL pipeline to identify failure point."""
    
    print("🔧 HITL Pipeline Debug Test")
    print("=" * 60)
    
    # Initialize Chatwoot
    await initialize_chatwoot_configs()
    
    # Use a question that should clearly escalate
    user_question = "Quiero ir con un grupo de 20 personas"
    ai_response = "Te recomiendo contactar con nuestro departamento de grupos para obtener la mejor tarifa."
    hotel_id = "2"
    conversation_id = 9
    
    print(f"📝 Question: {user_question}")
    print(f"🤖 Response: {ai_response}")
    print(f"🏨 Hotel: {hotel_id}, Conv: {conversation_id}")
    print()
    
    # Step 1: Test confidence evaluation directly
    print("🔍 STEP 1: Confidence Evaluation")
    print("-" * 40)
    
    try:
        confidence_result = await confidence_evaluator.evaluate_response_confidence(
            response=ai_response,
            user_question=user_question,
            context="Group booking inquiry",
            threshold=0.65  # Use new lower threshold
        )
        
        print(f"✅ Confidence: {confidence_result.confidence_score:.2f}")
        print(f"✅ Should escalate: {confidence_result.should_escalate}")
        print(f"✅ Reasons: {confidence_result.reasons[:2]}")
        
        if not confidence_result.should_escalate:
            print("❌ PROBLEM: Response should escalate but confidence says no!")
            print("   Check threshold or evaluation logic")
            return False
            
    except Exception as e:
        print(f"❌ STEP 1 FAILED: {str(e)}")
        return False
    
    print()
    
    # Step 2: Test HITL manager decision
    print("🔍 STEP 2: HITL Manager Decision")
    print("-" * 40)
    
    try:
        hitl_result = await hitl_manager.evaluate_and_handle_response(
            hotel_id=hotel_id,
            conversation_id=conversation_id,
            ai_response=ai_response,
            user_question=user_question,
            context="Group booking inquiry"
        )
        
        print(f"✅ Action: {hitl_result['action_taken']}")
        print(f"✅ Should escalate: {hitl_result['should_escalate']}")
        print(f"✅ Confidence: {hitl_result['confidence_score']:.2f}")
        
        if hitl_result['should_escalate']:
            escalation = hitl_result.get('escalation_result')
            if escalation:
                print(f"✅ Escalation success: {escalation.success}")
                print(f"✅ Escalation reason: {escalation.reason}")
                if not escalation.success:
                    print(f"❌ ESCALATION FAILED: {escalation.details}")
                    return False
            else:
                print("❌ PROBLEM: Should escalate but no escalation_result!")
                return False
        else:
            print("❌ PROBLEM: HITL manager says no escalation needed!")
            return False
            
    except Exception as e:
        print(f"❌ STEP 2 FAILED: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False
    
    print()
    
    # Step 3: Check conversation status
    print("🔍 STEP 3: Verify Chatwoot Status")
    print("-" * 40)
    
    try:
        from app.services.chatwoot_service import chatwoot_service
        
        status_result = await chatwoot_service.get_conversation_status(hotel_id, conversation_id)
        if status_result.get("success"):
            status = status_result.get("status")
            print(f"✅ Conversation status: {status}")
            if status == "open":
                print("✅ Conversation correctly marked as open")
            else:
                print(f"❌ Expected 'open' but got '{status}'")
        else:
            print(f"❌ Failed to get status: {status_result}")
            
    except Exception as e:
        print(f"❌ STEP 3 FAILED: {str(e)}")
    
    print()
    print("🎯 PIPELINE TEST COMPLETE")
    print("✅ If all steps passed, HITL is working correctly")
    print("❌ If any step failed, that's where the problem is")
    
    return True


async def test_optimized_logging():
    """Test that logging is now more concise."""
    
    print("\n📊 Testing Optimized Logging")
    print("=" * 60)
    
    # This should produce much less verbose output
    user_question = "¿Tienen habitaciones disponibles?"
    ai_response = "Sí, tenemos habitaciones disponibles. ¿Para qué fechas necesita?"
    
    print("🧪 Processing high-confidence response (should not escalate)...")
    
    result = await hitl_manager.evaluate_and_handle_response(
        hotel_id="2",
        conversation_id=9,
        ai_response=ai_response,
        user_question=user_question,
        context="Availability inquiry"
    )
    
    print(f"Result: {result['action_taken']} | Score: {result['confidence_score']:.2f}")
    print("\n✅ Logging should be much cleaner now!")


if __name__ == "__main__":
    asyncio.run(test_hitl_pipeline_step_by_step())
    asyncio.run(test_optimized_logging())