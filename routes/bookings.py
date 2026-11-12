from decimal import Decimal
from math import ceil
from flask import g, jsonify, request
from app import app
from config import db
from helpers import error, load_or_400, paginate, roles_required
from models import Booking, Property, Unit
from schemas import BookingSchema, BookingStatusSchema, PageSchema, StatusFilterSchema

booking_schema = BookingSchema()

TRANSITIONS = {
    "pending": {"confirmed", "cancelled"},
    "confirmed": {"cancelled", "completed"},
}

def months_between(start, end):
    """Rent is charged per month; part of a month counts as a full month."""
    return max(1, ceil((end - start).days / 30))

def can_view(user, booking):
    if user.role == "admin":
        return True
    if user.role == "customer":
        return booking.customer_id == user.id
    return booking.unit.property.manager_id == user.id


