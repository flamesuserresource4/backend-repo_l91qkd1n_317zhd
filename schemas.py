"""
Database Schemas for Lawn Mowing App

Define MongoDB collection schemas using Pydantic models.
Each Pydantic model maps to a collection with the lowercase class name.
- Quote -> "quote"
- Booking -> "booking"
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import date

class Quote(BaseModel):
    """
    Quote requests and computed results
    Collection: "quote"
    """
    name: str = Field(..., description="Customer full name")
    email: EmailStr = Field(..., description="Customer email")
    address: str = Field(..., description="Service address")
    zip_code: str = Field(..., min_length=4, max_length=10, description="ZIP/Postal code")
    lawn_size_sqft: int = Field(..., ge=100, le=100000, description="Estimated lawn size in square feet")
    frequency: str = Field(..., pattern="^(once|biweekly|weekly)$", description="Service frequency")
    extras: List[str] = Field(default_factory=list, description="Selected extras e.g., edging, leaf_cleanup, pet_waste")
    base_price: float = Field(..., ge=0, description="Calculated base price before discounts and fees")
    discount: float = Field(..., ge=0, description="Total discount applied")
    extras_total: float = Field(..., ge=0, description="Total extras price")
    service_fee: float = Field(..., ge=0, description="Service/booking fee")
    total: float = Field(..., ge=0, description="Final total price")

class Booking(BaseModel):
    """
    Confirmed bookings
    Collection: "booking"
    """
    quote_id: Optional[str] = Field(None, description="Associated quote document id")
    name: str = Field(..., description="Customer full name")
    email: EmailStr = Field(...)
    phone: str = Field(..., min_length=7, max_length=20)
    address: str = Field(...)
    zip_code: str = Field(...)
    lawn_size_sqft: int = Field(..., ge=100, le=100000)
    frequency: str = Field(..., pattern="^(once|biweekly|weekly)$")
    extras: List[str] = Field(default_factory=list)
    notes: Optional[str] = Field(None)
    preferred_date: Optional[date] = Field(None, description="Preferred service date")
    price_total: float = Field(..., ge=0, description="Total price confirmed at booking time")
    status: str = Field("confirmed", description="Booking status")
