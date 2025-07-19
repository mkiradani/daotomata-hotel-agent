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
    
    @patch('app.agents.pms_tools.get_pms_client')
    @patch('app.agents.pms_tools.build_cloudbeds_url')
    def test_create_reservation_returns_url(self, mock_build_url, mock_get_client):
        """Test that create_reservation returns a Cloudbeds URL."""
        mock_build_url.return_value = "https://hotels.cloudbeds.com/en/reservas/12345?checkin=2024-01-15&checkout=2024-01-17&adults=2&kids=0&currency=eur"
        mock_get_client.return_value = None  # Simulate no PMS client
        
        result = create_reservation(
            hotel_id="12345",
            guest_name="John Doe",
            guest_email="john@example.com",
            guest_phone="+1234567890",
            check_in="2024-01-15",
            check_out="2024-01-17",
            adults=2,
            children=0,
            room_type="deluxe"
        )
        
        assert "cloudbeds.com" in result
        mock_build_url.assert_called_once_with(
            hotel_id="12345",
            check_in="2024-01-15",
            check_out="2024-01-17",
            adults=2,
            children=0,
            currency="eur"
        )
    
    @patch('app.agents.pms_tools.get_pms_client')
    @patch('app.agents.pms_tools.build_cloudbeds_url')
    def test_create_reservation_with_currency(self, mock_build_url, mock_get_client):
        """Test create_reservation with specific currency."""
        mock_build_url.return_value = "https://hotels.cloudbeds.com/en/reservas/12345?currency=mad"
        mock_get_client.return_value = None
        
        result = create_reservation(
            hotel_id="12345",
            guest_name="Ahmed Ben Ali",
            guest_email="ahmed@example.com",
            guest_phone="+212123456789",
            check_in="2024-01-15",
            check_out="2024-01-17",
            adults=2,
            children=1,
            room_type="standard",
            currency="MAD"
        )
        
        assert "cloudbeds.com" in result
        mock_build_url.assert_called_once_with(
            hotel_id="12345",
            check_in="2024-01-15",
            check_out="2024-01-17",
            adults=2,
            children=1,
            currency="MAD"
        )
    
    @patch('app.agents.pms_tools.get_pms_client')
    @patch('app.agents.pms_tools.build_cloudbeds_url')
    def test_create_reservation_includes_message(self, mock_build_url, mock_get_client):
        """Test that create_reservation includes explanatory message."""
        mock_build_url.return_value = "https://hotels.cloudbeds.com/en/reservas/12345"
        mock_get_client.return_value = None
        
        result = create_reservation(
            hotel_id="12345",
            guest_name="Test Guest",
            guest_email="test@example.com",
            guest_phone="+1234567890",
            check_in="2024-01-15",
            check_out="2024-01-17",
            adults=1,
            children=0,
            room_type="standard"
        )
        
        assert "secure booking link" in result or "complete your reservation" in result
        assert "https://hotels.cloudbeds.com" in result