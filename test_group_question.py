#!/usr/bin/env python3
"""Test specific group booking question to debug escalation."""

import asyncio
from app.services.confidence_evaluator import confidence_evaluator


async def test_group_question():
    """Test confidence evaluation for group booking question."""
    
    print("🧪 Testing Group Booking Question")
    print("=" * 50)
    
    # Test the specific question about group of 20 people
    # You'll need to provide the actual AI response that was generated
    user_question = "Quiero ir con un grupo de 20 personas"
    
    # Example AI responses - replace with actual response from your system
    test_responses = [
        {
            "name": "High Confidence Response",
            "response": "¡Perfecto! Para un grupo de 20 personas, ofrecemos tarifas especiales de grupo. Tenemos habitaciones disponibles para grupos grandes y podemos organizar desayuno grupal. El descuento de grupo es del 15% para reservas de 10+ personas. ¿Te gustaría que revise disponibilidad para fechas específicas?",
            "expected": "NO ESCALATE"
        },
        {
            "name": "Medium Confidence Response", 
            "response": "Para grupos de 20 personas, normalmente ofrecemos tarifas especiales. Te recomiendo contactar con nuestro departamento de grupos para obtener la mejor tarifa y confirmar disponibilidad para tus fechas específicas.",
            "expected": "MAYBE ESCALATE"
        },
        {
            "name": "Low Confidence Response",
            "response": "Entiendo que quieres venir con un grupo grande. Para grupos de ese tamaño necesitarías hablar con alguien especializado en reservas grupales para obtener información específica sobre tarifas y disponibilidad.",
            "expected": "SHOULD ESCALATE"
        },
        {
            "name": "Generic/Vague Response",
            "response": "¡Hola! Gracias por contactarnos. Para ayudarte mejor con tu consulta, ¿podrías proporcionarme más detalles sobre lo que necesitas?",
            "expected": "SHOULD ESCALATE"
        }
    ]
    
    print(f"📝 User Question: {user_question}")
    print()
    
    for i, test_case in enumerate(test_responses, 1):
        print(f"🔍 Test {i}: {test_case['name']}")
        print(f"Expected: {test_case['expected']}")
        print(f"Response: {test_case['response'][:80]}...")
        
        try:
            result = await confidence_evaluator.evaluate_response_confidence(
                response=test_case["response"],
                user_question=user_question,
                context="Group booking inquiry",
                threshold=0.7
            )
            
            action = "ESCALATE" if result.should_escalate else "PROCEED"
            status = "✅" if (
                (result.should_escalate and "ESCALATE" in test_case["expected"]) or
                (not result.should_escalate and "NO ESCALATE" in test_case["expected"])
            ) else "❌"
            
            print(f"📊 Confidence: {result.confidence_score:.2f} → {action} {status}")
            print(f"📋 Key reasons: {', '.join(result.reasons[:2])}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print()
    
    print("=" * 50)
    print("💡 ANALYSIS:")
    print("   - High confidence (0.7+): Specific info, clear next steps")
    print("   - Medium confidence (0.5-0.7): Some info but needs clarification") 
    print("   - Low confidence (<0.5): Vague, admits lack of knowledge")
    print()
    print("🔧 If your actual response should have escalated but didn't:")
    print("   1. Check if it contained specific booking details")
    print("   2. Look for uncertainty keywords ('tal vez', 'creo que')")
    print("   3. See if it provided clear actionable information")
    print()
    print("📋 PASTE YOUR ACTUAL AI RESPONSE HERE TO DEBUG:")
    print("   (Replace one of the test responses above with your actual response)")


if __name__ == "__main__":
    asyncio.run(test_group_question())