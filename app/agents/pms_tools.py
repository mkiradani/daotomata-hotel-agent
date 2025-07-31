"""PMS-integrated tools for OpenAI Agents using Cloudbeds API."""

import asyncio
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from agents import function_tool, RunContextWrapper

# Import our Cloudbeds service
try:
    from app.services.cloudbeds_service import CloudbedsService
    cloudbeds_service = CloudbedsService()
    PMS_AVAILABLE = True
    print("✅ Cloudbeds integration loaded successfully")
except ImportError as e:
    print(f"⚠️ Cloudbeds integration not available: {e}")
    cloudbeds_service = None
    PMS_AVAILABLE = False


def build_cloudbeds_url(
    hotel_id: str, 
    check_in: str, 
    check_out: str, 
    adults: int = 1, 
    children: int = 0, 
    currency: str = "eur"
) -> str:
    """Build Cloudbeds URL for hotel reservations redirect.
    
    Args:
        hotel_id: The Cloudbeds hotel ID
        check_in: Check-in date in YYYY-MM-DD format
        check_out: Check-out date in YYYY-MM-DD format
        adults: Number of adult guests
        children: Number of children
        currency: Currency code (default: eur)
    
    Returns:
        str: Cloudbeds URL for direct booking
    """
    base_url = "https://hotels.cloudbeds.com/en/reservas"
    
    # Build query parameters
    params = {
        "checkin": check_in,
        "checkout": check_out,
        "adults": str(adults),
        "kids": str(children),
        "currency": currency.lower()
    }
    
    # Convert params to query string
    query_string = "&".join([f"{key}={value}" for key, value in params.items()])
    
    return f"{base_url}/{hotel_id}?{query_string}"


@function_tool
async def check_real_room_availability(
    ctx: RunContextWrapper[Any],
    check_in: str,
    check_out: str,
    guests: int = 2,
    children: int = 0,
    hotel_id: Optional[str] = None,
) -> str:
    """Check real room availability using Cloudbeds PMS.

    Args:
        check_in: Check-in date in YYYY-MM-DD format
        check_out: Check-out date in YYYY-MM-DD format
        guests: Number of adult guests (default: 2)
        children: Number of children (default: 0)
        hotel_id: The hotel ID. If not provided, uses the current hotel context.
    """
    try:
        # Use hotel_id from context if not provided
        if not hotel_id and hasattr(ctx.context, "hotel_id"):
            hotel_id = ctx.context.hotel_id

        if not hotel_id:
            return "Hotel ID not available in context."

        # Check availability using our Cloudbeds service
        if PMS_AVAILABLE and cloudbeds_service:
            result = await cloudbeds_service.check_availability(
                hotel_id=int(hotel_id),
                check_in=check_in,
                check_out=check_out,
                adults=guests,
                children=children
            )
            
            if result.get("error"):
                return f"**Room Availability Check**\n\n{result['error']}"
            
            if result.get("available"):
                if result.get("rooms"):
                    # We have real-time availability data
                    response = f"""**Room Availability Check**

✅ **Available Rooms Found!**

**Your Search:**
- Check-in: {result['check_in']}
- Check-out: {result['check_out']}
- Nights: {result['nights']}
- Guests: {result['adults']} adults{f', {result["children"]} children' if result.get('children', 0) > 0 else ''}

**Available Room Types ({result['total_rooms_available']} options):**

"""
                    for room in result['rooms']:
                        response += f"""
**{room['roomTypeName']}**
- Price: {room['currency']} {room['roomRate']:.2f} per night
- Total: {room['currency']} {room['totalRate']:.2f} for {result['nights']} nights
- Available units: {room['roomsAvailable']}
- Max guests: {room['maxGuests']}
"""
                    
                    response += f"""

**Ready to Book?**
🔗 **[Click here to complete your booking]({result['booking_url']})**

This secure link will take you directly to our booking system where you can:
- Select your preferred room type
- Complete your reservation with secure payment
- Receive instant confirmation

Need help? Contact our reception team for assistance."""
                    return response
                else:
                    # Fallback to booking URL only
                    response = f"""**Room Availability Check**

✅ **Check availability and book your room online!**

**Your Request:**
- Check-in: {result['check_in']}
- Check-out: {result['check_out']}
- Nights: {result['nights']}
- Guests: {result['adults']} adults{f', {result["children"]} children' if result.get('children', 0) > 0 else ''}

{result.get('message', 'Please check our booking system for real-time availability.')}

🔗 **[Click here to check real-time availability and complete your booking]({result['booking_url']})**

This secure link will take you directly to our hotel's booking system where you can:
- See all available room types and current rates
- View detailed room descriptions and photos
- Complete your reservation with secure payment
- Receive instant confirmation

Need help? Contact our reception team for assistance."""
                    return response
            else:
                return "No availability information found."
        else:
            return f"""**Room Availability Check**

I apologize, but I cannot check real-time availability at the moment.

**Your Request:**
- Check-in: {check_in}
- Check-out: {check_out}
- Guests: {guests} adults{f', {children} children' if children > 0 else ''}

Please contact the hotel directly for real-time availability and booking assistance."""

    except ValueError:
        return "Invalid date format. Please use YYYY-MM-DD format."
    except Exception as e:
        return f"Error checking availability: {str(e)}"


