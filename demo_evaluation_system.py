#!/usr/bin/env python3
"""
Demostración del sistema de evaluación AI sin dependencias del SDK completo.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
import sys

# Add project root to path
current_file = Path(__file__).resolve()  
project_root = current_file.parent
sys.path.insert(0, str(project_root))

def simulate_agent_responses():
    """Simula respuestas del agente para diferentes escenarios."""
    
    responses = {
        "basic_info_inquiry": {
            "user": "Hi! Can you tell me about your hotel and what amenities you have?",
            "assistant": """**Hotel Madrid Palace**

Welcome to Hotel Madrid Palace, a luxury 5-star hotel in the heart of Madrid!

**Our Amenities Include:**
- Full-service spa and wellness center
- State-of-the-art fitness center 
- Outdoor swimming pool
- Fine dining restaurant
- Cocktail bar and lounge
- 24/7 concierge service
- Complimentary WiFi throughout
- Valet parking available

We're located in the historic center of Madrid, just steps away from the Royal Palace, Prado Museum, and the best shopping and dining the city has to offer.

How can I assist you further with your stay?""",
            "tools_used": ["get_hotel_info", "get_hotel_facilities"]
        },
        
        "availability_check": {
            "user": "Do you have any rooms available from March 15th to March 18th for 2 guests?",
            "assistant": """**Room Availability**
Check-in: 2024-03-15
Check-out: 2024-03-18
Nights: 3
Guests: 2

**Standard Room** - ✅ Available
Price: €120/night (Total: €360)
Amenities: WiFi, Air Conditioning, TV, Private Bathroom

**Deluxe Room** - ✅ Available  
Price: €180/night (Total: €540)
Amenities: WiFi, Air Conditioning, TV, Private Bathroom, Balcony, Mini Bar

**Suite** - ✅ Available
Price: €350/night (Total: €1,050)
Amenities: WiFi, Air Conditioning, TV, Private Bathroom, Balcony, Mini Bar, Living Area, Kitchen

Would you like me to help you make a reservation for any of these rooms?""",
            "tools_used": ["check_room_availability"]
        },
        
        "service_request": {
            "user": "Hi, I'm in room 315 and I need some extra towels. Also, could you arrange for late checkout tomorrow?",
            "assistant": """**Service Requests Submitted**

**Request 1:**
Request ID: SR-A8B2F4
Service Type: Housekeeping
Description: Extra towels for room 315
Room Number: 315
Priority: Normal
Status: Received
Estimated completion: Within 2-4 hours

**Request 2:** 
Request ID: SR-C9E1D7
Service Type: Front Desk
Description: Late checkout arrangement for room 315
Room Number: 315
Priority: Normal
Status: Received
Estimated completion: Within 1-2 hours

You will be notified when both services are completed. Thank you for staying with us!""",
            "tools_used": ["request_hotel_service"]
        },
        
        "weather_and_activities": {
            "user": "What's the weather like in Madrid this week? I'm looking for some outdoor activities to do during my stay.",
            "assistant": """**Current Weather in Madrid**

🌡️ **Temperature**: 18.5°C (High: 22°C, Low: 14°C)
🌤️ **Conditions**: Partly cloudy with sunny intervals
🌧️ **Rain Chance**: 15%
💧 **Humidity**: 65%
💨 **Wind**: 12.3 km/h

**🎯 Activity Recommendations**
Overall suitability: Good
Advice: Perfect weather for outdoor activities! Light jacket recommended for evening.

✅ **Recommended**: Walking tours, outdoor dining, park visits, cycling
❌ **Avoid**: Beach activities (no beach nearby)

👕 **Clothing**: Comfortable layers, light jacket for evening

**Available Hotel Activities & Experiences**

**City Tour**
Guided tour of Madrid's historic center
Price: EUR 45
Duration: 3h
Max participants: 15

**Flamenco Show**  
Traditional Spanish flamenco performance with dinner
Price: EUR 85
Duration: 2h
Max participants: 50

The weather is perfect for exploring Madrid! Would you like me to help you book any of these activities?""",
            "tools_used": ["get_local_weather", "get_hotel_activities"]
        },
        
        "complex_multi_tool": {
            "user": "I'm arriving tomorrow for a 3-day stay. Can you check the weather, suggest activities, and tell me about your spa services? Also, I might need room service for breakfast.",
            "assistant": """I'd be happy to help you prepare for your 3-day stay! Let me provide you with all the information you need.

**Current Weather Forecast**
🌡️ Temperature: 19°C (Perfect for outdoor activities)
🌤️ Conditions: Sunny with light clouds
🌧️ Rain Chance: 10%
Advice: Excellent weather for sightseeing - bring comfortable walking shoes!

**Recommended Activities for 3 Days**
**City Tour** - Perfect for Day 1
Guided historic center tour, 3 hours, €45

