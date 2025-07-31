#!/usr/bin/env python3
"""
AI Evaluation Test - Simula conversaciones realistas con el hotel agent
"""

import asyncio
import httpx
import json
from datetime import datetime
import time

# Test scenarios que simulan conversaciones reales
TEST_SCENARIOS = [
    {
        "id": "booking_inquiry",
        "name": "Booking Inquiry Flow",
        "messages": [
            {
                "message": "Hi! I'm looking to book a room for tonight. What do you have available?",
                "expected_tools": ["check_room_availability", "get_hotel_info"],
                "expected_agent": "booking_agent"
            }
        ]
    },
    {
        "id": "concierge_recommendations", 
        "name": "Concierge Recommendations",
        "messages": [
            {
                "message": "What are some good restaurants nearby? I'm interested in local cuisine.",
                "expected_tools": ["get_local_weather", "get_hotel_info"],
                "expected_agent": "concierge_agent"
            }
        ]
    },
    {
        "id": "hotel_services",
        "name": "Hotel Services Inquiry",
        "messages": [
            {
                "message": "What services and facilities does the hotel offer?",
                "expected_tools": ["get_hotel_facilities", "get_hotel_info"],
                "expected_agent": "triage_agent"
            }
        ]
    },
    {
        "id": "weather_activities",
        "name": "Weather and Activities",
        "messages": [
            {
                "message": "What's the weather like today? Any recommendations for outdoor activities?",
                "expected_tools": ["get_local_weather", "get_hotel_activities"],
                "expected_agent": "concierge_agent"
            }
        ]
    },
    {
        "id": "service_request",
        "name": "Service Request",
        "messages": [
            {
                "message": "I need extra towels in my room 205. Can you arrange that?",
                "expected_tools": ["request_hotel_service"],
                "expected_agent": "service_agent"
            }
        ]
    }
]

class AIEvaluator:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.results = []
        
    async def run_scenario(self, scenario):
        """Ejecuta un scenario de conversación y evalúa los resultados."""
        print(f"\n🧪 Testing: {scenario['name']}")
        
        scenario_results = {
            "id": scenario["id"],
            "name": scenario["name"],
            "messages": [],
            "passed": True,
            "errors": []
        }
        
        session_id = f"test_{scenario['id']}_{int(time.time())}"
        
        for i, test_msg in enumerate(scenario["messages"]):
            print(f"  📤 User: {test_msg['message'][:50]}...")
            
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        f"{self.base_url}/api/chat/",
                        json={
                            "message": test_msg["message"],
                            "session_id": session_id,
                            "hotel_id": "test-hotel-evaluation"
                        }
                    )
                    
                    if response.status_code != 200:
                        scenario_results["passed"] = False
                        scenario_results["errors"].append(f"HTTP {response.status_code}: {response.text}")
                        continue
                        
                    result = response.json()
                    
                    print(f"  📥 Agent: {result.get('agent_used', 'unknown')}")
                    print(f"  📝 Response: {result.get('message', '')[:100]}...")
                    print(f"  🔧 Tools: {result.get('tools_used', [])}")
                    
                    # Validaciones
                    message_result = {
                        "user_message": test_msg["message"],
                        "agent_response": result.get("message", ""),
                        "agent_used": result.get("agent_used", ""),
                        "tools_used": result.get("tools_used", []),
                        "validations": {}
                    }
                    
                    # Validar que hay respuesta
                    if not result.get("message"):
                        scenario_results["passed"] = False
                        scenario_results["errors"].append("Empty response from agent")
                        message_result["validations"]["has_response"] = False
                    else:
                        message_result["validations"]["has_response"] = True
                        
                    # Validar longitud de respuesta (debe ser útil)
                    response_length = len(result.get("message", ""))
                    if response_length < 20:
                        scenario_results["passed"] = False
                        scenario_results["errors"].append(f"Response too short: {response_length} chars")
                        message_result["validations"]["adequate_length"] = False
                    else:
                        message_result["validations"]["adequate_length"] = True
                        
                    # Validar que no hay errores obvios en la respuesta
                    error_indicators = ["error", "technical difficulties", "try again", "not available"]
                    response_lower = result.get("message", "").lower()
                    has_error = any(indicator in response_lower for indicator in error_indicators)
                    
                    if has_error:
                        print(f"  ⚠️  Response contains error indicators")
                        message_result["validations"]["no_error_indicators"] = False
                    else:
                        message_result["validations"]["no_error_indicators"] = True
                        
                    scenario_results["messages"].append(message_result)
                    
            except Exception as e:
                print(f"  ❌ Error: {e}")
                scenario_results["passed"] = False
                scenario_results["errors"].append(f"Exception: {str(e)}")
                
        # Evaluar resultado general del scenario
        if scenario_results["passed"]:
            print(f"  ✅ {scenario['name']}: PASSED")
        else:
            print(f"  ❌ {scenario['name']}: FAILED")
            for error in scenario_results["errors"]:
                print(f"     - {error}")
                
        self.results.append(scenario_results)
        return scenario_results
        
    async def run_all_scenarios(self):
        """Ejecuta todos los scenarios de test."""
        print("🚀 Starting AI Evaluation Tests")
        print(f"📍 Testing against: {self.base_url}")
        print(f"🧪 Running {len(TEST_SCENARIOS)} scenarios")
        
        start_time = datetime.now()
        
        for scenario in TEST_SCENARIOS:
            await self.run_scenario(scenario)
            await asyncio.sleep(1)  # Pequeña pausa entre tests
            
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Resumen final
        passed_scenarios = sum(1 for r in self.results if r["passed"])
        total_scenarios = len(self.results)
        
        print("\n" + "="*60)
        print("📊 AI EVALUATION SUMMARY")
        print("="*60)
        print(f"🎯 Scenarios Passed: {passed_scenarios}/{total_scenarios}")
        print(f"📈 Success Rate: {(passed_scenarios/total_scenarios)*100:.1f}%")
        print(f"⏱️  Total Duration: {duration:.1f}s")
        print(f"📅 Completed: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if passed_scenarios == total_scenarios:
            print("🎉 ALL TESTS PASSED! The hotel agent is working perfectly.")
        else:
            print("⚠️  Some tests failed. Review the errors above.")
            
        # Guardar resultados
        results_file = f"ai_evaluation_results_{int(time.time())}.json"
        with open(results_file, "w") as f:
            json.dump({
                "summary": {
                    "passed_scenarios": passed_scenarios,
                    "total_scenarios": total_scenarios,
                    "success_rate": (passed_scenarios/total_scenarios)*100,
                    "duration_seconds": duration,
                    "completed_at": end_time.isoformat()
                },
                "scenarios": self.results
            }, f, indent=2)
            
        print(f"💾 Results saved to: {results_file}")
        
        return passed_scenarios == total_scenarios

async def main():
    """Función principal de evaluación."""
    evaluator = AIEvaluator()
    
    # Verificar que el servidor esté corriendo
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{evaluator.base_url}/health")
            if response.status_code != 200:
                print(f"❌ Server not healthy: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return False
        
    print("✅ Server is healthy, starting evaluation...")
    
    # Ejecutar evaluación completa
    success = await evaluator.run_all_scenarios()
    return success

if __name__ == "__main__":
    asyncio.run(main())