@function_tool
async def create_reservation(
    ctx: RunContextWrapper[Any],
    check_in: str,
    check_out: str,
    guest_first_name: str,
    guest_last_name: str,
    guest_email: str,
    guest_phone: str,
    room_type_id: str,
    adults: int = 2,
    children: int = 0,
    special_requests: Optional[str] = None,
    hotel_id: Optional[str] = None,
) -> str:
    """Create a new reservation using Cloudbeds URL redirect.

    Args:
        check_in: Check-in date in YYYY-MM-DD format
        check_out: Check-out date in YYYY-MM-DD format
        guest_first_name: Guest's first name
        guest_last_name: Guest's last name
        guest_email: Guest's email address
        guest_phone: Guest's phone number
        room_type_id: ID of the room type to book
        adults: Number of adult guests (default: 2)
        children: Number of children (default: 0)
        special_requests: Any special requests
        hotel_id: The hotel ID. If not provided, uses the current hotel context.
    """
    try:
        # Parse dates to validate format
        check_in_date = datetime.strptime(check_in, "%Y-%m-%d").date()
        check_out_date = datetime.strptime(check_out, "%Y-%m-%d").date()

        # Validate dates
        if check_in_date <= date.today():
            return "Check-in date must be in the future."

        if check_out_date <= check_in_date:
            return "Check-out date must be after check-in date."

        nights = (check_out_date - check_in_date).days

        # Use hotel_id from context if not provided
        if not hotel_id and hasattr(ctx.context, "hotel_id"):
            hotel_id = ctx.context.hotel_id

        if not hotel_id:
            return "Hotel ID not available in context."

        # Get booking URL from Cloudbeds service
        if PMS_AVAILABLE and cloudbeds_service:
            credentials = await cloudbeds_service.get_hotel_credentials(int(hotel_id))
            booking_url_id = credentials.get("booking_url_id", "")
            
            if booking_url_id:
                booking_url = cloudbeds_service.build_booking_url(
                    booking_url_id=booking_url_id,
                    check_in=check_in,
                    check_out=check_out,
                    adults=adults,
                    children=children,
                    currency="eur"
                )
            else:
                return "Booking URL not configured for this hotel. Please contact reception."
        else:
            return "Booking service not available. Please contact reception."

        # Format response with booking URL
        response = f"""**Complete Your Reservation**

**Reservation Details:**
- Guest: {guest_first_name} {guest_last_name}
- Email: {guest_email}
- Phone: {guest_phone}
- Check-in: {check_in}
- Check-out: {check_out}
- Nights: {nights}
- Guests: {adults} adults{f', {children} children' if children > 0 else ''}
- Room Type ID: {room_type_id}
{f'- Special Requests: {special_requests}' if special_requests else ''}

**To complete your booking, please visit:**
{booking_url}

This secure link will take you directly to the hotel's booking system where you can:
- Review room availability and rates
- Complete your reservation
- Make secure payment
- Receive instant confirmation

The booking system will pre-fill your selected dates and guest information. Thank you for choosing our hotel!"""

        return response

    except ValueError:
        return "Invalid date format. Please use YYYY-MM-DD format."
    except Exception as e:
        return f"Error preparing reservation: {str(e)}"


