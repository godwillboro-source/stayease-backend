from io import BytesIO
from unittest.mock import patch


def test_image_upload_requires_manager_login(client):
    response = client.post(
        "/api/uploads/images",
        data={"image": (BytesIO(b"image-data"), "building.jpg")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 401


def test_image_upload_requires_cloudinary_configuration(client, manager_h):
    response = client.post(
        "/api/uploads/images",
        headers=manager_h,
        data={"image": (BytesIO(b"image-data"), "building.jpg")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 503
    assert response.get_json()["error"] == "Image uploads are not configured"


def test_image_upload_returns_cloudinary_url(client, manager_h, app):
    app.config.update(
        CLOUDINARY_CLOUD_NAME="test-cloud",
        CLOUDINARY_API_KEY="test-key",
        CLOUDINARY_API_SECRET="test-secret",
    )
    cloudinary_result = {
        "secure_url": "https://res.cloudinary.com/test-cloud/image/upload/building.jpg"
    }
    with patch("routes.uploads.cloudinary.uploader.upload", return_value=cloudinary_result) as upload:
        response = client.post(
            "/api/uploads/images",
            headers=manager_h,
            data={"image": (BytesIO(b"image-data"), "building.jpg")},
            content_type="multipart/form-data",
        )

    assert response.status_code == 201
    assert response.get_json() == {"image_url": cloudinary_result["secure_url"]}
    assert upload.call_args.kwargs["folder"] == "stayease/properties"
    assert upload.call_args.kwargs["allowed_formats"] == ["jpg", "jpeg", "png", "webp"]


def test_image_upload_rejects_non_image_files(client, manager_h, app):
    app.config.update(
        CLOUDINARY_CLOUD_NAME="test-cloud",
        CLOUDINARY_API_KEY="test-key",
        CLOUDINARY_API_SECRET="test-secret",
    )
    response = client.post(
        "/api/uploads/images",
        headers=manager_h,
        data={"image": (BytesIO(b"plain text"), "notes.txt")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Image must be a JPEG, PNG, or WebP file"
