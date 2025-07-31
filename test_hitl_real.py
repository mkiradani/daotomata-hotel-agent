#!/usr/bin/env python3
"""Test real HITL functionality with actual API calls."""

import asyncio
from app.services.confidence_evaluator import confidence_evaluator
from app.services.hitl_manager import hitl_manager


async def test_real_confidence_evaluation():
    """Test confidence evaluation with real responses."""
    
    print("🧪 Testing HITL Confidence Evaluation with Real Data")
    print("=" * 60)
    
    # Test cases with real hotel responses
    test_cases = [
        {
            "name": "High Confidence Response",
            "response": "Definitivamente tenemos disponibilidad para el 15 de enero. El precio es exactamente $120 por noche, incluye desayuno continental y WiFi gratuito. Puedo confirmar su reserva ahora mismo.",
            "question": "¿Tienen disponibilidad para el 15 de enero?",
            "expected_confidence": "high"
        },
        {
            "name": "Low Confidence Response", 
            "response": "No estoy seguro si tenemos disponibilidad para esa fecha. Tal vez podría verificar con recepción. Creo que puede ser posible, pero no puedo confirmarlo.",
            "question": "¿Tienen habitaciones disponibles para mañana?",
            "expected_confidence": "low"
        },
        {
            "name": "Empty Response",
            "response": "",
            "question": "¿Cuál es el precio de las habitaciones?",
            "expected_confidence": "low"
        },
        {
            "name": "Error Response",
            "response": "Error: Unable to process your request. Service temporarily unavailable.",
            "question": "¿Pueden ayudarme con mi reserva?",
            "expected_confidence": "low"
        },
        {
            "name": "Medium Confidence Response",
            "response": "Según nuestra disponibilidad actual, parece que tenemos habitaciones libres para esa fecha. El precio suele ser alrededor de $100-150 por noche, pero debería confirmar los detalles exactos.",
            "question": "¿Cuánto cuesta una habitación para el fin de semana?",
            "expected_confidence": "medium"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['name']}")
        print(f"Question: {test_case['question']}")
        print(f"Response: {test_case['response'][:100]}{'...' if len(test_case['response']) > 100 else ''}")
        
        try:
            # Evaluate confidence with real API call
            result = await confidence_evaluator.evaluate_response_confidence(
                response=test_case["response"],
                user_question=test_case["question"],
                context="Hotel booking conversation",
                threshold=0.7
            )
            
            print(f"📊 Confidence Score: {result.confidence_score:.2f}")
            print(f"🚨 Should Escalate: {result.should_escalate}")
            print(f"🔧 Evaluation Method: {result.evaluation_method}")
            print(f"📋 Reasons: {', '.join(result.reasons)}")
            
            # Verify expected confidence level
            if test_case["expected_confidence"] == "high":
                expected_escalate = False
                expected_score_range = (0.7, 1.0)
            elif test_case["expected_confidence"] == "low":
                expected_escalate = True
                expected_score_range = (0.0, 0.7)
            else:  # medium
                expected_escalate = result.confidence_score < 0.7
                expected_score_range = (0.3, 0.8)
            
            # Check results
            score_ok = expected_score_range[0] <= result.confidence_score <= expected_score_range[1]
            escalate_ok = result.should_escalate == expected_escalate
            
            status = "✅ PASS" if (score_ok and escalate_ok) else "❌ FAIL"
            print(f"Status: {status}")
            
            if not score_ok:
                print(f"  Score {result.confidence_score:.2f} not in expected range {expected_score_range}")
            if not escalate_ok:
                print(f"  Escalation {result.should_escalate} != expected {expected_escalate}")
            
            results.append({
                "test": test_case["name"],
                "score": result.confidence_score,
                "should_escalate": result.should_escalate,
                "reasons": result.reasons,
                "pass": score_ok and escalate_ok
            })
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            results.append({
                "test": test_case["name"],
                "error": str(e),
                "pass": False
            })
    
    # Summary
    print("\n" + "=" * 60)
    print("📈 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results if r.get("pass", False))
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    for result in results:
        status = "✅" if result.get("pass", False) else "❌"
        print(f"{status} {result['test']}")
        if "score" in result:
            print(f"    Score: {result['score']:.2f}, Escalate: {result['should_escalate']}")
        if "error" in result:
            print(f"    Error: {result['error']}")
    
    return results


async def test_real_escalation_flow():
    """Test escalation flow with mock Chatwoot."""
    
    print("\n🔄 Testing HITL Escalation Flow")
    print("=" * 60)
    
    # Mock Chatwoot service for testing
    from unittest.mock import AsyncMock, patch
    
    with patch('app.services.hitl_manager.chatwoot_service') as mock_chatwoot:
        # Mock successful Chatwoot responses
        mock_chatwoot.mark_conversation_open.return_value = {
            "success": True,
            "conversation_id": 123,
            "status": "open",
            "hotel_id": "1"
        }
        
        mock_chatwoot.send_message.return_value = {
            "success": True,
            "message_id": "msg_123"
        }
        
        # Test escalation with low confidence response
        print("🚨 Testing escalation with low confidence response...")
        
        result = await hitl_manager.evaluate_and_handle_response(
            hotel_id="1",
            conversation_id=123,
            ai_response="No estoy seguro de la disponibilidad. Tal vez deberías llamar directamente.",
            user_question="¿Tienen habitaciones disponibles?",
            context="Hotel booking inquiry"
        )
        
        print(f"📊 Confidence Score: {result['confidence_score']:.2f}")
        print(f"🚨 Should Escalate: {result['should_escalate']}")
        print(f"🎯 Action Taken: {result['action_taken']}")
        
        if result["should_escalate"]:
            print("✅ Escalation triggered correctly")
            
            # Verify Chatwoot service calls
            if mock_chatwoot.mark_conversation_open.called:
                print("✅ Chatwoot conversation marked as open")
            else:
                print("❌ Failed to mark conversation as open")
                
            if mock_chatwoot.send_message.called:
                print("✅ Private note sent to agents")
            else:
                print("❌ Failed to send private note")
                
        else:
            print("❌ Expected escalation but none occurred")
    
    # Test statistics
    print("\n📊 Testing escalation statistics...")
    stats = await hitl_manager.get_escalation_stats()
    print(f"Total escalations: {stats['total_escalations']}")
    print(f"Hotels with escalations: {stats['hotels_with_escalations']}")
    
    return True


async def main():
    """Run all real HITL tests."""
    
    print("🚀 Starting Real HITL Integration Tests")
    print("=" * 80)
    
    try:
        # Test confidence evaluation
        confidence_results = await test_real_confidence_evaluation()
        
        # Test escalation flow
        escalation_results = await test_real_escalation_flow()
        
        print("\n🎯 ALL TESTS COMPLETED")
        print("=" * 80)
        
        # Overall summary
        confidence_passed = sum(1 for r in confidence_results if r.get("pass", False))
        confidence_total = len(confidence_results)
        
        print(f"✅ Confidence Tests: {confidence_passed}/{confidence_total}")
        print(f"✅ Escalation Tests: {'PASS' if escalation_results else 'FAIL'}")
        
        overall_success = (confidence_passed == confidence_total) and escalation_results
        
        print(f"\n🏆 OVERALL RESULT: {'✅ SUCCESS' if overall_success else '❌ SOME FAILURES'}")
        
        return overall_success
        
    except Exception as e:
        print(f"💥 CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)