"""Pydantic models for the Hotel Bot API."""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class MessageRole(str, Enum):
    """Message roles for chat."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """Chat message model."""

    role: MessageRole
    content: str
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    """Chat request model."""

    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(
        None, description="Session ID for conversation continuity"
    )
    hotel_id: Optional[str] = Field(None, description="Hotel ID for context")
    conversation_id: Optional[int] = Field(None, description="Chatwoot conversation ID for HITL")
    user_context: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional user context"
    )


class ChatResponse(BaseModel):
    """Chat response model."""

    message: str = Field(..., description="Assistant response")
    session_id: str = Field(..., description="Session ID")
    agent_used: Optional[str] = Field(
        None, description="Which agent handled the request"
    )
    tools_used: Optional[List[str]] = Field(
        default_factory=list, description="Tools used in response"
    )
    handoff_occurred: bool = Field(
        default=False, description="Whether a handoff occurred"
    )


class BookingRequest(BaseModel):
    """Booking request model."""

    check_in: date = Field(..., description="Check-in date")
    check_out: date = Field(..., description="Check-out date")
    guests: int = Field(..., ge=1, le=10, description="Number of guests")
    children: int = Field(default=0, ge=0, le=10, description="Number of children")
    room_type: Optional[str] = Field(None, description="Preferred room type")
    guest_first_name: str = Field(..., description="Guest first name")
    guest_last_name: str = Field(..., description="Guest last name")
    guest_email: str = Field(..., description="Guest email")
    guest_phone: str = Field(..., description="Guest phone")
    special_requests: Optional[str] = Field(None, description="Special requests")
    hotel_id: Optional[str] = Field(None, description="Hotel ID")


class BookingResponse(BaseModel):
    """Booking response model."""

    booking_id: str = Field(..., description="Booking confirmation ID")
    status: str = Field(..., description="Booking status")
    confirmation_code: Optional[str] = Field(None, description="Confirmation code")
    check_in: date = Field(..., description="Check-in date")
    check_out: date = Field(..., description="Check-out date")
    nights: int = Field(..., description="Number of nights")
    room_type: str = Field(..., description="Room type booked")
    total_amount: float = Field(..., description="Total booking amount")
    currency: str = Field(default="EUR", description="Currency")
    guest_name: str = Field(..., description="Primary guest name")
    message: str = Field(..., description="Booking confirmation message")


class AvailabilityRequest(BaseModel):
    """Room availability request model."""

    check_in: date = Field(..., description="Check-in date")
    check_out: date = Field(..., description="Check-out date")
    guests: int = Field(..., ge=1, le=10, description="Number of guests")
    children: int = Field(default=0, ge=0, le=10, description="Number of children")
    hotel_id: Optional[str] = Field(None, description="Hotel ID")


class RoomAvailability(BaseModel):
    """Room availability response model."""

    room_type: str
    available: bool
    price_per_night: Optional[float] = None
    currency: str = "EUR"
    total_price: Optional[float] = None
    amenities: List[str] = Field(default_factory=list)


class AvailabilityResponse(BaseModel):
    """Availability response model."""

    check_in: date
    check_out: date
    nights: int
    rooms: List[RoomAvailability]
    hotel_id: str


class ServiceRequest(BaseModel):
    """Hotel service request model."""

    service_type: str = Field(..., description="Type of service requested")
    description: str = Field(..., description="Service description")
    room_number: Optional[str] = Field(None, description="Room number if applicable")
    priority: str = Field(default="normal", description="Priority level")
    scheduled_time: Optional[datetime] = Field(
        None, description="Scheduled time for service"
    )


class ServiceResponse(BaseModel):
    """Service request response model."""

    request_id: str
    status: str
    estimated_completion: Optional[datetime] = None
    message: str


class HotelInfo(BaseModel):
    """Hotel information model."""

    id: str
    name: str
    description: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    amenities: List[str] = Field(default_factory=list)
    policies: Optional[Dict[str, Any]] = None


class ActivityInfo(BaseModel):
    """Hotel activity information model."""

    id: str
    title: str
    description: Optional[str] = None
    price: Optional[float] = None
    currency: str = "EUR"
    duration_minutes: Optional[int] = None
    max_participants: Optional[int] = None
    category: Optional[str] = None
    available_times: List[str] = Field(default_factory=list)


class FacilityInfo(BaseModel):
    """Hotel facility information model."""

    id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    operating_hours: Optional[str] = None
    location: Optional[str] = None
    is_featured: bool = False


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
