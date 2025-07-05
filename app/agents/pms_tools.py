"""PMS-integrated tools for OpenAI Agents using Cloudbeds API."""

import asyncio
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from agents import function_tool, RunContextWrapper

# Try to import PMS services, but make them optional
PMS_AVAILABLE = False
try:
    import sys
    import os
    from pathlib import Path

    # Add project root to path for absolute imports
    current_file = Path(__file__).resolve()
    # Go up from services/bot/app/agents/ to project root
    project_root = current_file.parent.parent.parent.parent.parent

    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        print(f"✅ Added project root to path: {project_root}")

    # Now import using absolute paths from project root
    from services.pms.client.base import CloudbedsClient
    from services.pms.services.availability import AvailabilityService
    from services.pms.services.reservations import ReservationService
    from services.pms.services.rooms import RoomService
    from services.pms.services.rates import RateService
    from services.pms.utils.tenant import TenantManager
    from services.pms.models.reservation import (
        ReservationSearchParams,
        ReservationCreateRequest,
        Guest,
        ReservationRoom,
    )

    # Initialize tenant manager
    tenant_manager = TenantManager()
    PMS_AVAILABLE = True
    print("✅ PMS integration loaded successfully")
except ImportError as e:
    print(f"⚠️ PMS integration not available: {e}")
    tenant_manager = None


async def get_pms_client(hotel_id: str):
    """Get PMS client for a specific hotel"""
    if not PMS_AVAILABLE:
        return None

    try:
        tenant_config = await tenant_manager.get_tenant_config(hotel_id)
        if not tenant_config:
            return None

        return CloudbedsClient(tenant_config)
    except Exception as e:
        print(f"Error getting PMS client for hotel {hotel_id}: {e}")
        return None


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
    if not PMS_AVAILABLE:
        return f"""**Room Availability Check**

I apologize, but the PMS (Property Management System) integration is currently not available.

**Your Request:**
- Check-in: {check_in}
- Check-out: {check_out}
- Guests: {guests} adults{f', {children} children' if children > 0 else ''}

**What I can help with instead:**
- General hotel information and amenities
- Local area recommendations
- Hotel services and facilities
- Dining options and spa services

Please contact the hotel directly at the front desk for real-time availability and booking assistance."""

    try:
        # Parse dates
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

        # Get PMS client
        client = await get_pms_client(hotel_id)
        if not client:
            return "PMS integration not configured for this hotel."

        async with client:
            # Get availability service
            availability_service = AvailabilityService(client)
            room_service = RoomService(client)

            # Get room types
            room_types = await room_service.get_room_types()
            if not room_types:
                return "No room types found for this hotel."

            # Check availability for each room type
            response = f"**Room Availability**\n"
            response += f"Check-in: {check_in}\n"
            response += f"Check-out: {check_out}\n"
            response += f"Nights: {nights}\n"
            response += f"Guests: {guests} adults"
            if children > 0:
                response += f", {children} children"
            response += "\n\n"

            available_rooms = []

            for room_type in room_types:
                # Check if room type can accommodate guests
                if guests > room_type.max_adults or children > room_type.max_children:
                    continue

                # Check availability
                availability_check = await availability_service.check_availability(
                    start_date=check_in_date,
                    end_date=check_out_date,
                    room_type_id=room_type.room_type_id,
                    rooms_needed=1,
                    adults=guests,
                    children=children,
                )

                # Get lowest rate
                lowest_rate = await availability_service.get_lowest_rate(
                    start_date=check_in_date,
                    end_date=check_out_date,
                    room_type_id=room_type.room_type_id,
                    adults=guests,
                    children=children,
                )

                room_info = {
                    "name": room_type.name,
                    "available": availability_check["available"],
                    "available_units": availability_check.get("min_available", 0),
                    "max_occupancy": f"{room_type.max_adults} adults, {room_type.max_children} children",
                    "amenities": room_type.amenities,
                    "size": room_type.size_sqm,
                    "rate_info": lowest_rate,
                }

                available_rooms.append(room_info)

            # Format response
            if not available_rooms:
                response += "No rooms available for the selected dates and guest count."
            else:
                for room in available_rooms:
                    status = "✅ Available" if room["available"] else "❌ Not Available"
                    response += f"**{room['name']}** - {status}\n"

                    if room["available"]:
                        if room["rate_info"]:
                            rate = room["rate_info"]
                            response += f"Price: {rate['currency']} {rate['rate_per_night']:.2f}/night\n"
                            response += f"Total: {rate['currency']} {rate['total_amount']:.2f} for {nights} nights\n"

                        response += f"Available units: {room['available_units']}\n"
                        response += f"Max occupancy: {room['max_occupancy']}\n"

                        if room["size"]:
                            response += f"Size: {room['size']} m²\n"

                        if room["amenities"]:
                            response += (
                                f"Amenities: {', '.join(room['amenities'][:5])}\n"
                            )

                    response += "\n"

            return response

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
    """Create a new reservation using Cloudbeds PMS.

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
    if not PMS_AVAILABLE:
        return f"""**Reservation Request**

