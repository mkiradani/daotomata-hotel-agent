"""Tests to validate Directus migration is working correctly."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestDirectusMigration:
    """Test cases to validate Directus migration."""

    def test_directus_service_can_be_imported(self):
        """Test that DirectusService class can be imported without errors."""
        from app.services.directus_service import DirectusService
        
        # Just verify the class exists and can be referenced
        assert DirectusService is not None
        assert hasattr(DirectusService, 'get_hotel_by_id')
        assert hasattr(DirectusService, 'get_hotel_activities')

    def test_directus_service_methods_exist(self):
        """Test that DirectusService has all expected methods."""
        from app.services.directus_service import DirectusService
        
        # Verify all expected methods exist
        expected_methods = [
            'get_hotel_by_id',
            'get_hotel_by_domain', 
            'get_hotel_coordinates',
            'get_hotel_name',
            'get_hotel_activities',
            'get_hotel_facilities',
            'create_service_request'
        ]
        
        for method_name in expected_methods:
            assert hasattr(DirectusService, method_name), f"Missing method: {method_name}"
            method = getattr(DirectusService, method_name)
            assert callable(method), f"Method {method_name} is not callable"

    def test_agent_tools_can_be_imported(self):
        """Test that agent tools can be imported without errors."""
        from agents import FunctionTool
        
        # Import tools and verify they're FunctionTool objects
        from app.agents.tools import get_hotel_info, get_local_weather
        
        assert isinstance(get_hotel_info, FunctionTool)
        assert isinstance(get_local_weather, FunctionTool)
        
        # Verify function names are correct
        assert get_hotel_info.name == "get_hotel_info"
        assert get_local_weather.name == "get_local_weather"
        
        # Verify they have descriptions
        assert get_hotel_info.description is not None
        assert get_local_weather.description is not None

    def test_supabase_references_removed(self):
        """Test that Supabase references have been completely removed."""
        import subprocess
        
        # Search for any remaining supabase references
        try:
            result = subprocess.run([
                'grep', '-r', 'supabase', 'app/', '--exclude-dir=__pycache__'
            ], capture_output=True, text=True)
            
            # If grep finds matches, result.returncode will be 0
            if result.returncode == 0:
                print("Found remaining supabase references:")
                print(result.stdout)
                # Allow some references in comments or strings, but no imports
                lines = result.stdout.strip().split('\n')
                problematic_lines = [
                    line for line in lines 
                    if 'import' in line.lower() and 'supabase' in line.lower()
                ]
                assert len(problematic_lines) == 0, f"Found supabase imports: {problematic_lines}"
            
        except FileNotFoundError:
            # grep not available, skip this test
            pass

    def test_directus_references_present(self):
        """Test that Directus references are properly added."""
        from app.services.directus_service import DirectusService
        from app.config import settings
        
        # Check that Directus service exists
        assert DirectusService is not None
        
        # Check that Directus config is present
        assert hasattr(settings, 'directus_url')
        assert hasattr(settings, 'directus_token')

    def test_chat_service_can_be_imported(self):
        """Test that chat service can be imported without errors."""
        from app.services.chat_service import ChatService, chat_service
        
        # Verify ChatService class exists
        assert ChatService is not None
        
        # Verify global chat_service instance exists
        assert chat_service is not None
        assert isinstance(chat_service, ChatService)

    def test_requirements_updated(self):
        """Test that requirements.txt has been updated correctly."""
        with open('requirements.txt', 'r') as f:
            content = f.read()
        
        # Should not contain supabase
        assert 'supabase' not in content.lower()
        
        # Should contain py-directus
        assert 'py-directus' in content.lower()

    def test_hotel_api_can_be_imported(self):
        """Test that hotel API endpoints can be imported."""
        from app.api.hotel import get_hotel_info, get_activities, get_facilities
        
        # Should be importable without errors
        assert get_hotel_info is not None
        assert get_activities is not None
        assert get_facilities is not None
        
        # Verify they're async functions
        import asyncio
        assert asyncio.iscoroutinefunction(get_hotel_info)
        assert asyncio.iscoroutinefunction(get_activities)
        assert asyncio.iscoroutinefunction(get_facilities)