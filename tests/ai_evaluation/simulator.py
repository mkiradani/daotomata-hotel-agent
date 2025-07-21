"""Conversation simulator for testing hotel agent interactions."""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import sys

# Add project root to path
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
sys.path.insert(0, str(project_root))

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.agents.hotel_agents import HotelAgent
from app.models import ChatMessage
from .config import TEST_HOTELS, TEST_SCENARIOS, HotelConfig, ConversationScenario
from .logger import ConversationLogger


class SimulationResult(BaseModel):
    """Result of a conversation simulation."""
    
    scenario_id: str
    hotel_id: str
    conversation_id: str
    messages: List[Dict[str, Any]]
    tools_used: List[str]
    execution_time: float
    success: bool
    error_message: Optional[str] = None
    agent_responses: List[Dict[str, Any]] = []
    timestamp: datetime


class ConversationSimulator:
    """Simulates conversations between users and hotel agents."""
    
    def __init__(self, openai_client: Optional[AsyncOpenAI] = None):
        """Initialize the conversation simulator.
        
        Args:
            openai_client: Optional OpenAI client. If not provided, will create one.
        """
        self.openai_client = openai_client or AsyncOpenAI()
        self.logger = ConversationLogger()
        self.agents: Dict[str, HotelAgent] = {}
        
    async def setup_test_hotels(self) -> None:
        """Setup test hotel configurations in the system."""
        for hotel in TEST_HOTELS:
            # Create mock hotel data structure
            hotel_data = {
                "id": hotel.id,
                "name": hotel.name,
                "description": hotel.description,
                "address": {
                    "city": hotel.city,
                    "country": hotel.country
                },
                "contact_email": hotel.contact_email,
                "contact_phone": hotel.contact_phone,
                "latitude": hotel.coordinates[0],
                "longitude": hotel.coordinates[1],
                "facilities": [
                    {"name": facility, "category": "General", "description": f"{facility.title()} facility"}
                    for facility in hotel.facilities
                ],
                "activities": hotel.activities
            }
            
            # Create hotel agent for this hotel
            self.agents[hotel.id] = HotelAgent(hotel_id=hotel.id)
            
            self.logger.log_info(f"Setup test hotel: {hotel.name} ({hotel.id})")
    
    async def simulate_conversation(
        self, 
        scenario: ConversationScenario,
        max_turns: int = 10
    ) -> SimulationResult:
        """Simulate a conversation based on a scenario.
        
        Args:
            scenario: The conversation scenario to simulate
            max_turns: Maximum number of conversation turns
            
        Returns:
            SimulationResult: Result of the simulation
        """
        start_time = datetime.now()
        conversation_id = str(uuid.uuid4())[:8]
        
        self.logger.log_info(f"Starting simulation: {scenario.title} (ID: {conversation_id})")
        
        try:
            # Get hotel agent
            agent = self.agents.get(scenario.hotel_id)
            if not agent:
                raise ValueError(f"No agent found for hotel: {scenario.hotel_id}")
            
            # Initialize conversation tracking
            messages = []
            tools_used = []
            agent_responses = []
            
            # Start with the initial message
            current_message = scenario.initial_message
            turn_count = 0
            
            while turn_count < max_turns:
                turn_count += 1
                
                # Log user message
                self.logger.log_conversation(
                    conversation_id=conversation_id,
                    role="user", 
                    content=current_message,
                    turn_number=turn_count
                )
                
                messages.append({
                    "role": "user",
                    "content": current_message,
                    "timestamp": datetime.now().isoformat(),
                    "turn": turn_count
                })
                
                # Get agent response
                chat_message = ChatMessage(
                    message=current_message,
                    user_id=f"test_user_{conversation_id}",
                    session_id=conversation_id,
                    hotel_id=scenario.hotel_id
                )
                
                # Process message with agent
                agent_start = datetime.now()
                try:
                    response = await agent.process_message(chat_message)
                    agent_duration = (datetime.now() - agent_start).total_seconds()
                    
                    # Extract tools used from response (if available)
                    used_tools = self._extract_tools_from_response(response)
                    tools_used.extend(used_tools)
                    
                    # Log agent response
                    self.logger.log_conversation(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=response.response,
                        turn_number=turn_count,
                        tools_used=used_tools,
                        processing_time=agent_duration
                    )
                    
                    messages.append({
                        "role": "assistant",
                        "content": response.response,
                        "timestamp": datetime.now().isoformat(),
                        "turn": turn_count,
                        "tools_used": used_tools,
                        "processing_time": agent_duration
                    })
                    
                    agent_responses.append({
                        "turn": turn_count,
                        "response": response.response,
                        "tools_used": used_tools,
                        "processing_time": agent_duration,
                        "metadata": {
                            "hotel_id": scenario.hotel_id,
                            "scenario_id": scenario.scenario_id
                        }
                    })
                    
                except Exception as e:
                    error_msg = f"Agent error on turn {turn_count}: {str(e)}"
                    self.logger.log_error(error_msg, conversation_id=conversation_id)
                    raise e
                
                # Check if we should continue based on scenario flow
                if turn_count < len(scenario.conversation_flow):
                    # Get next user message from scenario
                    next_turn = scenario.conversation_flow[turn_count]
                    if next_turn["role"] == "user":
                        current_message = next_turn["content"]
                    else:
                        break  # End if no more user messages
                else:
                    # Generate a follow-up message or end conversation
                    if turn_count < 3:  # Continue with automatic follow-ups
                        current_message = await self._generate_followup_message(
                            messages, scenario
                        )
                    else:
                        break
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = SimulationResult(
                scenario_id=scenario.scenario_id,
                hotel_id=scenario.hotel_id,
                conversation_id=conversation_id,
                messages=messages,
                tools_used=list(set(tools_used)),  # Remove duplicates
                execution_time=execution_time,
                success=True,
                agent_responses=agent_responses,
                timestamp=start_time
            )
            
            self.logger.log_info(
                f"Completed simulation: {scenario.title} "
                f"({turn_count} turns, {execution_time:.2f}s, "
                f"tools: {', '.join(result.tools_used)})"
            )
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Simulation failed: {str(e)}"
            
            self.logger.log_error(error_msg, conversation_id=conversation_id)
            
            return SimulationResult(
                scenario_id=scenario.scenario_id,
                hotel_id=scenario.hotel_id,
                conversation_id=conversation_id,
                messages=messages if 'messages' in locals() else [],
                tools_used=tools_used if 'tools_used' in locals() else [],
                execution_time=execution_time,
                success=False,
                error_message=error_msg,
                agent_responses=agent_responses if 'agent_responses' in locals() else [],
                timestamp=start_time
            )
    
    def _extract_tools_from_response(self, response) -> List[str]:
        """Extract tool names used from agent response."""
        tools_used = []
        
        # This is a simplified extraction - in a real implementation,
        # you would integrate with the OpenAI Agents framework to track tool usage
        response_text = response.response.lower() if hasattr(response, 'response') else str(response).lower()
        
        # Look for tool indicators in the response
        tool_indicators = {
            "get_hotel_info": ["hotel information", "hotel details", "about our hotel"],
            "check_room_availability": ["availability", "rooms available", "room check"],
            "get_hotel_activities": ["activities", "experiences", "things to do"],
            "get_hotel_facilities": ["facilities", "amenities", "services"],
            "get_local_weather": ["weather", "temperature", "forecast"],
            "request_hotel_service": ["service request", "request submitted", "request id"]
        }
        
        for tool_name, indicators in tool_indicators.items():
            if any(indicator in response_text for indicator in indicators):
                tools_used.append(tool_name)
        
        return tools_used
    
    async def _generate_followup_message(
        self, 
        messages: List[Dict[str, Any]], 
        scenario: ConversationScenario
    ) -> str:
        """Generate a realistic follow-up message based on conversation context."""
        
        # Simple follow-up messages based on scenario type
        followups = {
            "basic_info_inquiry": [
                "That sounds perfect! Do you have a pool?",
                "What are your check-in and check-out times?",
                "Thank you for the information!"
            ],
            "availability_check": [
                "What about pricing for those rooms?",
                "Do any rooms have a balcony?", 
                "How can I make a reservation?"
            ],
            "weather_and_activities": [
                "That's great weather! Any indoor activities too?",
                "How much do the activities cost?",
                "Can you help me book the tour?"
            ],
            "service_request": [
                "How long will that take?",
                "Thank you for the quick service!",
                "Is there anything else you can help with?"
            ],
            "complex_multi_tool": [
                "Perfect! Can you help me book the sailing trip?",
                "What's the best way to make a spa reservation?",
                "This is exactly what I needed, thank you!"
            ]
        }
        
        scenario_followups = followups.get(scenario.scenario_id, ["Thank you for your help!"])
        
        # Choose based on turn number or randomly
        turn_number = len([m for m in messages if m["role"] == "user"])
        if turn_number < len(scenario_followups):
            return scenario_followups[turn_number - 1]
        else:
            return "Thank you for all your help!"
    
    async def run_all_scenarios(
        self,
        hotel_filter: Optional[List[str]] = None,
        scenario_filter: Optional[List[str]] = None
    ) -> List[SimulationResult]:
        """Run all configured test scenarios.
        
        Args:
            hotel_filter: Optional list of hotel IDs to test
            scenario_filter: Optional list of scenario IDs to test
            
        Returns:
            List of simulation results
        """
        await self.setup_test_hotels()
        
        scenarios_to_run = TEST_SCENARIOS
        
        # Apply filters
        if scenario_filter:
            scenarios_to_run = [s for s in scenarios_to_run if s.scenario_id in scenario_filter]
        
        if hotel_filter:
            # For hotel filter, we need to modify scenarios to use only those hotels
            # For simplicity, we'll run each scenario on each filtered hotel
            filtered_scenarios = []
            for scenario in scenarios_to_run:
                for hotel_id in hotel_filter:
                    if hotel_id in [h.id for h in TEST_HOTELS]:
                        modified_scenario = scenario.model_copy()
                        modified_scenario.hotel_id = hotel_id
                        modified_scenario.scenario_id = f"{scenario.scenario_id}_{hotel_id}"
                        filtered_scenarios.append(modified_scenario)
            scenarios_to_run = filtered_scenarios
        
        results = []
        
        self.logger.log_info(f"Running {len(scenarios_to_run)} scenarios")
        
        for scenario in scenarios_to_run:
            try:
                result = await self.simulate_conversation(scenario)
                results.append(result)
                
                # Small delay between scenarios to avoid rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.log_error(f"Failed to run scenario {scenario.scenario_id}: {str(e)}")
                # Continue with other scenarios
        
        self.logger.log_info(f"Completed {len(results)} simulations")
        
        return results
    
    async def run_single_scenario(
        self, 
        scenario_id: str, 
        hotel_id: Optional[str] = None
    ) -> Optional[SimulationResult]:
        """Run a single scenario by ID.
        
        Args:
            scenario_id: ID of the scenario to run
            hotel_id: Optional hotel ID to override scenario default
            
        Returns:
            Simulation result or None if scenario not found
        """
        await self.setup_test_hotels()
        
        # Find the scenario
        scenario = None
        for s in TEST_SCENARIOS:
            if s.scenario_id == scenario_id:
                scenario = s.model_copy()
                if hotel_id:
                    scenario.hotel_id = hotel_id
                break
        
        if not scenario:
            self.logger.log_error(f"Scenario not found: {scenario_id}")
            return None
        
        return await self.simulate_conversation(scenario)