"""
Request/Response utility functions
"""

from fastapi.responses import JSONResponse
from fastapi import status
from typing import Any, Optional


def success_response(data: Any, message: str = None) -> JSONResponse:
    content = {"status": "success", "data": data}
    if message:
        content["message"] = message
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=content
    )


def created_response(data: Any, message: str = "Created successfully") -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "status": "success",
            "message": message,
            "data": data
        }
    )


def error_response(message: str, code: int, details: Any = None) -> JSONResponse:
    content = {"status": "error", "message": message}
    if details:
        content["details"] = details
    return JSONResponse(status_code=code, content=content)


def unauthorized_response(message: str = "Unauthorized") -> JSONResponse:
    return error_response(message, status.HTTP_401_UNAUTHORIZED)


def forbidden_response(message: str = "Forbidden") -> JSONResponse:
    return error_response(message, status.HTTP_403_FORBIDDEN)


def not_found_response(message: str = "Not found") -> JSONResponse:
    return error_response(message, status.HTTP_404_NOT_FOUND)


def bad_request_response(message: str, details: Any = None) -> JSONResponse:
    return error_response(message, status.HTTP_400_BAD_REQUEST, details)


def internal_server_error_response(message: str = "Internal server error") -> JSONResponse:
    return error_response(message, status.HTTP_500_INTERNAL_SERVER_ERROR)


def validation_error_response(errors: list) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "message": "Validation error",
            "details": errors
        }
    )
