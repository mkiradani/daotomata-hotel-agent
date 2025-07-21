#!/usr/bin/env python3
"""
Test real AI evaluation with OpenAI API.
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

async def test_real_ai_evaluation():
    """Test the AI evaluation system with real OpenAI API."""
    
    print("🤖 TESTING REAL AI EVALUATION SYSTEM")
    print("="*50)
    
    # Check API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found!")
        return False
    
    print(f"✅ API Key found: {api_key[:20]}...")
    
    try:
        from openai import AsyncOpenAI
        from tests.ai_evaluation.evaluator import AIEvaluator, ResponseEvaluation
        from tests.ai_evaluation.config import ConversationScenario
        from tests.ai_evaluation.logger import ConversationLogger
        
        print("✅ Imports successful")
        
        # Initialize components
        client = AsyncOpenAI(api_key=api_key)
        evaluator = AIEvaluator(client)
        logger = ConversationLogger()
        
        print("✅ AI Evaluator initialized")
        
        # Create a test conversation scenario
        test_scenario = ConversationScenario(
            scenario_id="test_ai_real",
            hotel_id="hotel_madrid_luxury",
            title="Real AI Test",
            description="Testing real AI evaluation",
            initial_message="Can you tell me about your hotel?",
            expected_tools=["get_hotel_info", "get_hotel_facilities"],
            success_criteria=["Provides hotel information", "Professional response"]
        )
        
        # Test response for evaluation
        test_response_data = {
            "turn": 1,
            "response": """**Hotel Madrid Palace**

Welcome to Hotel Madrid Palace, a luxury 5-star hotel in the heart of Madrid!

Our hotel features elegant rooms and suites, world-class amenities including a full-service spa, fitness center, fine dining restaurant, and rooftop bar with stunning city views. 

We're perfectly located near the Royal Palace, Prado Museum, and Madrid's best shopping districts. Our dedicated concierge team is available 24/7 to assist with restaurant reservations, tour bookings, and any special requests.

How can I help make your stay memorable?""",
            "tools_used": ["get_hotel_info", "get_hotel_facilities"],
            "processing_time": 1.5,
            "metadata": {"hotel_id": "hotel_madrid_luxury", "scenario_id": "test_ai_real"}
        }
        
        print("\n🎯 Testing single response evaluation...")
        
        # Test single response evaluation
        response_eval = await evaluator._evaluate_single_response(
            test_response_data, test_scenario, type('MockResult', (), {
                'conversation_id': 'test_001',
                'scenario_id': 'test_ai_real', 
                'hotel_id': 'hotel_madrid_luxury',
                'tools_used': ['get_hotel_info', 'get_hotel_facilities'],
                'execution_time': 2.5,
                'success': True,
                'messages': [
                    {'role': 'user', 'content': 'Can you tell me about your hotel?'},
                    {'role': 'assistant', 'content': test_response_data['response']}
                ]
            })()
        )
        
        print(f"✅ AI Response Evaluation completed!")
        print(f"   📊 Accuracy Score: {response_eval.accuracy_score:.3f}")
        print(f"   🤝 Helpfulness Score: {response_eval.helpfulness_score:.3f}")
        print(f"   😊 Politeness Score: {response_eval.politeness_score:.3f}")
        print(f"   🛠️  Tool Usage Appropriate: {response_eval.tool_usage_appropriate}")
        
        if response_eval.strengths:
            print(f"   ✅ Strengths: {', '.join(response_eval.strengths[:2])}")
        if response_eval.issues:
            print(f"   ⚠️  Issues: {', '.join(response_eval.issues[:2])}")
        
        # Test conversation flow evaluation
        print("\n🌊 Testing conversation flow evaluation...")
        
        mock_result = type('MockResult', (), {
            'conversation_id': 'test_flow_001',
            'scenario_id': 'test_ai_real',
            'hotel_id': 'hotel_madrid_luxury',
            'tools_used': ['get_hotel_info', 'get_hotel_facilities'], 
            'execution_time': 3.2,
            'success': True,
            'messages': [
                {'role': 'user', 'content': 'Can you tell me about your hotel?'},
                {'role': 'assistant', 'content': test_response_data['response']},
                {'role': 'user', 'content': 'That sounds great! Do you have a spa?'},
                {'role': 'assistant', 'content': 'Yes! Our full-service spa offers massages, treatments, and relaxation areas. Would you like me to check availability for any specific services?'}
            ]
        })()
        
        flow_score = await evaluator._evaluate_conversation_flow(mock_result, test_scenario)
        print(f"✅ Conversation Flow Score: {flow_score:.3f}")
        
        # Test evaluation summary generation
        print("\n📝 Testing evaluation summary generation...")
        
        mock_scores = [
            type('Score', (), {'dimension': 'accuracy', 'score': response_eval.accuracy_score, 'weight': 0.3})(),
            type('Score', (), {'dimension': 'helpfulness', 'score': response_eval.helpfulness_score, 'weight': 0.2})(),
            type('Score', (), {'dimension': 'politeness', 'score': response_eval.politeness_score, 'weight': 0.15})(),
        ]
        
        overall_score = sum(s.score * s.weight for s in mock_scores) / sum(s.weight for s in mock_scores)
        
        summary = await evaluator._generate_evaluation_summary(
            mock_result, test_scenario, mock_scores, overall_score
        )
        
        print(f"✅ AI Generated Summary:")
        print(f"   {summary}")
        
        print("\n" + "="*50)
        print("🎉 REAL AI EVALUATION TEST SUCCESSFUL!")
        print("="*50)
        
        print(f"\n📊 **TEST RESULTS:**")
        print(f"   🎯 Overall Performance: {overall_score:.3f}")
        print(f"   🤖 AI Accuracy: {response_eval.accuracy_score:.3f}")
        print(f"   🤝 AI Helpfulness: {response_eval.helpfulness_score:.3f}")
        print(f"   😊 AI Politeness: {response_eval.politeness_score:.3f}")
        print(f"   🌊 Conversation Flow: {flow_score:.3f}")
        
        print(f"\n✅ **SYSTEM STATUS:**")
        print("   🟢 OpenAI API connection working")
        print("   🟢 AI evaluation pipeline functional") 
        print("   🟢 Response analysis working")
        print("   🟢 Summary generation working")
        print("   🟢 Ready for full conversation testing")
        
        return True
        
    except Exception as e:
        print(f"❌ AI Evaluation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_real_ai_evaluation())
        if result:
            print("\n🎉 ✅ Real AI evaluation system is working perfectly!")
            print("\n🚀 Ready to run full evaluation suite:")
            print("   python -m tests.ai_evaluation.main --run-all")
            sys.exit(0)
        else:
            print("\n❌ Real AI evaluation test failed")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        sys.exit(1)