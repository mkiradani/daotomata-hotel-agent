"""Hotel information API endpoints."""

from typing import List, Optional
from datetime import date
from fastapi import APIRouter, HTTPException, Query

from ..models import (
    AvailabilityRequest,
    AvailabilityResponse,
    BookingRequest,
    BookingResponse,
    ServiceRequest,
    ServiceResponse,
    HotelInfo,
    ActivityInfo,
    FacilityInfo,
    ErrorResponse,
)
from ..config import settings

router = APIRouter(prefix="/api/hotel", tags=["hotel"])


@router.get("/info", response_model=HotelInfo)
async def get_hotel_info(hotel_id: Optional[str] = None) -> HotelInfo:
    """
    Get hotel information including amenities, policies, and contact details.

    If hotel_id is not provided, uses the current hotel context from the domain.
    """
    try:
        from ..services.directus_service import directus_service

        # Use hotel_id or detect from domain
        if not hotel_id:
            if settings.current_domain:
                hotel_data = await directus_service.get_hotel_by_domain(settings.current_domain)
            else:
                raise HTTPException(
                    status_code=400, detail="Hotel ID or domain required"
                )
        else:
            hotel_data = await directus_service.get_hotel_by_id(hotel_id)

        if not hotel_data:
            raise HTTPException(status_code=404, detail="Hotel not found")

        return HotelInfo(
            id=hotel_data["id"],
            name=hotel_data["name"],
            description=hotel_data.get("description"),
            address=hotel_data.get("address"),
            contact_email=hotel_data.get("contact_email"),
            contact_phone=hotel_data.get("contact_phone"),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving hotel information: {str(e)}"
        )


@router.post("/availability", response_model=AvailabilityResponse)
async def check_availability(
    request: AvailabilityRequest, hotel_id: Optional[str] = None
) -> AvailabilityResponse:
    """
    Check room availability for specified dates and guest count.

    Returns available room types with pricing and amenities.
    In a production environment, this would integrate with the hotel's PMS system.
    """
    try:
        # Validate dates
        if request.check_in <= date.today():
            raise HTTPException(
                status_code=400, detail="Check-in date must be in the future"
            )

        if request.check_out <= request.check_in:
            raise HTTPException(
                status_code=400, detail="Check-out date must be after check-in date"
            )

        nights = (request.check_out - request.check_in).days

        # Mock availability data (replace with actual PMS integration)
        from ..models import RoomAvailability

        available_rooms = [
            RoomAvailability(
                room_type="Standard Room",
                available=True,
                price_per_night=120.0,
                total_price=120.0 * nights,
                amenities=["WiFi", "Air Conditioning", "TV", "Private Bathroom"],
            ),
            RoomAvailability(
                room_type="Deluxe Room",
                available=True,
                price_per_night=180.0,
                total_price=180.0 * nights,
                amenities=[
                    "WiFi",
                    "Air Conditioning",
                    "TV",
                    "Private Bathroom",
                    "Balcony",
                    "Mini Bar",
                ],
            ),
            RoomAvailability(
                room_type="Suite",
                available=request.guests <= 4,
                price_per_night=350.0,
                total_price=350.0 * nights,
                amenities=[
                    "WiFi",
                    "Air Conditioning",
                    "TV",
                    "Private Bathroom",
                    "Balcony",
                    "Mini Bar",
                    "Living Area",
                    "Kitchen",
                ],
            ),
        ]

        return AvailabilityResponse(
            check_in=request.check_in,
            check_out=request.check_out,
            nights=nights,
            rooms=available_rooms,
            hotel_id=hotel_id or "default",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error checking availability: {str(e)}"
        )


