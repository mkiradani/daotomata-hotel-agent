"""Tests for PMS tools functionality."""
import pytest
from unittest.mock import patch, MagicMock
from app.agents.pms_tools import build_cloudbeds_url, create_reservation


class TestBuildCloudbedsUrl:
    """Test cases for build_cloudbeds_url function."""
    
    def test_basic_url_generation(self):
        """Test basic URL generation with required parameters."""
        url = build_cloudbeds_url(
            hotel_id="12345",
            check_in="2024-01-15",
            check_out="2024-01-17",
            adults=2
        )
        
        expected = "https://hotels.cloudbeds.com/en/reservas/12345?checkin=2024-01-15&checkout=2024-01-17&adults=2&kids=0&currency=eur"
        assert url == expected
    
    def test_url_with_children(self):
        """Test URL generation with children parameter."""
        url = build_cloudbeds_url(
            hotel_id="12345",
            check_in="2024-01-15",
            check_out="2024-01-17",
            adults=2,
            children=1
        )
        
        expected = "https://hotels.cloudbeds.com/en/reservas/12345?checkin=2024-01-15&checkout=2024-01-17&adults=2&kids=1&currency=eur"
        assert url == expected
    
    def test_url_with_different_currency(self):
        """Test URL generation with different currency."""
        url = build_cloudbeds_url(
            hotel_id="12345",
            check_in="2024-01-15",
            check_out="2024-01-17",
            adults=2,
            currency="MAD"
        )
        
        expected = "https://hotels.cloudbeds.com/en/reservas/12345?checkin=2024-01-15&checkout=2024-01-17&adults=2&kids=0&currency=mad"
        assert url == expected
    
    def test_url_with_all_parameters(self):
        """Test URL generation with all parameters."""
        url = build_cloudbeds_url(
            hotel_id="67890",
            check_in="2024-02-01",
            check_out="2024-02-05",
            adults=3,
            children=2,
            currency="USD"
        )
        
        expected = "https://hotels.cloudbeds.com/en/reservas/67890?checkin=2024-02-01&checkout=2024-02-05&adults=3&kids=2&currency=usd"
        assert url == expected
    
    def test_currency_case_insensitive(self):
        """Test that currency parameter is converted to lowercase."""
        url = build_cloudbeds_url(
            hotel_id="12345",
            check_in="2024-01-15",
            check_out="2024-01-17",
            adults=1,
            currency="EUR"
        )
        
        assert "currency=eur" in url
    
    def test_special_characters_in_hotel_id(self):
        """Test URL generation with special characters in hotel ID."""
        url = build_cloudbeds_url(
            hotel_id="hotel-test-123",
            check_in="2024-01-15",
            check_out="2024-01-17",
            adults=1
        )
        
        expected = "https://hotels.cloudbeds.com/en/reservas/hotel-test-123?checkin=2024-01-15&checkout=2024-01-17&adults=1&kids=0&currency=eur"
        assert url == expected
    
    def test_zero_children_parameter(self):
        """Test URL generation with explicitly zero children."""
        url = build_cloudbeds_url(
            hotel_id="12345",
            check_in="2024-01-15",
            check_out="2024-01-17",
            adults=2,
            children=0
        )
        
        assert "kids=0" in url
    
    def test_morocco_currency(self):
        """Test URL generation with Moroccan Dirham currency."""
        url = build_cloudbeds_url(
            hotel_id="12345",
            check_in="2024-01-15",
            check_out="2024-01-17",
            adults=2,
            currency="MAD"
        )
        
        assert "currency=mad" in url


class TestCreateReservation:
    """Test cases for create_reservation function."""
    
    def test_create_reservation_is_function_tool(self):
        """Test that create_reservation is properly decorated as a FunctionTool."""
        from app.agents.pms_tools import create_reservation
        from agents import FunctionTool
        
        # Verify it's a FunctionTool object
        assert isinstance(create_reservation, FunctionTool)
        
        # Verify it has the expected function name
        assert create_reservation.name == "create_reservation"
        
        # Verify it has a description
        assert create_reservation.description is not None
        assert "reservation" in create_reservation.description.lower()
        
        # Verify it has parameters schema
        assert hasattr(create_reservation, 'params_json_schema')
        schema = create_reservation.params_json_schema
        assert "properties" in schema
        assert "check_in" in schema["properties"]
        assert "guest_first_name" in schema["properties"]
        assert "guest_email" in schema["properties"]

    def test_create_reservation_has_correct_parameters(self):
        """Test that create_reservation has the correct parameter schema."""
        from app.agents.pms_tools import create_reservation
        
        # Get the schema
        schema = create_reservation.params_json_schema
        
        # Verify required parameters exist
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        # Check essential parameters
        essential_params = ["check_in", "check_out", "guest_first_name", "guest_last_name", "guest_email", "room_type_id"]
        for param in essential_params:
            assert param in properties, f"Missing parameter: {param}"
        
        # Verify some parameters are required
        assert "check_in" in required
        assert "guest_first_name" in required
        assert "guest_email" in required
        
    def test_create_reservation_tool_schema(self):
        """Test that create_reservation has correct OpenAI function schema."""
        from app.agents.pms_tools import create_reservation
        
        # Get function schema
        schema = create_reservation.params_json_schema
        
        # Verify required fields are present
        required_fields = schema.get("required", [])
        assert "check_in" in required_fields
        assert "check_out" in required_fields
        assert "guest_first_name" in required_fields
        assert "guest_last_name" in required_fields
        assert "guest_email" in required_fields
        assert "room_type_id" in required_fields
        
        # Verify properties have correct types
        properties = schema.get("properties", {})
        assert properties["check_in"]["type"] == "string"
        assert properties["guest_email"]["type"] == "string"
        assert properties["adults"]["type"] == "integer"