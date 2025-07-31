#!/usr/bin/env python3
"""Test group booking detection and escalation."""

import asyncio
from app.services.confidence_evaluator import confidence_evaluator

async def test_group_booking_scenarios():
    """Test various group booking scenarios that should escalate."""
    
    print("🧪 Testing Group Booking Detection")
    print("=" * 50)
    
    test_cases = [
        {
            "user_question": "Me gustaria organizar un retiro con un grupo de 20 personas en el hotel",
            "ai_response": "¡Hola! Soy el especialista en reservas del hotel. Estoy aquí para ayudarte a organizar tu retiro para 20 personas. Necesitaré algunos detalles para poder comenzar: Fecha de entrada y salida (en formato AAAA-MM-DD). Número de habitaciones necesarias.",
            "should_escalate": True,
            "description": "20 person retreat - AI claiming to be specialist"
        },
        {
            "user_question": "Quiero ir con un grupo de 20 personas",
            "ai_response": "Te recomiendo contactar con nuestro departamento de grupos para obtener la mejor tarifa.",
            "should_escalate": True,
            "description": "20 person group - referral response"
        },
        {
            "user_question": "Necesito reservar para 15 personas",
            "ai_response": "Puedo ayudarte con tu reserva para 15 personas. ¿Qué fechas tienes en mente?",
            "should_escalate": True,
            "description": "15 person group - AI offering direct help"
        },
        {
            "user_question": "¿Tienen habitaciones para 2 personas?",
            "ai_response": "Sí, tenemos habitaciones dobles disponibles. ¿Para qué fechas necesitas?",
            "should_escalate": False,
            "description": "Normal 2 person booking - should NOT escalate"
        },
        {
            "user_question": "Organizamos un evento corporativo para 50 personas",
            "ai_response": "Excelente, puedo asistirte con tu evento corporativo. Contamos con salones de conferencias.",
            "should_escalate": True,
            "description": "50 person corporate event"
        },
        {
            "user_question": "Somos un grupo de 8 amigos",
            "ai_response": "Perfecto, puedo ayudarte con la reserva para tu grupo de 8 personas.",
            "should_escalate": False,
            "description": "8 person group - under threshold"
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
                context="Group booking test",
                threshold=0.65
            )
            
            actual_escalate = result.should_escalate
            expected_escalate = test_case['should_escalate']
            
            if actual_escalate == expected_escalate:
                print(f"   ✅ PASS: Score {result.confidence_score:.2f} - {'ESCALATE' if actual_escalate else 'PROCEED'}")
                print(f"   Method: {result.evaluation_method}")
            else:
                print(f"   ❌ FAIL: Score {result.confidence_score:.2f} - Expected {'ESCALATE' if expected_escalate else 'PROCEED'}, got {'ESCALATE' if actual_escalate else 'PROCEED'}")
                print(f"   Reasons: {result.reasons}")
                print(f"   Method: {result.evaluation_method}")
            
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
    
    print(f"\n🎯 Test completed!")

if __name__ == "__main__":
    asyncio.run(test_group_booking_scenarios())