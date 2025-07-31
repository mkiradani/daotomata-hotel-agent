#!/usr/bin/env python3
"""Test detection of false action claims."""

import asyncio
from app.services.confidence_evaluator import confidence_evaluator

async def test_false_action_detection():
    """Test that false action claims are detected and trigger escalation."""
    
    print("🧪 Testing False Action Claim Detection")
    print("=" * 50)
    
    # Test cases with false action claims
    test_cases = [
        {
            "user_question": "Necesitaria hablar con un gerente",
            "ai_response": "He transferido tu solicitud al gerente de servicios. Pronto se pondrán en contacto contigo para discutir los detalles de tu retiro de artes marciales.",
            "should_escalate": True,
            "description": "Manager request with false transfer claim"
        },
        {
            "user_question": "¿Pueden ayudarme con mi reserva?",
            "ai_response": "Por supuesto, puedo ayudarte con tu reserva. ¿Qué información necesitas?",
            "should_escalate": False,
            "description": "Normal helpful response"
        },
        {
            "user_question": "Tengo un problema urgente",
            "ai_response": "He contactado al departamento de atención al cliente. Se comunicarán contigo en los próximos minutos.",
            "should_escalate": True,
            "description": "Urgent issue with false contact claim"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {test_case['description']}")
        print(f"   Question: {test_case['user_question']}")
        print(f"   Response: {test_case['ai_response'][:80]}...")
        print(f"   Expected: {'ESCALATE' if test_case['should_escalate'] else 'PROCEED'}")
        
        try:
            result = await confidence_evaluator.evaluate_response_confidence(
                response=test_case['ai_response'],
                user_question=test_case['user_question'],
                context="Test case",
                threshold=0.65
            )
            
            actual_escalate = result.should_escalate
            expected_escalate = test_case['should_escalate']
            
            if actual_escalate == expected_escalate:
                print(f"   ✅ PASS: Score {result.confidence_score:.2f} - {'ESCALATE' if actual_escalate else 'PROCEED'}")
            else:
                print(f"   ❌ FAIL: Score {result.confidence_score:.2f} - Expected {'ESCALATE' if expected_escalate else 'PROCEED'}, got {'ESCALATE' if actual_escalate else 'PROCEED'}")
                print(f"   Reasons: {result.reasons}")
            
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
    
    print(f"\n🎯 Test completed!")

if __name__ == "__main__":
    asyncio.run(test_false_action_detection())