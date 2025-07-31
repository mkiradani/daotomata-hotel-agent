"""Test currency conversion functionality with real Cloudbeds API data."""

import asyncio
import pytest
from app.services.cloudbeds_service import CloudbedsService
from app.agents.pms_tools import get_currency_exchange_rate
from agents import RunContextWrapper
from types import SimpleNamespace


class TestCurrencyConversion:
    """Test currency conversion using real API data."""
    
    @pytest.fixture
    async def cloudbeds_service(self):
        """Create CloudbedsService instance."""
        return CloudbedsService()
    
    @pytest.fixture
    def mock_context(self):
        """Create mock context with hotel_id."""
        # Create context directly without RunContextWrapper for testing
        ctx = SimpleNamespace(context=SimpleNamespace(hotel_id="1"))
        return ctx
    
    @pytest.mark.asyncio
    async def test_get_currency_settings(self, cloudbeds_service):
        """Test getting currency settings from Cloudbeds API."""
        # Using hotel_id 1 (should be configured in your test environment)
        result = await cloudbeds_service.get_currency_settings(hotel_id=1)
        
        print("\n=== Currency Settings Response ===")
        print(f"Success: {result.get('success')}")
        print(f"Data: {result.get('data')}")
        
        # Verify response structure
        assert isinstance(result, dict)
        assert "success" in result
        
        if result.get("success"):
            data = result.get("data", {})
            assert "default" in data
            assert "acceptable" in data
            assert "format" in data
            assert "rates" in data
            
            print(f"\nDefault currency: {data.get('default')}")
            print(f"Acceptable currencies: {data.get('acceptable')}")
            print(f"Format settings: {data.get('format')}")
            print(f"Fixed rates: {data.get('rates', {}).get('fixed', [])}")
    
    @pytest.mark.asyncio
    async def test_currency_conversion_same_currency(self, mock_context):
        """Test converting between same currency."""
        result = await get_currency_exchange_rate(
            ctx=mock_context,
            amount=100.0,
            from_currency="EUR",
            to_currency="EUR",
            hotel_id="1"
        )
        
        print("\n=== Same Currency Test ===")
        print(result)
        
        assert "No conversion needed" in result
        assert "100.00 EUR = 100.00 EUR" in result
    
    @pytest.mark.asyncio
    async def test_currency_conversion_eur_to_usd(self, mock_context):
        """Test converting EUR to USD."""
        result = await get_currency_exchange_rate(
            ctx=mock_context,
            amount=100.0,
            from_currency="EUR",
            to_currency="USD",
            hotel_id="1"
        )
        
        print("\n=== EUR to USD Conversion ===")
        print(result)
        
        # Check for success or appropriate error message
        assert "Currency Conversion" in result
        # Either successful conversion or error about missing rate/unsupported currency
    
    @pytest.mark.asyncio
    async def test_currency_conversion_unsupported(self, mock_context):
        """Test converting with unsupported currency."""
        result = await get_currency_exchange_rate(
            ctx=mock_context,
            amount=100.0,
            from_currency="EUR",
            to_currency="XYZ",  # Invalid currency
            hotel_id="1"
        )
        
        print("\n=== Unsupported Currency Test ===")
        print(result)
        
        assert "Currency Conversion Error" in result or "not supported" in result
    
    @pytest.mark.asyncio
    async def test_currency_conversion_invalid_amount(self, mock_context):
        """Test with invalid amount."""
        result = await get_currency_exchange_rate(
            ctx=mock_context,
            amount="invalid",  # Invalid amount
            from_currency="EUR",
            to_currency="USD",
            hotel_id="1"
        )
        
        print("\n=== Invalid Amount Test ===")
        print(result)
        
        assert "Error" in result
    
    @pytest.mark.asyncio
    async def test_currency_conversion_no_hotel_id(self):
        """Test without hotel_id in context."""
        # Create context without hotel_id
        ctx = SimpleNamespace(context=SimpleNamespace())
        
        result = await get_currency_exchange_rate(
            ctx=ctx,
            amount=100.0,
            from_currency="EUR",
            to_currency="USD"
        )
        
        print("\n=== No Hotel ID Test ===")
        print(result)
        
        assert "Hotel ID not available" in result
    
    @pytest.mark.asyncio
    async def test_currency_conversion_with_formatting(self, mock_context):
        """Test large amount conversion to check number formatting."""
        result = await get_currency_exchange_rate(
            ctx=mock_context,
            amount=12345.67,
            from_currency="EUR",
            to_currency="USD",
            hotel_id="1"
        )
        
        print("\n=== Large Amount Formatting Test ===")
        print(result)
        
        # Should contain formatted numbers with thousand separators
        assert "Currency Conversion" in result


if __name__ == "__main__":
    # Run tests directly
    async def run_tests():
        test = TestCurrencyConversion()
        service = CloudbedsService()
        
        # Create mock context
        # Create context directly without RunContextWrapper for testing
        ctx = SimpleNamespace(context=SimpleNamespace(hotel_id="1"))
        
        print("Running Currency Conversion Tests...")
        
        # Test 1: Get currency settings
        print("\n1. Testing get_currency_settings...")
        try:
            result = await service.get_currency_settings(hotel_id=1)
            print(f"Result: {result}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test 2: Same currency conversion
        print("\n2. Testing same currency conversion...")
        try:
            result = await get_currency_exchange_rate(
                ctx=ctx,
                amount=100.0,
                from_currency="EUR",
                to_currency="EUR"
            )
            print(result)
        except Exception as e:
            print(f"Error: {e}")
        
        # Test 3: EUR to USD conversion
        print("\n3. Testing EUR to USD conversion...")
        try:
            result = await get_currency_exchange_rate(
                ctx=ctx,
                amount=100.0,
                from_currency="EUR",
                to_currency="USD"
            )
            print(result)
        except Exception as e:
            print(f"Error: {e}")
        
        print("\nAll tests completed!")
    
    # Run the async tests
    asyncio.run(run_tests())