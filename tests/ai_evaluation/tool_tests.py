"""Comprehensive tests for all hotel agent tools."""

import asyncio
import json
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import sys

# Add project root to path
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
sys.path.insert(0, str(project_root))

from pydantic import BaseModel

from app.agents.tools import (
    get_hotel_info,
    check_room_availability,
    get_hotel_activities,
    get_hotel_facilities,
    get_local_weather,
    request_hotel_service
)
from app.agents.pms_tools import (
    check_real_room_availability,
    create_reservation,
    search_reservations,
    get_reservation_details,
    get_room_types_info
)
from .config import TEST_HOTELS, HotelConfig
from .logger import ConversationLogger


class ToolTestResult(BaseModel):
    """Result of a single tool test."""
    
    tool_name: str
    hotel_id: str
    test_case: str
    success: bool
    response_content: str
    execution_time: float
    error_message: Optional[str] = None
    response_length: int = 0
    contains_expected_content: bool = False
    timestamp: datetime


class MockContext:
    """Mock context for tool testing."""
    
    def __init__(self, hotel_id: str):
        self.hotel_id = hotel_id


class MockRunContextWrapper:
    """Mock run context wrapper for tool testing."""
    
    def __init__(self, hotel_id: str):
        self.context = MockContext(hotel_id)