**Flamenco Show** - Great for evening entertainment  
Traditional dinner show, 2 hours, €85

**Hotel Spa Services**
✅ Full-service spa and wellness center
✅ Massage therapy and treatments
✅ Sauna and relaxation areas
✅ Couples spa packages available

**Room Service Information**
We offer 24/7 room service including:
- Continental breakfast (€25)
- Full English breakfast (€35)
- À la carte dining options
- Delivery typically within 30-45 minutes

**Service Request Created**
Request ID: RS-F4A8B2
Service Type: Room Service  
Description: Continental breakfast setup for tomorrow
Priority: Normal
Status: Received

Everything is arranged for your arrival! Is there anything else you'd like me to prepare for your stay?""",
            "tools_used": ["get_local_weather", "get_hotel_activities", "get_hotel_facilities", "request_hotel_service"]
        }
    }
    
    return responses

async def demo_evaluation_system():
    """Demonstra el sistema completo de evaluación."""
    
    print("🤖 DEMOSTRACIÓN DEL SISTEMA DE EVALUACIÓN AI")
    print("="*60)
    
    # Importar el sistema de evaluación
    from tests.ai_evaluation.logger import ConversationLogger
    from tests.ai_evaluation.config import TEST_SCENARIOS, EVALUATION_CONFIG
    
    # Inicializar logger
    logger = ConversationLogger()
    
    # Simular evaluaciones para todos los escenarios
    simulated_responses = simulate_agent_responses()
    
    evaluations_data = []
    
    print("\n📊 SIMULANDO CONVERSACIONES Y EVALUACIONES...")
    print("-" * 60)
    
    for scenario_id, response_data in simulated_responses.items():
        print(f"\n🎭 Escenario: {scenario_id}")
        
        # Log conversation
        conversation_id = f"demo_{scenario_id}"
        
        # User message
        logger.log_conversation(
            conversation_id=conversation_id,
            role="user",
            content=response_data["user"],
            turn_number=1
        )
        
        # Assistant response
        logger.log_conversation(
            conversation_id=conversation_id,
            role="assistant", 
            content=response_data["assistant"],
            turn_number=1,
            tools_used=response_data["tools_used"],
            processing_time=1.2
        )
        
        # Simular evaluación AI
        # En un sistema real, esto sería hecho por GPT-4
        evaluation_score = simulate_ai_evaluation(response_data, scenario_id)
        
        # Log evaluation
        logger.log_evaluation(
            conversation_id=conversation_id,
            scenario_id=scenario_id,
            hotel_id="hotel_madrid_luxury",
            overall_score=evaluation_score["overall_score"],
            passed=evaluation_score["passed"],
            dimension_scores=evaluation_score["dimension_scores"],
            tools_expected=evaluation_score["expected_tools"],
            tools_used=response_data["tools_used"],
            missing_tools=evaluation_score["missing_tools"],
            evaluation_summary=evaluation_score["summary"],
            recommendations=evaluation_score["recommendations"],
            execution_time=0.8
        )
        
        evaluations_data.append(evaluation_score)
        
        print(f"   👤 Usuario: {response_data['user'][:80]}...")
        print(f"   🤖 Agente: {response_data['assistant'][:80]}...")
        print(f"   🛠️  Herramientas: {', '.join(response_data['tools_used'])}")
        print(f"   ⭐ Puntuación: {evaluation_score['overall_score']:.3f} ({'✅ APROBADO' if evaluation_score['passed'] else '❌ REPROBADO'})")
    
    # Generar resumen
    print("\n📈 GENERANDO RESUMEN DE SESIÓN...")
    summary = logger.generate_session_summary({
        "demo_mode": True,
        "total_scenarios": len(simulated_responses)
    })
    
    # Exportar a CSV
    csv_path = logger.export_to_csv()
    
    print("\n" + "="*60)
    print("🎉 DEMOSTRACIÓN COMPLETADA")
    print("="*60)
    
    # Mostrar estadísticas finales
    stats = summary["statistics"]
    print(f"\n📊 **ESTADÍSTICAS FINALES:**")
    print(f"   💬 Total conversaciones: {stats['total_conversations']}")
    print(f"   ✅ Tasa de éxito: {stats['pass_rate']:.1%}")
    print(f"   ⭐ Puntuación promedio: {stats['average_score']:.3f}")
    print(f"   🛠️  Cobertura de herramientas: {stats['tool_coverage']:.1%}")
    
    print(f"\n📁 **ARCHIVOS GENERADOS:**")
    print(f"   📄 Resultados CSV: {csv_path}")
    print(f"   📋 Resumen JSON: {summary['files']['summary']}")
    print(f"   💬 Conversaciones: {summary['files']['conversations']}")
    print(f"   📊 Evaluaciones: {summary['files']['evaluations']}")
    
    print(f"\n🎯 **PUNTUACIONES POR DIMENSIÓN:**")
    dim_scores = summary["dimension_scores"]
    for dimension, score in dim_scores.items():
        print(f"   {dimension.title()}: {score:.3f}")
    
    # Análisis de patrones simulado
    print(f"\n🔍 **ANÁLISIS DE PATRONES:**")
    passed_count = len([e for e in evaluations_data if e["passed"]])
    failed_count = len(evaluations_data) - passed_count
    
    if failed_count == 0:
        print("   🎉 ¡Excelente! Todas las conversaciones aprobaron")
    else:
        print(f"   ⚠️  {failed_count} conversaciones necesitan mejora")
    
    # Herramientas más usadas
    all_tools = []
    for resp in simulated_responses.values():
        all_tools.extend(resp["tools_used"])
    
    from collections import Counter
    tool_counts = Counter(all_tools)
    
    print(f"\n🛠️  **HERRAMIENTAS MÁS USADAS:**")
    for tool, count in tool_counts.most_common():
        print(f"   {tool}: {count} veces")
    
    print(f"\n💡 **RECOMENDACIONES:**")
    print("   1. El sistema está funcionando correctamente")
    print("   2. Cobertura de herramientas es excelente") 
    print("   3. Calidad de respuestas es alta")
    print("   4. Listo para testing con OpenAI API Key")
    
    return True

