#!/usr/bin/env python3
"""
Test de AI Evaluation con MCP de Directus - Datos reales
"""

import asyncio
import httpx
import json
from datetime import datetime
import time

# Test scenarios con datos reales de Directus
MCP_TEST_SCENARIOS = [
    {
        "id": "directus_hotel_info",
        "name": "Hotel Information from Directus",
        "messages": [
            {
                "message": "Tell me about Maison Demo hotel - what services and facilities does it offer?",
                "expected_data": ["Maison Demo", "facilities", "services"],
                "hotel_id": "1"
            }
        ]
    },
    {
        "id": "directus_hotel_list",
        "name": "List All Hotels from Directus",
        "messages": [
            {
                "message": "What hotels are available in your system? Show me their names and details.",
                "expected_data": ["Maison Demo", "Baberrih Hotel"],
                "hotel_id": None
            }
        ]
    },
    {
        "id": "baberrih_hotel_info",
        "name": "Baberrih Hotel Information",
        "messages": [
            {
                "message": "Can you tell me about Baberrih Hotel and what it offers?",
                "expected_data": ["Baberrih Hotel", "information"],
                "hotel_id": "2"
            }
        ]
    },
    {
        "id": "directus_booking_inquiry",
        "name": "Booking Inquiry with Real Data",
        "messages": [
            {
                "message": "I want to book a room at Maison Demo for tomorrow. What room types are available?",
                "expected_data": ["Maison Demo", "room", "available"],
                "hotel_id": "1"
            }
        ]
    },
]