class HotelToolTester:
    """Comprehensive tester for all hotel agent tools."""
    
    def __init__(self):
        """Initialize the hotel tool tester."""
        self.logger = ConversationLogger()
        self.test_results: List[ToolTestResult] = []
    
    async def test_all_tools(self, hotel_ids: Optional[List[str]] = None) -> List[ToolTestResult]:
        """Test all tools across all or specified hotels.
        
        Args:
            hotel_ids: Optional list of hotel IDs to test. If None, tests all configured hotels.
            
        Returns:
            List of tool test results
        """
        if hotel_ids is None:
            hotel_ids = [hotel.id for hotel in TEST_HOTELS]
        
        self.logger.log_info(f"Starting comprehensive tool testing for {len(hotel_ids)} hotels")
        
        for hotel_id in hotel_ids:
            await self.test_hotel_tools(hotel_id)
        
        self.logger.log_info(f"Completed tool testing: {len(self.test_results)} tests executed")
        
        return self.test_results
    
    async def test_hotel_tools(self, hotel_id: str) -> List[ToolTestResult]:
        """Test all tools for a specific hotel.
        
        Args:
            hotel_id: Hotel ID to test
            
        Returns:
            List of test results for this hotel
        """
        hotel_results = []
        
        self.logger.log_info(f"Testing all tools for hotel: {hotel_id}")
        
        # Create mock context
        ctx = MockRunContextWrapper(hotel_id)
        
        # Test basic hotel tools
        hotel_results.extend(await self._test_get_hotel_info(ctx, hotel_id))
        hotel_results.extend(await self._test_check_room_availability(ctx, hotel_id))
        hotel_results.extend(await self._test_get_hotel_activities(ctx, hotel_id))
        hotel_results.extend(await self._test_get_hotel_facilities(ctx, hotel_id))
        hotel_results.extend(await self._test_get_local_weather(ctx, hotel_id))
        hotel_results.extend(await self._test_request_hotel_service(ctx, hotel_id))
        
        # Test PMS tools (these might fail if PMS is not available)
        hotel_results.extend(await self._test_check_real_room_availability(ctx, hotel_id))
        hotel_results.extend(await self._test_create_reservation(ctx, hotel_id))
        hotel_results.extend(await self._test_search_reservations(ctx, hotel_id))
        hotel_results.extend(await self._test_get_reservation_details(ctx, hotel_id))
        hotel_results.extend(await self._test_get_room_types_info(ctx, hotel_id))
        
        self.test_results.extend(hotel_results)
        
        return hotel_results
    
    async def _test_get_hotel_info(self, ctx, hotel_id: str) -> List[ToolTestResult]:
        """Test get_hotel_info tool."""
        results = []
        
        # Test case 1: Basic hotel info
        result = await self._execute_tool_test(
            tool_name="get_hotel_info",
            hotel_id=hotel_id,
            test_case="basic_info",
            tool_function=lambda: get_hotel_info(ctx),
            expected_content=["hotel", "name", "address"]
        )
        results.append(result)
        
        # Test case 2: Explicit hotel_id parameter
        result = await self._execute_tool_test(
            tool_name="get_hotel_info",
            hotel_id=hotel_id,
            test_case="explicit_hotel_id",
            tool_function=lambda: get_hotel_info(ctx, hotel_id=hotel_id),
            expected_content=["hotel", "name"]
        )
        results.append(result)
        
        return results
    
    async def _test_check_room_availability(self, ctx, hotel_id: str) -> List[ToolTestResult]:
        """Test check_room_availability tool."""
        results = []
        
        # Test case 1: Valid future dates
        tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        next_week = (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        result = await self._execute_tool_test(
            tool_name="check_room_availability",
            hotel_id=hotel_id,
            test_case="valid_dates",
            tool_function=lambda: check_room_availability(
                ctx, check_in=tomorrow, check_out=next_week, guests=2
            ),
            expected_content=["availability", "room", "price", "nights"]
        )
        results.append(result)
        
        # Test case 2: Invalid dates (past date)
        yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        result = await self._execute_tool_test(
            tool_name="check_room_availability",
            hotel_id=hotel_id,
            test_case="invalid_past_date",
            tool_function=lambda: check_room_availability(
                ctx, check_in=yesterday, check_out=tomorrow, guests=2
            ),
            expected_content=["must be in the future", "error"]
        )
        results.append(result)
        
        # Test case 3: Many guests
        result = await self._execute_tool_test(
            tool_name="check_room_availability",
            hotel_id=hotel_id,
            test_case="many_guests",
            tool_function=lambda: check_room_availability(
                ctx, check_in=tomorrow, check_out=next_week, guests=6
            ),
            expected_content=["availability", "room"]
        )
        results.append(result)
        
        return results
    
    async def _test_get_hotel_activities(self, ctx, hotel_id: str) -> List[ToolTestResult]:
        """Test get_hotel_activities tool."""
        results = []
        
        # Test case 1: Get all activities
        result = await self._execute_tool_test(
            tool_name="get_hotel_activities",
            hotel_id=hotel_id,
            test_case="get_all_activities",
            tool_function=lambda: get_hotel_activities(ctx),
            expected_content=["activities", "experience"]
        )
        results.append(result)
        
        return results
    
    async def _test_get_hotel_facilities(self, ctx, hotel_id: str) -> List[ToolTestResult]:
        """Test get_hotel_facilities tool."""
        results = []
        
        # Test case 1: Get all facilities
        result = await self._execute_tool_test(
            tool_name="get_hotel_facilities",
            hotel_id=hotel_id,
            test_case="get_all_facilities",
            tool_function=lambda: get_hotel_facilities(ctx),
            expected_content=["facilities", "amenities"]
        )
        results.append(result)
        
        return results
    
    async def _test_get_local_weather(self, ctx, hotel_id: str) -> List[ToolTestResult]:
        """Test get_local_weather tool."""
        results = []
        
        # Test case 1: Get weather for hotel location
        result = await self._execute_tool_test(
            tool_name="get_local_weather",
            hotel_id=hotel_id,
            test_case="hotel_weather",
            tool_function=lambda: get_local_weather(ctx),
            expected_content=["weather", "temperature"]
        )
        results.append(result)
        
        # Test case 2: Get weather with activity advice
        result = await self._execute_tool_test(
            tool_name="get_local_weather",
            hotel_id=hotel_id,
            test_case="weather_with_activities",
            tool_function=lambda: get_local_weather(ctx, include_activity_advice=True),
            expected_content=["weather", "temperature", "activity", "advice"]
        )
        results.append(result)
        
        # Test case 3: Get weather for specific city
        result = await self._execute_tool_test(
            tool_name="get_local_weather",
            hotel_id=hotel_id,
            test_case="specific_city_weather",
            tool_function=lambda: get_local_weather(ctx, city="Madrid"),
            expected_content=["weather", "madrid"]
        )
        results.append(result)
        
        return results
    
    async def _test_request_hotel_service(self, ctx, hotel_id: str) -> List[ToolTestResult]:
        """Test request_hotel_service tool."""
        results = []
        
        # Test case 1: Housekeeping request
        result = await self._execute_tool_test(
            tool_name="request_hotel_service",
            hotel_id=hotel_id,
            test_case="housekeeping_request",
            tool_function=lambda: request_hotel_service(
                ctx, 
                service_type="housekeeping",
                description="Need extra towels",
                room_number="315",
                priority="normal"
            ),
            expected_content=["service request", "submitted", "request id"]
        )
        results.append(result)
        
        # Test case 2: Room service request
        result = await self._execute_tool_test(
            tool_name="request_hotel_service",
            hotel_id=hotel_id,
            test_case="room_service_request",
            tool_function=lambda: request_hotel_service(
                ctx,
                service_type="room_service",
                description="Continental breakfast to room 420",
                room_number="420",
                priority="high"
            ),
            expected_content=["service request", "submitted", "room service"]
        )
        results.append(result)
        
        # Test case 3: Maintenance request
        result = await self._execute_tool_test(
            tool_name="request_hotel_service",
            hotel_id=hotel_id,
            test_case="maintenance_request",
            tool_function=lambda: request_hotel_service(
                ctx,
                service_type="maintenance",
                description="Air conditioning not working in room 205",
                room_number="205",
                priority="urgent"
            ),
            expected_content=["service request", "maintenance", "urgent"]
        )
        results.append(result)
        
        return results
    
    # PMS Tools Tests (these may fail if PMS integration is not available)
    
    async def _test_check_real_room_availability(self, ctx, hotel_id: str) -> List[ToolTestResult]:
        """Test check_real_room_availability tool."""
        results = []
        
        tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        next_week = (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        # Test case 1: Valid dates with PMS
        result = await self._execute_tool_test(
            tool_name="check_real_room_availability",
            hotel_id=hotel_id,
            test_case="pms_valid_dates",
            tool_function=lambda: check_real_room_availability(
                ctx, check_in=tomorrow, check_out=next_week, guests=2
            ),
            expected_content=["availability", "room", "pms"],
            allow_pms_unavailable=True
        )
        results.append(result)
        
        return results
    
    async def _test_create_reservation(self, ctx, hotel_id: str) -> List[ToolTestResult]:
        """Test create_reservation tool."""
        results = []
        
        tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        next_week = (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        # Test case 1: Create reservation with redirect
        result = await self._execute_tool_test(
            tool_name="create_reservation",
            hotel_id=hotel_id,
            test_case="create_with_redirect",
            tool_function=lambda: create_reservation(
                ctx,
                check_in=tomorrow,
                check_out=next_week,
                guest_first_name="John",
                guest_last_name="Doe",
                guest_email="john.doe@example.com",
                guest_phone="+1234567890",
                room_type_id="standard",
                adults=2
            ),
            expected_content=["reservation", "booking", "cloudbeds", "complete"],
            allow_pms_unavailable=True
        )
        results.append(result)
        
        return results
    
    async def _test_search_reservations(self, ctx, hotel_id: str) -> List[ToolTestResult]:
        """Test search_reservations tool."""
        results = []
        
        # Test case 1: Search by email
        result = await self._execute_tool_test(
            tool_name="search_reservations",
            hotel_id=hotel_id,
            test_case="search_by_email",
            tool_function=lambda: search_reservations(
                ctx, guest_email="test@example.com"
            ),
            expected_content=["reservation", "search", "pms"],
            allow_pms_unavailable=True
        )
        results.append(result)
        
        return results
    
    async def _test_get_reservation_details(self, ctx, hotel_id: str) -> List[ToolTestResult]:
        """Test get_reservation_details tool."""
        results = []
        
        # Test case 1: Get details for non-existent reservation
        result = await self._execute_tool_test(
            tool_name="get_reservation_details",
            hotel_id=hotel_id,
            test_case="nonexistent_reservation",
            tool_function=lambda: get_reservation_details(
                ctx, reservation_id="TEST123"
            ),
            expected_content=["reservation", "details", "pms"],
            allow_pms_unavailable=True
        )
        results.append(result)
        
        return results
    
    async def _test_get_room_types_info(self, ctx, hotel_id: str) -> List[ToolTestResult]:
        """Test get_room_types_info tool."""
        results = []
        
        # Test case 1: Get all room types
        result = await self._execute_tool_test(
            tool_name="get_room_types_info",
            hotel_id=hotel_id,
            test_case="get_all_room_types",
            tool_function=lambda: get_room_types_info(ctx),
            expected_content=["room types", "pms"],
            allow_pms_unavailable=True
        )
        results.append(result)
        
        return results
    
    async def _execute_tool_test(
        self,
        tool_name: str,
        hotel_id: str,
        test_case: str,
        tool_function: callable,
        expected_content: List[str],
        allow_pms_unavailable: bool = False
    ) -> ToolTestResult:
        """Execute a single tool test.
        
        Args:
            tool_name: Name of the tool being tested
            hotel_id: Hotel ID for the test
            test_case: Description of the test case
            tool_function: Function to execute
            expected_content: List of strings expected in the response
            allow_pms_unavailable: Whether PMS unavailability should be considered success
            
        Returns:
            ToolTestResult
        """
        start_time = datetime.now()
        
        try:
            # Execute the tool
            response = await tool_function()
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Convert response to string if needed
            response_content = str(response) if response else ""
            response_length = len(response_content)
            
            # Check for expected content
            response_lower = response_content.lower()
            contains_expected = all(
                any(expected.lower() in response_lower for expected in expected_content)
                for expected in expected_content
            ) if expected_content else True
            
            # Special handling for PMS unavailability
            success = True
            error_message = None
            
            if allow_pms_unavailable and "pms" in response_lower and ("not available" in response_lower or "integration" in response_lower):
                # PMS unavailability is acceptable for PMS tools
                success = True
                contains_expected = True
            elif not response_content:
                success = False
                error_message = "Empty response"
            elif "error" in response_lower and not any("error" in exp.lower() for exp in expected_content):
                # Error in response when not expected
                success = False
                error_message = "Unexpected error in response"
            
            # Log the test
            self.logger.log_info(
                f"Tool test: {tool_name}[{test_case}] - "
                f"Hotel: {hotel_id} - "
                f"Success: {success} - "
                f"Time: {execution_time:.3f}s"
            )
            
            return ToolTestResult(
                tool_name=tool_name,
                hotel_id=hotel_id,
                test_case=test_case,
                success=success,
                response_content=response_content,
                execution_time=execution_time,
                error_message=error_message,
                response_length=response_length,
                contains_expected_content=contains_expected,
                timestamp=start_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_message = str(e)
            
            # Log the error
            self.logger.log_error(
                f"Tool test failed: {tool_name}[{test_case}] - "
                f"Hotel: {hotel_id} - "
                f"Error: {error_message}"
            )
            
            return ToolTestResult(
                tool_name=tool_name,
                hotel_id=hotel_id,
                test_case=test_case,
                success=False,
                response_content="",
                execution_time=execution_time,
                error_message=error_message,
                response_length=0,
                contains_expected_content=False,
                timestamp=start_time
            )
    
    def analyze_tool_results(self) -> Dict[str, Any]:
        """Analyze the results of all tool tests.
        
        Returns:
            Analysis of tool test results
        """
        if not self.test_results:
            return {}
        
        # Overall statistics
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r.success])
        success_rate = successful_tests / total_tests
        
        # Tool-specific statistics
        tool_stats = {}
        for result in self.test_results:
            if result.tool_name not in tool_stats:
                tool_stats[result.tool_name] = {
                    "total": 0,
                    "successful": 0,
                    "avg_execution_time": 0,
                    "test_cases": []
                }
            
            stats = tool_stats[result.tool_name]
            stats["total"] += 1
            if result.success:
                stats["successful"] += 1
            stats["test_cases"].append(result.test_case)
        
        # Calculate success rates and average execution times
        for tool_name, stats in tool_stats.items():
            stats["success_rate"] = stats["successful"] / stats["total"]
            
            tool_results = [r for r in self.test_results if r.tool_name == tool_name]
            stats["avg_execution_time"] = sum(r.execution_time for r in tool_results) / len(tool_results)
        
        # Hotel-specific statistics
        hotel_stats = {}
        for result in self.test_results:
            if result.hotel_id not in hotel_stats:
                hotel_stats[result.hotel_id] = {
                    "total": 0,
                    "successful": 0
                }
            
            stats = hotel_stats[result.hotel_id]
            stats["total"] += 1
            if result.success:
                stats["successful"] += 1
        
        # Calculate hotel success rates
        for hotel_id, stats in hotel_stats.items():
            stats["success_rate"] = stats["successful"] / stats["total"]
        
        # Find problematic tools and hotels
        problematic_tools = [
            tool for tool, stats in tool_stats.items()
            if stats["success_rate"] < 0.8
        ]
        
        problematic_hotels = [
            hotel for hotel, stats in hotel_stats.items()
            if stats["success_rate"] < 0.8
        ]
        
        # Common errors
        error_messages = [r.error_message for r in self.test_results if r.error_message]
        error_counts = {}
        for error in error_messages:
            # Simplify error for counting
            simple_error = error[:50] if error else "Unknown error"
            error_counts[simple_error] = error_counts.get(simple_error, 0) + 1
        
        common_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        analysis = {
            "overall": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": success_rate,
                "avg_execution_time": sum(r.execution_time for r in self.test_results) / total_tests
            },
            "by_tool": tool_stats,
            "by_hotel": hotel_stats,
            "issues": {
                "problematic_tools": problematic_tools,
                "problematic_hotels": problematic_hotels,
                "common_errors": common_errors
            },
            "recommendations": self._generate_tool_recommendations(
                tool_stats, hotel_stats, problematic_tools, problematic_hotels
            )
        }
        
        return analysis
    
    def _generate_tool_recommendations(
        self,
        tool_stats: Dict[str, Any],
        hotel_stats: Dict[str, Any],
        problematic_tools: List[str],
        problematic_hotels: List[str]
    ) -> List[str]:
        """Generate recommendations based on tool test analysis."""
        
        recommendations = []
        
        # Tool-specific recommendations
        if problematic_tools:
            recommendations.append(
                f"Review and fix tools with low success rates: {', '.join(problematic_tools)}"
            )
        
        # Hotel-specific recommendations
        if problematic_hotels:
            recommendations.append(
                f"Check hotel configurations for: {', '.join(problematic_hotels)}"
            )
        
        # Performance recommendations
        slow_tools = [
            tool for tool, stats in tool_stats.items()
            if stats["avg_execution_time"] > 3.0
        ]
        if slow_tools:
            recommendations.append(
                f"Optimize performance for slow tools: {', '.join(slow_tools)}"
            )
        
        # PMS integration recommendations
        pms_tools = [tool for tool in tool_stats.keys() if "real" in tool or "reservation" in tool or "room_types" in tool]
        if pms_tools:
            pms_success_rates = [tool_stats[tool]["success_rate"] for tool in pms_tools]
            avg_pms_success = sum(pms_success_rates) / len(pms_success_rates)
            if avg_pms_success < 0.5:
                recommendations.append("Consider implementing PMS integration for better tool coverage")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def export_results_to_json(self, filename: Optional[str] = None) -> str:
        """Export test results to JSON file.
        
        Args:
            filename: Optional filename. If not provided, generates timestamped filename.
            
        Returns:
            Path to the exported file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tool_test_results_{timestamp}.json"
        
        # Prepare data for export
        export_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(self.test_results),
                "hotels_tested": list(set(r.hotel_id for r in self.test_results)),
                "tools_tested": list(set(r.tool_name for r in self.test_results))
            },
            "results": [result.model_dump() for result in self.test_results],
            "analysis": self.analyze_tool_results()
        }
        
        # Write to file
        output_path = Path("logs/ai_evaluation") / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, default=str, ensure_ascii=False)
        
        self.logger.log_info(f"Exported tool test results to: {output_path}")
        
        return str(output_path)