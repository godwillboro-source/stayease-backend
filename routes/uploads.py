from io import BytesIO

import cloudinary
import cloudinary.uploader
from cloudinary.exceptions import Error as CloudinaryError
from flask import current_app, jsonify, request

from app import app
from helpers import error, roles_required

MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_MIMETYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_IMAGE_FORMATS = ["jpg", "jpeg", "png", "webp"]


@app.post("/api/uploads/images")
@roles_required("manager", approved_only=True)
def upload_image():
    """Upload a property image and return its Cloudinary URL.
    ---
    tags:
      - Uploads
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: image
        type: file
        required: true
    responses:
      201:
        description: Image uploaded.
      400:
        description: Missing, invalid, or oversized image.
      401:
        description: Authentication required.
      403:
        description: An approved manager account is required.
      503:
        description: Cloudinary is not configured.
    """
    image = request.files.get("image")
    if image is None or not image.filename:
        return error("Choose an image to upload", 400)
    if image.mimetype not in ALLOWED_IMAGE_MIMETYPES:
        return error("Image must be a JPEG, PNG, or WebP file", 400)

    image_data = image.stream.read(MAX_IMAGE_SIZE_BYTES + 1)
    if len(image_data) > MAX_IMAGE_SIZE_BYTES:
        return error("Image must be 5 MB or smaller", 400)
    if not image_data:
        return error("The selected image is empty", 400)

    cloudinary_settings = {
        "cloud_name": current_app.config["CLOUDINARY_CLOUD_NAME"],
        "api_key": current_app.config["CLOUDINARY_API_KEY"],
        "api_secret": current_app.config["CLOUDINARY_API_SECRET"],
    }
    if not all(cloudinary_settings.values()):
        return error("Image uploads are not configured", 503)

    cloudinary.config(**cloudinary_settings, secure=True)
    try:
        result = cloudinary.uploader.upload(
            BytesIO(image_data),
            folder="stayease/properties",
            resource_type="image",
            allowed_formats=ALLOWED_IMAGE_FORMATS,
        )
    except CloudinaryError:
        current_app.logger.exception("Cloudinary image upload failed")
        return error("Image upload failed", 502)

    image_url = result.get("secure_url")
    if not image_url:
        current_app.logger.error("Cloudinary upload response did not include secure_url")
        return error("Image upload failed", 502)
    return jsonify({"image_url": image_url}), 201