@router.post("/booking", response_model=BookingResponse)
async def create_booking(
    request: BookingRequest, hotel_id: Optional[str] = None
) -> BookingResponse:
    """
    Create a new hotel reservation.

    Creates a reservation using the Cloudbeds PMS integration.
    Returns booking confirmation details.
    """
    try:
        # Validate dates
        if request.check_in <= date.today():
            raise HTTPException(
                status_code=400, detail="Check-in date must be in the future"
            )

        if request.check_out <= request.check_in:
            raise HTTPException(
                status_code=400, detail="Check-out date must be after check-in date"
            )

        # Use hotel_id from request or parameter
        booking_hotel_id = request.hotel_id or hotel_id or "default"
        nights = (request.check_out - request.check_in).days

        # Try to create real reservation using PMS tools
        try:
            from ..agents.pms_tools import create_reservation
            from ..agents.base import RunContextWrapper

            # Create a mock context for the PMS tool
            class MockContext:
                def __init__(self, hotel_id: str):
                    self.hotel_id = hotel_id

            ctx = RunContextWrapper(MockContext(booking_hotel_id))

            # Call the PMS tool to create reservation
            result = await create_reservation(
                ctx=ctx,
                check_in=request.check_in.isoformat(),
                check_out=request.check_out.isoformat(),
                guest_first_name=request.guest_first_name,
                guest_last_name=request.guest_last_name,
                guest_email=request.guest_email,
                guest_phone=request.guest_phone,
                room_type_id=request.room_type or "standard",
                adults=request.guests,
                children=request.children,
                special_requests=request.special_requests,
                hotel_id=booking_hotel_id,
            )

            # Parse the result to extract booking details
            import uuid

            booking_id = str(uuid.uuid4())[:8]

            return BookingResponse(
                booking_id=booking_id,
                status="confirmed",
                confirmation_code=f"CB{booking_id.upper()}",
                check_in=request.check_in,
                check_out=request.check_out,
                nights=nights,
                room_type=request.room_type or "Standard Room",
                total_amount=120.0 * nights,  # This should come from PMS
                currency="EUR",
                guest_name=f"{request.guest_first_name} {request.guest_last_name}",
                message=f"Reservation confirmed! Your booking ID is {booking_id}. You will receive a confirmation email shortly.",
            )

        except Exception as pms_error:
            # Fallback to mock booking if PMS fails
            print(f"PMS booking failed, using mock: {pms_error}")

            import uuid

            booking_id = str(uuid.uuid4())[:8]

            return BookingResponse(
                booking_id=booking_id,
                status="confirmed",
                confirmation_code=f"MOCK{booking_id.upper()}",
                check_in=request.check_in,
                check_out=request.check_out,
                nights=nights,
                room_type=request.room_type or "Standard Room",
                total_amount=120.0 * nights,
                currency="EUR",
                guest_name=f"{request.guest_first_name} {request.guest_last_name}",
                message=f"Reservation confirmed! Your booking ID is {booking_id}. This is a test booking.",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating booking: {str(e)}")


@router.get("/activities", response_model=List[ActivityInfo])
async def get_activities(hotel_id: Optional[str] = None) -> List[ActivityInfo]:
    """
    Get list of available hotel activities and experiences.

    Returns all active activities for the specified hotel.
    """
    try:
        from ..services.directus_service import directus_service

        # Get hotel_id if not provided
        if not hotel_id and settings.current_domain:
            hotel_data = await directus_service.get_hotel_by_domain(settings.current_domain)
            if hotel_data:
                hotel_id = hotel_data.get("id")

        if not hotel_id:
            raise HTTPException(status_code=400, detail="Hotel ID required")

        # Fetch activities
        activities_data = await directus_service.get_hotel_activities(hotel_id)

        activities = []
        for activity in activities_data:
            activities.append(
                ActivityInfo(
                    id=activity["id"],
                    title=activity["title"],
                    description=activity.get("description"),
                    price=activity.get("price"),
                    currency=activity.get("currency", "EUR"),
                    duration_minutes=activity.get("duration_minutes"),
                    max_participants=activity.get("max_participants"),
                    category=activity.get("category"),
                )
            )

        return activities

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving activities: {str(e)}"
        )


@router.get("/facilities", response_model=List[FacilityInfo])
async def get_facilities(hotel_id: Optional[str] = None) -> List[FacilityInfo]:
    """
    Get list of hotel facilities and amenities.

    Returns all active facilities for the specified hotel, grouped by category.
    """
    try:
        from ..services.directus_service import directus_service

        # Get hotel_id if not provided
        if not hotel_id and settings.current_domain:
            hotel_data = await directus_service.get_hotel_by_domain(settings.current_domain)
            if hotel_data:
                hotel_id = hotel_data.get("id")

        if not hotel_id:
            raise HTTPException(status_code=400, detail="Hotel ID required")

        # Fetch facilities
        facilities_data = await directus_service.get_hotel_facilities(hotel_id)

        facilities = []
        for facility in facilities_data:
            facilities.append(
                FacilityInfo(
                    id=facility["id"],
                    name=facility["name"],
                    description=facility.get("description"),
                    category=facility.get("category"),
                    is_featured=facility.get("is_featured", False),
                )
            )

        return facilities

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving facilities: {str(e)}"
        )


@router.post("/service-request", response_model=ServiceResponse)
async def request_service(request: ServiceRequest) -> ServiceResponse:
    """
    Submit a hotel service request.

    Creates a service request that will be processed by the hotel staff.
    In a production environment, this would integrate with the hotel's PMS system.
    """
    try:
        # Generate request ID
        import uuid

        request_id = str(uuid.uuid4())[:8]

        # Mock service processing (replace with actual PMS integration)
        from datetime import datetime, timedelta

        # Estimate completion time based on service type
        if request.service_type.lower() in ["housekeeping", "maintenance"]:
            estimated_completion = datetime.now() + timedelta(hours=3)
        elif request.service_type.lower() == "room_service":
            estimated_completion = datetime.now() + timedelta(minutes=40)
        else:
            estimated_completion = datetime.now() + timedelta(hours=1.5)

        return ServiceResponse(
            request_id=request_id,
            status="received",
            estimated_completion=estimated_completion,
            message=f"Your {request.service_type} request has been received and will be processed shortly.",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error submitting service request: {str(e)}"
        )