I apologize, but the PMS (Property Management System) integration is currently not available for creating reservations.

**Your Reservation Details:**
- Guest: {guest_first_name} {guest_last_name}
- Email: {guest_email}
- Phone: {guest_phone}
- Check-in: {check_in}
- Check-out: {check_out}
- Guests: {adults} adults{f', {children} children' if children > 0 else ''}
- Room Type ID: {room_type_id}
{f'- Special Requests: {special_requests}' if special_requests else ''}

**To complete your reservation:**
Please contact the hotel directly:
- Call the front desk for immediate assistance
- Visit our website for online booking
- Email us with your reservation details

We apologize for any inconvenience and look forward to welcoming you!"""

    try:
        # Parse dates
        check_in_date = datetime.strptime(check_in, "%Y-%m-%d").date()
        check_out_date = datetime.strptime(check_out, "%Y-%m-%d").date()

        # Use hotel_id from context if not provided
        if not hotel_id and hasattr(ctx.context, "hotel_id"):
            hotel_id = ctx.context.hotel_id

        if not hotel_id:
            return "Hotel ID not available in context."

        # Get PMS client
        client = await get_pms_client(hotel_id)
        if not client:
            return "PMS integration not configured for this hotel."

        async with client:
            # Get reservation service
            reservation_service = ReservationService(client)
            availability_service = AvailabilityService(client)

            # First check availability
            availability_check = await availability_service.check_availability(
                start_date=check_in_date,
                end_date=check_out_date,
                room_type_id=room_type_id,
                rooms_needed=1,
                adults=adults,
                children=children,
            )

            if not availability_check["available"]:
                return (
                    f"Room type {room_type_id} is not available for the selected dates."
                )

            # Create guest object
            guest = Guest(
                first_name=guest_first_name,
                last_name=guest_last_name,
                email=guest_email,
                phone=guest_phone,
            )

            # Create room assignment
            room = ReservationRoom(
                room_type_id=room_type_id,
                room_type_name="",  # Will be filled by PMS
                adults=adults,
                children=children,
            )

            # Create reservation request
            reservation_request = ReservationCreateRequest(
                property_id=client.tenant_config.property_id,
                check_in=check_in_date,
                check_out=check_out_date,
                primary_guest=guest,
                rooms=[room],
                special_requests=special_requests,
                source="hotel_bot",
            )

            # Create the reservation
            reservation = await reservation_service.create_reservation(
                reservation_request
            )

            if reservation:
                response = f"**Reservation Created Successfully!**\n\n"
                response += f"Reservation ID: {reservation.reservation_id}\n"
                response += (
                    f"Confirmation Code: {reservation.confirmation_code or 'Pending'}\n"
                )
                response += f"Guest: {guest_first_name} {guest_last_name}\n"
                response += f"Email: {guest_email}\n"
                response += f"Check-in: {check_in}\n"
                response += f"Check-out: {check_out}\n"
                response += f"Nights: {reservation.nights}\n"
                response += f"Guests: {adults} adults"
                if children > 0:
                    response += f", {children} children"
                response += f"\nTotal Amount: {reservation.currency} {reservation.total_amount:.2f}\n"
                response += f"Status: {reservation.status.value.title()}\n"

                if special_requests:
                    response += f"Special Requests: {special_requests}\n"

                response += "\nThank you for your reservation!"

                return response
            else:
                return "Failed to create reservation. Please try again or contact the hotel directly."

    except ValueError:
        return "Invalid date format. Please use YYYY-MM-DD format."
    except Exception as e:
        return f"Error creating reservation: {str(e)}"


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
    if not PMS_AVAILABLE:
        return "**Reservation Search**\n\nI apologize, but the PMS integration is currently not available for searching reservations. Please contact the hotel front desk directly for assistance with finding your reservation."

    try:
        # Use hotel_id from context if not provided
        if not hotel_id and hasattr(ctx.context, "hotel_id"):
            hotel_id = ctx.context.hotel_id

        if not hotel_id:
            return "Hotel ID not available in context."

        # Get PMS client
        client = await get_pms_client(hotel_id)
        if not client:
            return "PMS integration not configured for this hotel."

        async with client:
            # Get reservation service
            reservation_service = ReservationService(client)

            # Build search parameters
            search_params = ReservationSearchParams(limit=10)

            if guest_email:
                search_params.guest_email = guest_email
            if confirmation_code:
                search_params.confirmation_code = confirmation_code
            if check_in_from:
                search_params.check_in_from = datetime.strptime(
                    check_in_from, "%Y-%m-%d"
                ).date()
            if check_in_to:
                search_params.check_in_to = datetime.strptime(
                    check_in_to, "%Y-%m-%d"
                ).date()

            # Search reservations
            reservations = await reservation_service.get_reservations(search_params)

            if not reservations:
                return "No reservations found matching the search criteria."

            response = f"**Found {len(reservations)} Reservation(s)**\n\n"

            for reservation in reservations:
                response += f"**Reservation ID:** {reservation.reservation_id}\n"
                if reservation.confirmation_code:
                    response += (
                        f"**Confirmation Code:** {reservation.confirmation_code}\n"
                    )
                response += f"**Guest:** {reservation.primary_guest.first_name} {reservation.primary_guest.last_name}\n"
                response += f"**Email:** {reservation.primary_guest.email}\n"
                response += f"**Check-in:** {reservation.check_in}\n"
                response += f"**Check-out:** {reservation.check_out}\n"
                response += f"**Nights:** {reservation.nights}\n"
                response += f"**Status:** {reservation.status.value.title()}\n"
                response += f"**Total Amount:** {reservation.currency} {reservation.total_amount:.2f}\n"

                if reservation.rooms:
                    response += f"**Rooms:** {len(reservation.rooms)} room(s)\n"
                    for i, room in enumerate(reservation.rooms, 1):
                        response += (
                            f"  Room {i}: {room.room_type_name} ({room.adults} adults"
                        )
                        if room.children > 0:
                            response += f", {room.children} children"
                        response += ")\n"

                if reservation.special_requests:
                    response += (
                        f"**Special Requests:** {reservation.special_requests}\n"
                    )

                response += "\n---\n\n"

            return response

    except ValueError:
        return "Invalid date format. Please use YYYY-MM-DD format."
    except Exception as e:
        return f"Error searching reservations: {str(e)}"


@function_tool
async def get_reservation_details(
    ctx: RunContextWrapper[Any], reservation_id: str, hotel_id: Optional[str] = None
) -> str:
    """Get detailed information about a specific reservation.

    Args:
        reservation_id: The reservation ID
        hotel_id: The hotel ID. If not provided, uses the current hotel context.
    """
    if not PMS_AVAILABLE:
        return f"**Reservation Details**\n\nI apologize, but the PMS integration is currently not available for retrieving reservation details for ID: {reservation_id}. Please contact the hotel front desk directly for assistance."

    try:
        # Use hotel_id from context if not provided
        if not hotel_id and hasattr(ctx.context, "hotel_id"):
            hotel_id = ctx.context.hotel_id

        if not hotel_id:
            return "Hotel ID not available in context."

        # Get PMS client
        client = await get_pms_client(hotel_id)
        if not client:
            return "PMS integration not configured for this hotel."

        async with client:
            # Get reservation service
            reservation_service = ReservationService(client)

            # Get reservation details
            reservation = await reservation_service.get_reservation(
                reservation_id, include_rate_details=True
            )

            if not reservation:
                return f"Reservation {reservation_id} not found."

            response = f"**Reservation Details**\n\n"
            response += f"**Reservation ID:** {reservation.reservation_id}\n"
            if reservation.confirmation_code:
                response += f"**Confirmation Code:** {reservation.confirmation_code}\n"

            # Guest information
            response += f"\n**Guest Information:**\n"
            response += f"Name: {reservation.primary_guest.first_name} {reservation.primary_guest.last_name}\n"
            response += f"Email: {reservation.primary_guest.email}\n"
            if reservation.primary_guest.phone:
                response += f"Phone: {reservation.primary_guest.phone}\n"
            if reservation.primary_guest.country:
                response += f"Country: {reservation.primary_guest.country}\n"

            # Stay information
            response += f"\n**Stay Information:**\n"
            response += f"Check-in: {reservation.check_in}\n"
            response += f"Check-out: {reservation.check_out}\n"
            response += f"Nights: {reservation.nights}\n"
            response += f"Total Guests: {reservation.total_guests}\n"
            response += f"Status: {reservation.status.value.title()}\n"

            # Room information
            if reservation.rooms:
                response += f"\n**Room Information:**\n"
                for i, room in enumerate(reservation.rooms, 1):
                    response += f"Room {i}: {room.room_type_name}\n"
                    response += f"  Guests: {room.adults} adults"
                    if room.children > 0:
                        response += f", {room.children} children"
                    response += "\n"
                    if room.room_id:
                        response += f"  Room Number: {room.room_id}\n"
                    if room.rate_plan_name:
                        response += f"  Rate Plan: {room.rate_plan_name}\n"
                    response += (
                        f"  Amount: {reservation.currency} {room.total_amount:.2f}\n"
                    )

            # Financial information
            response += f"\n**Financial Information:**\n"
            response += (
                f"Total Amount: {reservation.currency} {reservation.total_amount:.2f}\n"
            )
            response += (
                f"Paid Amount: {reservation.currency} {reservation.paid_amount:.2f}\n"
            )
            response += f"Balance: {reservation.currency} {reservation.balance:.2f}\n"

            # Additional information
            if reservation.special_requests:
                response += f"\n**Special Requests:**\n{reservation.special_requests}\n"

            if reservation.notes:
                response += f"\n**Notes:**\n{reservation.notes}\n"

            if reservation.source:
                response += f"\n**Booking Source:** {reservation.source}\n"

            response += f"\n**Created:** {reservation.created_at}\n"
            if reservation.modified_at:
                response += f"**Last Modified:** {reservation.modified_at}\n"

            return response

    except Exception as e:
        return f"Error retrieving reservation details: {str(e)}"


@function_tool
async def get_room_types_info(
    ctx: RunContextWrapper[Any], hotel_id: Optional[str] = None
) -> str:
    """Get information about available room types.

    Args:
        hotel_id: The hotel ID. If not provided, uses the current hotel context.
    """
    if not PMS_AVAILABLE:
        return "**Room Types Information**\n\nI apologize, but the PMS integration is currently not available for retrieving room type information. Please contact the hotel front desk directly or visit our website for room details and amenities."

    try:
        # Use hotel_id from context if not provided
        if not hotel_id and hasattr(ctx.context, "hotel_id"):
            hotel_id = ctx.context.hotel_id

        if not hotel_id:
            return "Hotel ID not available in context."

        # Get PMS client
        client = await get_pms_client(hotel_id)
        if not client:
            return "PMS integration not configured for this hotel."

        async with client:
            # Get room service
            room_service = RoomService(client)

            # Get room types
            room_types = await room_service.get_room_types()

            if not room_types:
                return "No room types found for this hotel."

            response = f"**Available Room Types**\n\n"

            for room_type in room_types:
                response += f"**{room_type.name}**\n"
                response += f"ID: {room_type.room_type_id}\n"

                if room_type.description:
                    response += f"Description: {room_type.description}\n"

                response += f"Max Occupancy: {room_type.max_adults} adults, {room_type.max_children} children\n"
                response += f"Default Occupancy: {room_type.default_adults} adults, {room_type.default_children} children\n"

                if room_type.size_sqm:
                    response += f"Size: {room_type.size_sqm} m²\n"

                if room_type.bed_type:
                    response += f"Bed Type: {room_type.bed_type}\n"

                response += f"Total Units: {room_type.total_units}\n"
                response += f"Available Units: {room_type.available_units}\n"

                if room_type.amenities:
                    response += f"Amenities: {', '.join(room_type.amenities)}\n"

                if room_type.base_rate:
                    response += f"Base Rate: {room_type.currency} {room_type.base_rate:.2f}/night\n"

                response += "\n"

            return response

    except Exception as e:
        return f"Error retrieving room types: {str(e)}"
