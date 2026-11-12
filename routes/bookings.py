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


