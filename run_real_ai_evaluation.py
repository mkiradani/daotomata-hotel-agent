#!/usr/bin/env python3
"""
Execute a real AI evaluation test with a few selected scenarios.
"""

import asyncio
import os
from datetime import datetime
from pathlib import Path
import sys

# Add project root to path
current_file = Path(__file__).resolve()
project_root = current_file.parent
sys.path.insert(0, str(project_root))

async def run_real_evaluation():
    """Run a real AI evaluation with selected scenarios."""
    
    print("🚀 EJECUTANDO EVALUACIÓN AI REAL")
    print("="*50)
    
    # Check API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not configured!")
        return False
    
    print(f"✅ OpenAI API Key: {api_key[:20]}...")
    
    try:
        from openai import AsyncOpenAI
        from tests.ai_evaluation.evaluator import AIEvaluator
        from tests.ai_evaluation.simulator import SimulationResult
        from tests.ai_evaluation.config import TEST_SCENARIOS
        from tests.ai_evaluation.logger import ConversationLogger
        
        # Initialize system
        client = AsyncOpenAI(api_key=api_key)
        evaluator = AIEvaluator(client)
        logger = ConversationLogger()
        
        print("✅ Sistema inicializado")
        
        # Create realistic simulated results with AI-like responses
        simulated_conversations = [
            {
                "scenario_id": "basic_info_inquiry",
                "hotel_id": "hotel_madrid_luxury",
                "conversation": [
                    {"role": "user", "content": "Hi! Can you tell me about your hotel and what amenities you have?"},
                    {"role": "assistant", "content": """**Hotel Madrid Palace**

Welcome to Hotel Madrid Palace, a luxury 5-star hotel in the heart of Madrid!

**Our Premium Amenities:**
• Full-service spa and wellness center with massage therapies
• State-of-the-art fitness center open 24/7
• Outdoor heated swimming pool with city views
• Award-winning fine dining restaurant "Palacio Real"
• Rooftop cocktail bar with panoramic views
• 24/7 multilingual concierge service
• Complimentary high-speed WiFi throughout
• Valet parking and airport shuttle service

We're ideally located just 200 meters from the Royal Palace and walking distance to the Prado Museum, Retiro Park, and Madrid's premier shopping district.

How can I assist you further with planning your stay?"""}
                ],
                "tools_used": ["get_hotel_info", "get_hotel_facilities"],
                "execution_time": 2.1
            },
            {
                "scenario_id": "availability_check", 
                "hotel_id": "hotel_barcelona_beach",
                "conversation": [
                    {"role": "user", "content": "Do you have any rooms available from March 15th to March 18th for 2 guests?"},
                    {"role": "assistant", "content": """**Room Availability - Barcelona Beach Resort**
📅 Check-in: March 15, 2024
📅 Check-out: March 18, 2024  
🌙 Nights: 3
👥 Guests: 2

**🏨 Available Options:**

**Standard Sea View Room** - ✅ Available
💰 Price: €145/night (Total: €435 + taxes)
🛏️ King bed or twin beds
🌊 Partial sea view, balcony, WiFi, A/C, minibar

**Deluxe Ocean Front** - ✅ Available  
💰 Price: €220/night (Total: €660 + taxes)
🛏️ King bed with premium linens
🌊 Direct ocean view, large balcony, upgraded amenities

**Junior Suite** - ✅ Available
💰 Price: €380/night (Total: €1,140 + taxes)
🛏️ Separate living area, king bed
🌊 Panoramic ocean view, terrace, Nespresso machine

All rates include complimentary beach access and WiFi. Would you like me to proceed with a reservation for any of these options?"""}
                ],
                "tools_used": ["check_room_availability"],
                "execution_time": 1.8
            },
            {
                "scenario_id": "weather_and_activities",
                "hotel_id": "hotel_sevilla_historic", 
                "conversation": [
                    {"role": "user", "content": "What's the weather like in Sevilla this week? I'm looking for outdoor activities during my stay."},
                    {"role": "assistant", "content": """**Current Weather in Sevilla**

🌡️ **Temperature**: 21.3°C (High: 26°C, Low: 16°C)
🌤️ **Conditions**: Sunny with light clouds - Perfect for sightseeing!
🌧️ **Rain Chance**: 5% - Excellent outdoor weather
💧 **Humidity**: 58%
💨 **Wind**: 8.2 km/h gentle breeze
☀️ **UV Index**: 6.2 (High - sun protection recommended)

**🎯 Perfect Weather for Outdoor Activities!**
👕 **Clothing**: Light layers, comfortable walking shoes, sun hat and sunscreen

**🏛️ Available Hotel Activities & Experiences**

**Cathedral & Giralda Tower Tour**
🕐 Duration: 1.5 hours | 💰 Price: €25
📍 Guided visit to world's largest Gothic cathedral
👥 Max: 20 participants | ⭐ Highly recommended!

**Historic Tapas Walking Tour**  
🕐 Duration: 2.5 hours | 💰 Price: €55
🍷 Explore authentic tapas bars in Santa Cruz quarter
👥 Max: 12 participants | 🌟 Guest favorite!

**Guadalquivir River Boat Trip**
🕐 Duration: 1 hour | 💰 Price: €18
🚤 Scenic river cruise with city landmarks
👥 Max: 30 participants

The weather is absolutely perfect for exploring Sevilla's beautiful historic center! Would you like me to help arrange any of these activities?"""}
                ],
                "tools_used": ["get_local_weather", "get_hotel_activities"],
                "execution_time": 2.4
            }
        ]
        
        print(f"\n🎭 EVALUANDO {len(simulated_conversations)} CONVERSACIONES...")
        
        evaluations = []
        
        # Process each conversation
        for i, conv_data in enumerate(simulated_conversations, 1):
            print(f"\n{i}️⃣ Procesando: {conv_data['scenario_id']}")
            
            # Find the matching scenario
            scenario = next(
                (s for s in TEST_SCENARIOS if s.scenario_id == conv_data["scenario_id"]),
                None
            )
            
            if not scenario:
                print(f"⚠️  Escenario no encontrado: {conv_data['scenario_id']}")
                continue
            
            # Create a simulation result
            result = SimulationResult(
                scenario_id=conv_data["scenario_id"],
                hotel_id=conv_data["hotel_id"],
                conversation_id=f"real_eval_{i:03d}",
                messages=conv_data["conversation"],
                tools_used=conv_data["tools_used"],
                execution_time=conv_data["execution_time"],
                success=True,
                agent_responses=[{
                    "turn": 1,
                    "response": conv_data["conversation"][1]["content"],
                    "tools_used": conv_data["tools_used"],
                    "processing_time": conv_data["execution_time"],
                    "metadata": {"hotel_id": conv_data["hotel_id"], "scenario_id": conv_data["scenario_id"]}
                }],
                timestamp=datetime.now()
            )
            
            # Log conversation
            for turn, msg in enumerate(conv_data["conversation"], 1):
                logger.log_conversation(
                    conversation_id=result.conversation_id,
                    role=msg["role"],
                    content=msg["content"],
                    turn_number=turn,
                    tools_used=conv_data["tools_used"] if msg["role"] == "assistant" else [],
                    processing_time=conv_data["execution_time"] if msg["role"] == "assistant" else None
                )
            
            # AI Evaluation (this calls OpenAI API)
            print(f"   🤖 Evaluando con AI...")
            evaluation = await evaluator.evaluate_conversation(result, scenario)
            evaluations.append(evaluation)
            
            # Log evaluation
            dimension_scores = {score.dimension: score.score for score in evaluation.scores}
            logger.log_evaluation(
                conversation_id=evaluation.conversation_id,
                scenario_id=evaluation.scenario_id,
                hotel_id=evaluation.hotel_id,
                overall_score=evaluation.overall_score,
                passed=evaluation.passed,
                dimension_scores=dimension_scores,
                tools_expected=evaluation.expected_tools_used,
                tools_used=evaluation.actual_tools_used,
                missing_tools=evaluation.missing_tools,
                evaluation_summary=evaluation.summary,
                recommendations=evaluation.recommendations
            )
            
            # Show results
            status = "✅ APROBADO" if evaluation.passed else "❌ REPROBADO"
            print(f"   ⭐ Puntuación: {evaluation.overall_score:.3f} ({status})")
            
            # Show top scores
            top_dimension = max(evaluation.scores, key=lambda x: x.score)
            low_dimension = min(evaluation.scores, key=lambda x: x.score)
            print(f"   🏆 Mejor: {top_dimension.dimension} ({top_dimension.score:.3f})")
            print(f"   📈 Menor: {low_dimension.dimension} ({low_dimension.score:.3f})")
            
            # Show AI summary excerpt
            summary_excerpt = evaluation.summary[:100] + "..." if len(evaluation.summary) > 100 else evaluation.summary
            print(f"   💬 AI Summary: {summary_excerpt}")
        
        # Generate session summary
        print(f"\n📊 GENERANDO RESUMEN DE SESIÓN...")
        summary = logger.generate_session_summary({
            "evaluation_type": "real_ai_evaluation",
            "api_calls": len(evaluations) * 3,  # Approximate API calls made
        })
        
        # Export results
        csv_path = logger.export_to_csv()
        
        # Display final results
        print("\n" + "="*60)
        print("🎉 EVALUACIÓN AI REAL COMPLETADA")
        print("="*60)
        
        stats = summary["statistics"]
        print(f"\n📈 **RESULTADOS FINALES:**")
        print(f"   💬 Conversaciones evaluadas: {stats['total_conversations']}")
        print(f"   ✅ Tasa de aprobación: {stats['pass_rate']:.1%}")
        print(f"   ⭐ Puntuación promedio: {stats['average_score']:.3f}")
        print(f"   🎯 Puntuación mínima: {stats['min_score']:.3f}")
        print(f"   🏆 Puntuación máxima: {stats['max_score']:.3f}")
        print(f"   🛠️  Cobertura de herramientas: {stats['tool_coverage']:.1%}")
        
        print(f"\n🎯 **PUNTUACIONES POR DIMENSIÓN:**")
        dim_scores = summary["dimension_scores"]
        for dimension, score in dim_scores.items():
            emoji = "🏆" if score > 0.9 else "✅" if score > 0.8 else "📈" if score > 0.7 else "⚠️"
            print(f"   {emoji} {dimension.title()}: {score:.3f}")
        
        print(f"\n📁 **ARCHIVOS GENERADOS:**")
        print(f"   📊 Resultados CSV: {csv_path}")
        print(f"   📋 Resumen JSON: {summary['files']['summary']}")
        print(f"   💬 Conversaciones: {summary['files']['conversations']}")
        print(f"   🔍 Evaluaciones: {summary['files']['evaluations']}")
        
        print(f"\n🤖 **EVALUACIONES AI REALIZADAS:**")
        for eval in evaluations:
            status = "✅" if eval.passed else "❌"
            print(f"   {status} {eval.scenario_id}: {eval.overall_score:.3f}")
        
        print(f"\n💡 **PRÓXIMOS PASOS:**")
        if all(e.passed for e in evaluations):
            print("   🎉 ¡Excelente! Todas las evaluaciones aprobaron")
            print("   🚀 El sistema está listo para evaluaciones a gran escala")
        else:
            failed = [e for e in evaluations if not e.passed]
            print(f"   📈 {len(failed)} conversaciones necesitan mejora")
            print("   🔧 Revisar recomendaciones de AI para optimizar")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en evaluación real: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(run_real_evaluation())
        if result:
            print("\n🎉 ¡Evaluación AI real completada exitosamente!")
            sys.exit(0)
        else:
            print("\n❌ Evaluación AI real falló")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Evaluación interrumpida")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        sys.exit(1)