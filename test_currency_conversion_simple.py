"""Simple test for currency conversion functionality."""

import asyncio
from app.services.cloudbeds_service import CloudbedsService


async def test_currency_settings():
    """Test getting currency settings directly from CloudbedsService."""
    service = CloudbedsService()
    
    print("Testing Currency Settings API...")
    
    # Test with hotel_id 1
    result = await service.get_currency_settings(hotel_id=1)
    
    print(f"\nResponse: {result}")
    
    if result.get("success"):
        data = result.get("data", {})
        print(f"\n✅ Success!")
        print(f"Default currency: {data.get('default')}")
        print(f"Acceptable currencies: {data.get('acceptable')}")
        print(f"Currency format: {data.get('format')}")
        
        rates = data.get("rates", {}).get("fixed", [])
        if rates:
            print(f"\nFixed exchange rates:")
            for rate in rates:
                print(f"  - {rate.get('currency')}: {rate.get('rate')}")
        else:
            print("\nNo fixed exchange rates configured")
    else:
        print(f"\n❌ Error: {result.get('error')}")


async def test_conversion_logic():
    """Test the conversion logic with mock data."""
    # Mock currency data similar to API response
    currency_data = {
        "default": "EUR",
        "acceptable": ["USD", "GBP", "JPY"],
        "format": {
            "decimal": ".",
            "thousand": ","
        },
        "rates": {
            "fixed": [
                {"currency": "USD", "rate": 1.18},
                {"currency": "GBP", "rate": 0.86},
                {"currency": "JPY", "rate": 130.5}
            ]
        }
    }
    
    # Build rates dictionary
    rates = {}
    for rate_info in currency_data["rates"]["fixed"]:
        if rate_info.get("currency") and rate_info.get("rate"):
            rates[rate_info["currency"]] = float(rate_info["rate"])
    
    print("\n\nTesting Currency Conversion Logic...")
    print(f"Default currency: {currency_data['default']}")
    print(f"Exchange rates: {rates}")
    
    # Test conversions
    test_cases = [
        (100, "EUR", "USD"),
        (100, "USD", "EUR"),
        (100, "EUR", "GBP"),
        (100, "GBP", "JPY"),
        (1000, "JPY", "EUR")
    ]
    
    for amount, from_curr, to_curr in test_cases:
        print(f"\n{amount} {from_curr} to {to_curr}:")
        
        # Convert to default currency (EUR) first
        if from_curr == "EUR":
            amount_in_eur = amount
        elif from_curr in rates:
            # If USD rate is 1.18, then 1 EUR = 1.18 USD
            # So 100 USD = 100 / 1.18 EUR
            amount_in_eur = amount / rates[from_curr]
        else:
            print(f"  ❌ {from_curr} not in rates")
            continue
        
        # Convert from EUR to target currency
        if to_curr == "EUR":
            converted = amount_in_eur
        elif to_curr in rates:
            # If USD rate is 1.18, then 1 EUR = 1.18 USD
            # So 100 EUR = 100 * 1.18 USD
            converted = amount_in_eur * rates[to_curr]
        else:
            print(f"  ❌ {to_curr} not in rates")
            continue
        
        print(f"  ✅ {amount} {from_curr} = {converted:.2f} {to_curr}")
        print(f"     (via EUR: {amount_in_eur:.2f})")


if __name__ == "__main__":
    print("=== Currency Conversion Test ===\n")
    asyncio.run(test_currency_settings())
    asyncio.run(test_conversion_logic())