@function_tool
async def search_reservations(
    ctx: RunContextWrapper[Any],
    guest_email: Optional[str] = None,
    confirmation_code: Optional[str] = None,
    check_in_from: Optional[str] = None,
    check_in_to: Optional[str] = None,
    hotel_id: Optional[str] = None,
) -> str:
    """Search for existing reservations using Cloudbeds PMS.

    Args:
        guest_email: Guest's email address
        confirmation_code: Reservation confirmation code
        check_in_from: Start date for check-in search (YYYY-MM-DD)
        check_in_to: End date for check-in search (YYYY-MM-DD)
        hotel_id: The hotel ID. If not provided, uses the current hotel context.
    """
    return """**Reservation Search**

To search for your existing reservation, please contact our reception team directly with:
- Your confirmation code, or
- The email address used for booking

Our staff will be happy to help you find your reservation and assist with any modifications needed.

For immediate assistance:
- Visit reception desk
- Call the hotel directly
- Email our reservations team"""


@function_tool
async def get_reservation_details(
    ctx: RunContextWrapper[Any], reservation_id: str, hotel_id: Optional[str] = None
) -> str:
    """Get detailed information about a specific reservation.

    Args:
        reservation_id: The reservation ID
        hotel_id: The hotel ID. If not provided, uses the current hotel context.
    """
    return f"""**Reservation Details**

To get detailed information about reservation ID: {reservation_id}, please contact our reception team.

They can provide:
- Current reservation status
- Room details and rates
- Check-in/check-out information
- Any special requests or notes
- Payment and balance information

For immediate assistance:
- Visit reception desk
- Call the hotel directly
- Email our reservations team"""


@function_tool
async def get_room_types_info(
    ctx: RunContextWrapper[Any], hotel_id: Optional[str] = None
) -> str:
    """Get information about available room types.

    Args:
        hotel_id: The hotel ID. If not provided, uses the current hotel context.
    """
    return """**Room Types Information**

Our hotel offers a variety of comfortable room types to suit your needs:

**Standard Rooms**
- Comfortable accommodation with all essential amenities
- Perfect for business travelers and short stays

**Deluxe Rooms** 
- Spacious rooms with enhanced comfort
- Additional amenities and better views

**Suites**
- Luxurious space with separate living area
- Premium amenities and exclusive services

**Family Rooms**
- Extra space for families
- Multiple beds and family-friendly features

For detailed information about:
- Room sizes and layouts
- Specific amenities in each room type
- Current rates and availability
- Photos and virtual tours

Please:
- Visit our website
- Contact reception directly
- Use the availability check tool to see real-time options"""


