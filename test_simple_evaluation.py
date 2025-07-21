#!/usr/bin/env python3
"""
Simple test script to verify the AI evaluation system works.
"""

import asyncio
import os
from pathlib import Path
import sys

# Add project root to path
current_file = Path(__file__).resolve()
project_root = current_file.parent
sys.path.insert(0, str(project_root))

async def test_basic_functionality():
    """Test basic functionality of the AI evaluation system."""
    
    print("🧪 Testing AI Evaluation System")
    print("="*50)
    
    # Test 1: Config and basic imports
    print("\n1️⃣ Testing imports...")
    try:
        from tests.ai_evaluation.config import TEST_HOTELS, TEST_SCENARIOS, AVAILABLE_TOOLS
        from tests.ai_evaluation.logger import ConversationLogger
        print(f"✅ Config loaded: {len(TEST_HOTELS)} hotels, {len(TEST_SCENARIOS)} scenarios")
        print(f"✅ Available tools: {', '.join(AVAILABLE_TOOLS)}")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Test 2: Logger functionality
    print("\n2️⃣ Testing logger...")
    try:
        logger = ConversationLogger()
        logger.log_info("Test log message")
        
        # Test conversation logging
        logger.log_conversation(
            conversation_id="test_001",
            role="user",
            content="Hello, I need information about your hotel",
            turn_number=1
        )
        
        logger.log_conversation(
            conversation_id="test_001", 
            role="assistant",
            content="I'd be happy to help you with information about our hotel!",
            turn_number=1,
            tools_used=["get_hotel_info"],
            processing_time=1.5
        )
        
        print("✅ Logging works correctly")
    except Exception as e:
        print(f"❌ Logger failed: {e}")
        return False
    
    # Test 3: Tool access (simplified)
    print("\n3️⃣ Testing tool access...")
    try:
        from app.agents.tools import get_hotel_info
        print("✅ Tool import successful")
        print(f"   Tool type: {type(get_hotel_info)}")
    except Exception as e:
        print(f"❌ Tool access failed: {e}")
        return False
    
    # Test 4: AI Evaluator (without OpenAI call)
    print("\n4️⃣ Testing AI evaluator structure...")
    try:
        # Only test if OPENAI_API_KEY is available
        if not os.getenv('OPENAI_API_KEY'):
            print("⚠️ Skipping AI evaluator test - no OpenAI API key")
        else:
            from tests.ai_evaluation.evaluator import AIEvaluator
            evaluator = AIEvaluator()
            print("✅ AI Evaluator created successfully")
    except Exception as e:
        print(f"❌ AI Evaluator failed: {e}")
        print("   This might be expected without proper OpenAI setup")
    
    # Test 5: Export functionality  
    print("\n5️⃣ Testing export functionality...")
    try:
        # Generate some test data
        logger.log_evaluation(
            conversation_id="test_001",
            scenario_id="basic_info_inquiry", 
            hotel_id="hotel_madrid_luxury",
            overall_score=0.85,
            passed=True,
            dimension_scores={
                "accuracy": 0.9,
                "helpfulness": 0.8,
                "tool_usage": 0.9,
                "conversation_flow": 0.8,
                "politeness": 0.85
            },
            tools_expected=["get_hotel_info"],
            tools_used=["get_hotel_info"],
            missing_tools=[],
            evaluation_summary="Good overall performance with appropriate tool usage",
            recommendations=["Maintain current quality level"]
        )
        
        # Test CSV export
        csv_path = logger.export_to_csv()
        print(f"✅ CSV export successful: {csv_path}")
        
        # Test session summary
        summary = logger.generate_session_summary()
        print(f"✅ Session summary generated: {len(summary)} fields")
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return False
    
    print("\n" + "="*50)
    print("🎉 Basic functionality test completed!")
    print("\n📋 Summary:")
    print("   ✅ Configuration and imports work")
    print("   ✅ Logging system functional")
    print("   ✅ Tool access available") 
    print("   ✅ Export functionality works")
    print("   ⚠️ AI evaluation requires OpenAI API key for full testing")
    
    print("\n🚀 Next steps to fully test:")
    print("   1. Set OPENAI_API_KEY environment variable")
    print("   2. Run: python -m tests.ai_evaluation.main --tools-only")
    print("   3. Run: python -m tests.ai_evaluation.main --conversations-only")
    
    return True

if __name__ == "__main__":
    result = asyncio.run(test_basic_functionality())
    if result:
        print("\n✅ All basic tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)