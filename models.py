from datetime import datetime, timezone

from sqlalchemy.ext.hybrid import hybrid_property

from config import bcrypt, db

ROLES = ("admin", "manager", "customer")
UNIT_TYPES = ("bedsitter", "studio", "1_bedroom", "2_bedroom", "3_bedroom", "4_bedroom")
PROPERTY_STATUSES = ("pending", "approved", "rejected")
BOOKING_STATUSES = ("pending", "confirmed", "cancelled", "completed")


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(db.Model):
    """One table for all three roles: admin, manager, customer."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    _password_hash = db.Column(db.String, nullable=False)
    role = db.Column(db.String(20), nullable=False, default="customer")
    # Managers must be approved by an admin before they can list properties.
    is_approved = db.Column(db.Boolean, nullable=False, default=True)
    # An admin can block a user.
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    properties = db.relationship(
        "Property", back_populates="manager", cascade="all, delete-orphan"
    )
    bookings = db.relationship(
        "Booking", back_populates="customer", cascade="all, delete-orphan"
    )

    @hybrid_property
    def password_hash(self):
        raise AttributeError("Password hashes may not be viewed.")

    @password_hash.setter
    def password_hash(self, password):
        self._password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def authenticate(self, password):
        return bcrypt.check_password_hash(self._password_hash, password)

    def __repr__(self):
        return f"<User {self.id} {self.username} ({self.role})>"


class City(db.Model):
    """Managed by the admin. A manager picks one when registering a property."""
    __tablename__ = "cities"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    # A city that still has properties cannot be deleted (checked in the route).
    properties = db.relationship("Property", back_populates="city")

    def __repr__(self):
        return f"<City {self.id} {self.name}>"


class Property(db.Model):
    """A building / apartment complex registered by a manager."""
    __tablename__ = "properties"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    area = db.Column(db.String(100))  # estate / neighbourhood inside the city
    address = db.Column(db.String(255))
    image_url = db.Column(db.String(500))
    # pending -> approved / rejected, decided by an admin
    status = db.Column(db.String(20), nullable=False, default="pending")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    manager_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey("cities.id"), nullable=False)

    manager = db.relationship("User", back_populates="properties")
    city = db.relationship("City", back_populates="properties")
    units = db.relationship(
        "Unit", back_populates="property", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Property {self.id} {self.name}>"


class Unit(db.Model):
    """A rentable type inside a property, e.g. '2 bedroom at 20,000 a month'."""
    __tablename__ = "units"
    __table_args__ = (
        db.CheckConstraint("price_per_month >= 0", name="price_positive"),
        db.CheckConstraint("available_units <= total_units", name="availability"),
    )

    id = db.Column(db.Integer, primary_key=True)
    unit_type = db.Column(db.String(30), nullable=False)  # see UNIT_TYPES
    price_per_month = db.Column(db.Float, nullable=False)
    bathrooms = db.Column(db.Integer, default=1)
    amenities = db.Column(db.String(500))  # comma separated: "wifi,parking,water"
    image_url = db.Column(db.String(500))
    total_units = db.Column(db.Integer, nullable=False, default=1)
    available_units = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    property_id = db.Column(db.Integer, db.ForeignKey("properties.id"), nullable=False)

    property = db.relationship("Property", back_populates="units")
    bookings = db.relationship(
        "Booking", back_populates="unit", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Unit {self.id} {self.unit_type} {self.price_per_month}>"


class Booking(db.Model):
    """A customer's booking of a unit."""
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    total_price = db.Column(db.Float)
    # pending -> confirmed -> completed, or cancelled
    status = db.Column(db.String(20), nullable=False, default="pending")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    customer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey("units.id"), nullable=False)

    customer = db.relationship("User", back_populates="bookings")
    unit = db.relationship("Unit", back_populates="bookings")

    def __repr__(self):
        return f"<Booking {self.id} {self.status}>"