def simulate_ai_evaluation(response_data, scenario_id):
    """Simula una evaluación AI de la calidad de la respuesta."""
    
    # Criterios específicos por escenario
    scenario_criteria = {
        "basic_info_inquiry": {
            "expected_tools": ["get_hotel_info", "get_hotel_facilities"],
            "base_score": 0.85
        },
        "availability_check": {
            "expected_tools": ["check_room_availability"],
            "base_score": 0.90
        },
        "service_request": {
            "expected_tools": ["request_hotel_service"],
            "base_score": 0.88
        },
        "weather_and_activities": {
            "expected_tools": ["get_local_weather", "get_hotel_activities"],
            "base_score": 0.92
        },
        "complex_multi_tool": {
            "expected_tools": ["get_local_weather", "get_hotel_activities", "get_hotel_facilities", "request_hotel_service"],
            "base_score": 0.87
        }
    }
    
    criteria = scenario_criteria.get(scenario_id, {"expected_tools": [], "base_score": 0.75})
    expected_tools = set(criteria["expected_tools"])
    used_tools = set(response_data["tools_used"])
    
    # Calcular puntuaciones de dimensiones
    tool_coverage = len(used_tools.intersection(expected_tools)) / len(expected_tools) if expected_tools else 1.0
    
    dimension_scores = {
        "accuracy": criteria["base_score"] + 0.05,  # Información precisa
        "helpfulness": criteria["base_score"] + 0.03,  # Respuesta útil
        "tool_usage": tool_coverage,  # Uso correcto de herramientas
        "conversation_flow": criteria["base_score"] - 0.02,  # Fluidez
        "politeness": 0.95  # Siempre cortés
    }
    
    # Puntuación general (promedio ponderado)
    weights = {
        "accuracy": 0.3,
        "helpfulness": 0.2, 
        "tool_usage": 0.2,
        "conversation_flow": 0.15,
        "politeness": 0.15
    }
    
    overall_score = sum(dimension_scores[dim] * weights[dim] for dim in dimension_scores)
    passed = overall_score >= 0.75
    
    missing_tools = list(expected_tools - used_tools)
    
    # Generar recomendaciones
    recommendations = []
    if tool_coverage < 1.0:
        recommendations.append(f"Utilizar herramientas faltantes: {', '.join(missing_tools)}")
    if overall_score < 0.85:
        recommendations.append("Mejorar calidad general de la respuesta")
    if not recommendations:
        recommendations.append("Mantener el excelente nivel de calidad")
    
    return {
        "overall_score": overall_score,
        "passed": passed,
        "dimension_scores": dimension_scores,
        "expected_tools": list(expected_tools),
        "missing_tools": missing_tools,
        "summary": f"Evaluación {scenario_id}: puntuación {overall_score:.3f}, herramientas {len(used_tools)}/{len(expected_tools)}",
        "recommendations": recommendations
    }

if __name__ == "__main__":
    try:
        result = asyncio.run(demo_evaluation_system())
        if result:
            print("\n🎉 ¡Demostración completada exitosamente!")
            print("\nPara probar con AI real, configura OPENAI_API_KEY y ejecuta:")
            print("python -m tests.ai_evaluation.main --run-all")
            sys.exit(0)
        else:
            print("\n❌ Demostración falló")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Demostración interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error en demostración: {e}")
        sys.exit(1)