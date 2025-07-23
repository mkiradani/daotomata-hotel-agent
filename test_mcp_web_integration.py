#!/usr/bin/env python3
"""
Integration test for MCP in web context
"""

import asyncio
import requests
import time
import subprocess
import signal
import os
from contextlib import asynccontextmanager

async def test_mcp_web_integration():
    """Test MCP functionality in web API context."""
    print("🧪 Testing MCP integration in web context...")
    
    # Start the FastAPI server
    print("🚀 Starting FastAPI server...")
    server_process = subprocess.Popen([
        "python", "-m", "uvicorn", "main:app", 
        "--host", "0.0.0.0", "--port", "3000"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    try:
        # Wait for server to start
        time.sleep(8)
        
        # Test 1: Basic MCP endpoint test
        print("📝 Test 1: Basic MCP endpoint...")
        response = requests.post(
            "http://localhost:3000/api/chat-mcp/test",
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Status: {result['status']}")
            print(f"🤖 Agent: {result['agent_used']}")
            print(f"📄 Response preview: {result['test_response'][:100]}...")
            
            # Check if we got real data (not error handler)
            if result['agent_used'] != 'error_handler' and 'facilities' in result['test_response'].lower():
                print("✅ MCP integration working - got real hotel data!")
                test1_success = True
            else:
                print("❌ Still getting error handler response")
                test1_success = False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            test1_success = False
        
        # Test 2: Chat endpoint with hotel context
        print("\n📝 Test 2: Chat endpoint with hotel context...")
        chat_request = {
            "message": "What are the available room types and their rates?",
            "session_id": "test-integration-session",
            "hotel_id": "1"
        }
        
        response = requests.post(
            "http://localhost:3000/api/chat-mcp/",
            json=chat_request,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Status: Success")
            print(f"🤖 Agent: {result['agent_used']}")
            print(f"📄 Response preview: {result['message'][:150]}...")
            
            # Check if hotel context is working
            if result['agent_used'] != 'error_handler':
                print("✅ Hotel context working - got agent response!")
                test2_success = True
            else:
                print("❌ Still getting error handler response")
                test2_success = False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            test2_success = False
        
        # Test 3: Session history
        print("\n📝 Test 3: Session history...")
        response = requests.get(
            f"http://localhost:3000/api/chat-mcp/sessions/{chat_request['session_id']}/history",
            timeout=10
        )
        
        if response.status_code == 200:
            history = response.json()
            print(f"✅ History retrieved: {len(history)} messages")
            test3_success = True
        else:
            print(f"❌ History error: {response.status_code}")
            test3_success = False
        
        # Overall result
        all_tests_passed = test1_success and test2_success and test3_success
        
        if all_tests_passed:
            print("\n🎉 All MCP web integration tests PASSED!")
        else:
            print("\n💥 Some MCP web integration tests FAILED!")
        
        return all_tests_passed
        
    finally:
        # Clean up server process
        print("\n🛑 Stopping server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()

if __name__ == "__main__":
    success = asyncio.run(test_mcp_web_integration())
    exit(0 if success else 1)