class MCPAIEvaluator:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.results = []
        
    async def run_scenario(self, scenario):
        """Ejecuta un scenario con MCP y evalúa los resultados."""
        print(f"\n🧪 Testing MCP: {scenario['name']}")
        
        scenario_results = {
            "id": scenario["id"],
            "name": scenario["name"],
            "messages": [],
            "passed": True,
            "errors": [],
            "mcp_data_found": False
        }
        
        session_id = f"mcp_test_{scenario['id']}_{int(time.time())}"
        
        for i, test_msg in enumerate(scenario["messages"]):
            print(f"  📤 User: {test_msg['message'][:60]}...")
            
            try:
                # Probar endpoint MCP
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        f"{self.base_url}/api/chat-mcp/",
                        json={
                            "message": test_msg["message"],
                            "session_id": session_id,
                            "hotel_id": test_msg.get("hotel_id")
                        }
                    )
                    
                    if response.status_code != 200:
                        scenario_results["passed"] = False
                        scenario_results["errors"].append(f"HTTP {response.status_code}: {response.text}")
                        continue
                        
                    result = response.json()
                    
                    print(f"  📥 Agent: {result.get('agent_used', 'unknown')}")
                    response_text = result.get('message', '')
                    print(f"  📝 Response: {response_text[:100]}...")
                    print(f"  🔧 Tools: {result.get('tools_used', [])}")
                    
                    # Validaciones específicas para MCP
                    message_result = {
                        "user_message": test_msg["message"],
                        "agent_response": response_text,
                        "agent_used": result.get("agent_used", ""),
                        "tools_used": result.get("tools_used", []),
                        "validations": {}
                    }
                    
                    # Validar que hay respuesta
                    if not response_text:
                        scenario_results["passed"] = False
                        scenario_results["errors"].append("Empty response from MCP agent")
                        message_result["validations"]["has_response"] = False
                    else:
                        message_result["validations"]["has_response"] = True
                    
                    # Validar que contiene datos esperados
                    expected_data = test_msg.get("expected_data", [])
                    data_found = []
                    
                    for expected in expected_data:
                        if expected.lower() in response_text.lower():
                            data_found.append(expected)
                    
                    if data_found:
                        scenario_results["mcp_data_found"] = True
                        message_result["validations"]["expected_data_found"] = data_found
                        print(f"  ✅ Datos encontrados: {', '.join(data_found)}")
                    else:
                        scenario_results["passed"] = False
                        scenario_results["errors"].append(f"Expected data not found: {expected_data}")
                        message_result["validations"]["expected_data_found"] = []
                        print(f"  ❌ Datos esperados NO encontrados: {expected_data}")
                    
                    # Validar longitud de respuesta
                    if len(response_text) < 20:
                        scenario_results["passed"] = False
                        scenario_results["errors"].append(f"Response too short: {len(response_text)} chars")
                        message_result["validations"]["adequate_length"] = False
                    else:
                        message_result["validations"]["adequate_length"] = True
                        
                    scenario_results["messages"].append(message_result)
                    
            except Exception as e:
                print(f"  ❌ Error: {e}")
                scenario_results["passed"] = False
                scenario_results["errors"].append(f"Exception: {str(e)}")
                
        # Evaluar resultado general del scenario
        if scenario_results["passed"] and scenario_results["mcp_data_found"]:
            print(f"  ✅ {scenario['name']}: PASSED (MCP data verified)")
        elif scenario_results["passed"]:
            print(f"  ⚠️  {scenario['name']}: PASSED (but no MCP data found)")
        else:
            print(f"  ❌ {scenario['name']}: FAILED")
            for error in scenario_results["errors"]:
                print(f"     - {error}")
                
        self.results.append(scenario_results)
        return scenario_results
        
    async def run_all_scenarios(self):
        """Ejecuta todos los scenarios de test MCP."""
        print("🚀 Starting MCP AI Evaluation Tests")
        print(f"📍 Testing against: {self.base_url}")
        print(f"🧪 Running {len(MCP_TEST_SCENARIOS)} MCP scenarios")
        
        start_time = datetime.now()
        
        for scenario in MCP_TEST_SCENARIOS:
            await self.run_scenario(scenario)
            await asyncio.sleep(1)  # Pequeña pausa entre tests
            
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Resumen final
        passed_scenarios = sum(1 for r in self.results if r["passed"])
        mcp_data_scenarios = sum(1 for r in self.results if r["mcp_data_found"])
        total_scenarios = len(self.results)
        
        print("\n" + "="*70)
        print("📊 MCP AI EVALUATION SUMMARY")
        print("="*70)
        print(f"🎯 Scenarios Passed: {passed_scenarios}/{total_scenarios}")
        print(f"📈 Success Rate: {(passed_scenarios/total_scenarios)*100:.1f}%")
        print(f"🔗 MCP Data Found: {mcp_data_scenarios}/{total_scenarios}")
        print(f"📊 MCP Data Rate: {(mcp_data_scenarios/total_scenarios)*100:.1f}%")
        print(f"⏱️  Total Duration: {duration:.1f}s")
        print(f"📅 Completed: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if passed_scenarios == total_scenarios and mcp_data_scenarios > 0:
            print("🎉 ALL MCP TESTS PASSED! Directus data integration working perfectly.")
        elif passed_scenarios == total_scenarios:
            print("✅ All tests passed, but MCP data needs verification.")
        else:
            print("⚠️  Some MCP tests failed. Review the errors above.")
            
        # Guardar resultados
        results_file = f"mcp_evaluation_results_{int(time.time())}.json"
        with open(results_file, "w") as f:
            json.dump({
                "summary": {
                    "passed_scenarios": passed_scenarios,
                    "total_scenarios": total_scenarios,
                    "success_rate": (passed_scenarios/total_scenarios)*100,
                    "mcp_data_scenarios": mcp_data_scenarios,
                    "mcp_data_rate": (mcp_data_scenarios/total_scenarios)*100,
                    "duration_seconds": duration,
                    "completed_at": end_time.isoformat()
                },
                "scenarios": self.results
            }, f, indent=2)
            
        print(f"💾 MCP Results saved to: {results_file}")
        
        return passed_scenarios == total_scenarios and mcp_data_scenarios > 0

async def main():
    """Función principal de evaluación MCP."""
    evaluator = MCPAIEvaluator()
    
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
        
    print("✅ Server is healthy, starting MCP evaluation...")
    
    # Ejecutar evaluación MCP completa
    success = await evaluator.run_all_scenarios()
    return success

if __name__ == "__main__":
    asyncio.run(main())