@function_tool
async def get_currency_exchange_rate(
    ctx: RunContextWrapper[Any],
    amount: float,
    from_currency: str,
    to_currency: str,
    hotel_id: Optional[str] = None,
) -> str:
    """Convert prices between currencies using hotel's configured exchange rates.
    
    Args:
        amount: The amount to convert
        from_currency: Source currency ISO code (e.g., 'EUR', 'USD')
        to_currency: Target currency ISO code (e.g., 'EUR', 'USD')
        hotel_id: The hotel ID. If not provided, uses the current hotel context.
    """
    try:
        # Use hotel_id from context if not provided
        if not hotel_id and hasattr(ctx.context, "hotel_id"):
            hotel_id = ctx.context.hotel_id
        
        if not hotel_id:
            return "Hotel ID not available in context."
        
        # Normalize currency codes
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        # Check if conversion is needed
        if from_currency == to_currency:
            return f"**Currency Conversion**\n\n{amount:.2f} {from_currency} = {amount:.2f} {to_currency}\n\nNo conversion needed - same currency."
        
        # Get currency settings from Cloudbeds
        if PMS_AVAILABLE and cloudbeds_service:
            result = await cloudbeds_service.get_currency_settings(int(hotel_id))
            
            if not result.get("success"):
                return f"**Currency Conversion Error**\n\n{result.get('error', 'Failed to get currency settings')}"
            
            currency_data = result.get("data", {})
            default_currency = currency_data.get("default", "EUR").upper()
            acceptable_currencies = [c.upper() for c in currency_data.get("acceptable", [])]
            rates_data = currency_data.get("rates", {})
            fixed_rates = rates_data.get("fixed", [])
            
            # Build rates dictionary
            rates = {}
            for rate_info in fixed_rates:
                if rate_info.get("currency") and rate_info.get("rate"):
                    rates[rate_info["currency"].upper()] = float(rate_info["rate"])
            
            # Check if currencies are supported
            if from_currency not in acceptable_currencies and from_currency != default_currency:
                return f"""**Currency Conversion Error**
                
The currency '{from_currency}' is not supported by this hotel.

**Supported currencies:**
- Default: {default_currency}
- Acceptable: {', '.join(acceptable_currencies)}

Please use one of the supported currencies for your inquiry."""
            
            if to_currency not in acceptable_currencies and to_currency != default_currency:
                return f"""**Currency Conversion Error**
                
The currency '{to_currency}' is not supported by this hotel.

**Supported currencies:**
- Default: {default_currency}
- Acceptable: {', '.join(acceptable_currencies)}

Please use one of the supported currencies for conversion."""
            
            # Perform conversion
            # First convert to default currency if needed
            if from_currency == default_currency:
                amount_in_default = amount
            elif from_currency in rates:
                # Convert from the source currency to default
                # If rate is 1.2, it means 1 default = 1.2 source, so source to default is divide
                amount_in_default = amount / rates[from_currency]
            else:
                return f"""**Currency Conversion Error**

No exchange rate found for {from_currency} to {default_currency}.

The hotel has not configured an exchange rate for this currency pair. Please contact reception for assistance with currency conversion."""
            
            # Then convert from default to target currency
            if to_currency == default_currency:
                converted_amount = amount_in_default
            elif to_currency in rates:
                # Convert from default to target
                # If rate is 1.2, it means 1 default = 1.2 target, so default to target is multiply
                converted_amount = amount_in_default * rates[to_currency]
            else:
                return f"""**Currency Conversion Error**

No exchange rate found for {default_currency} to {to_currency}.

The hotel has not configured an exchange rate for this currency pair. Please contact reception for assistance with currency conversion."""
            
            # Format response
            currency_format = currency_data.get("format", {})
            decimal_sep = currency_format.get("decimal", ".")
            thousand_sep = currency_format.get("thousand", ",")
            
            # Format numbers with proper separators
            def format_number(num):
                # Convert to string with 2 decimal places
                num_str = f"{num:.2f}"
                integer_part, decimal_part = num_str.split(".")
                
                # Add thousand separators
                if thousand_sep:
                    integer_part = "{:,}".format(int(integer_part)).replace(",", thousand_sep)
                
                return f"{integer_part}{decimal_sep}{decimal_part}"
            
            formatted_amount = format_number(amount)
            formatted_converted = format_number(converted_amount)
            
            response = f"""**Currency Conversion**

{formatted_amount} {from_currency} = **{formatted_converted} {to_currency}**

**Exchange Rate Information:**
- Hotel's default currency: {default_currency}"""
            
            # Show the exchange rates used
            if from_currency != default_currency and from_currency in rates:
                response += f"\n- {from_currency} to {default_currency}: 1 {from_currency} = {1/rates[from_currency]:.4f} {default_currency}"
            if to_currency != default_currency and to_currency in rates:
                response += f"\n- {default_currency} to {to_currency}: 1 {default_currency} = {rates[to_currency]:.4f} {to_currency}"
            
            response += "\n\n*Note: These are the hotel's configured exchange rates. Actual rates may vary for payment processing.*"
            
            return response
            
        else:
            return """**Currency Conversion Service Unavailable**

I apologize, but the currency conversion service is not available at the moment.

Please contact reception for assistance with currency conversion and current exchange rates."""
    
    except ValueError as e:
        return f"**Currency Conversion Error**\n\nInvalid amount provided. Please ensure the amount is a valid number."
    except Exception as e:
        return f"**Currency Conversion Error**\n\nAn error occurred: {str(e)}"
