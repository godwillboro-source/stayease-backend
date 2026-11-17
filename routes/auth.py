from flask import g, jsonify, request, session

from app import app
from config import db
from email_service import EmailDeliveryError, send_sign_in_notification, send_welcome_email
from helpers import error, load_or_400, roles_required
from models import User
from schemas import LoginSchema, RegisterSchema, UserSchema

user_schema = UserSchema()
session_user_schema = UserSchema(only=("id", "name", "role"))


@app.post("/api/auth/register")
def register():
    """Create a customer or manager account.
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [name, email, password, role]
          properties:
            name: {type: string}
            email: {type: string, format: email}
            phone: {type: string}
            password: {type: string, format: password}
            role: {type: string, enum: [manager, customer]}
    responses:
      201:
        description: Account created.
      400:
        description: Invalid registration data.
      409:
        description: Email is already registered.
    """
    data = load_or_400(RegisterSchema(), request.get_json(silent=True))
    email = data["email"].lower()
    if User.query.filter_by(email=email).first():
        return error("Email already registered", 409)

    user = User(
        name=data["name"],
        email=email,
        phone=data.get("phone"),
        role=data["role"],
        # managers wait for admin approval, customers can use the app straight away
        is_approved=(data["role"] != "manager"),
    )
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()

    email_sent = True
    try:
        send_welcome_email(user.email, user.name)
    except EmailDeliveryError as exc:
        app.logger.warning("Welcome email delivery failed for user id %s: %s", user.id, exc)
        email_sent = False

    message = "Registered successfully"
    if user.role == "manager":
        message += ". An admin must approve your account before you can list properties"
    return jsonify({
        "message": message,
        "user": user_schema.dump(user),
        "email_sent": email_sent,
    }), 201


@app.post("/api/auth/login")
def login():
    """Log in and create a session.
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [email, password]
          properties:
            email: {type: string, format: email}
            password: {type: string, format: password}
    responses:
      200:
        description: Login succeeded.
      401:
        description: Invalid email or password.
      403:
        description: Account is blocked.
    """
    data = load_or_400(LoginSchema(), request.get_json(silent=True))
    user = User.query.filter_by(email=data["email"].lower()).first()
    if not user or not user.check_password(data["password"]):
        return error("Invalid email or password", 401)
    if not user.is_active:
        return error("This account has been blocked", 403)

    session.clear()
    session["user_id"] = user.id
    email_notification_sent = True
    try:
        send_sign_in_notification(user.email, user.name)
    except EmailDeliveryError as exc:
        app.logger.warning("Sign-in notification failed for user id %s: %s", user.id, exc)
        email_notification_sent = False
    return jsonify({
        "user": session_user_schema.dump(user),
        "email_notification_sent": email_notification_sent,
    })


@app.delete("/api/auth/logout")
@roles_required()
def logout():
    """End the current session.
    ---
    tags:
      - Authentication
    responses:
      200:
        description: Session ended.
      401:
        description: Authentication required.
    """
    session.clear()
    return jsonify({"message": "Logged out successfully"})


@app.get("/api/auth/me")
@roles_required()
def me():
    """Return the current user's basic profile.
    ---
    tags:
      - Authentication
    responses:
      200:
        description: Current user.
      401:
        description: Authentication required.
    """
    return jsonify(session_user_schema.dump(g.current_user))