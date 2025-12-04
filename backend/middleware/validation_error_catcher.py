# backend/exceptions/handlers.py
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import logging

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        field = ".".join(str(x) for x in error['loc'])
        error_type = error['type']
        msg = error['msg']
        errors.append({
            "field": field,
            "status": "ERROR",
            "error_type": error_type,
            "message": msg,
            "input_value": error.get('input')
        })

    error_details_str = "\n".join([
        f"  Field: {err['field']}\n"
        f"    Status: {err['status']}\n"
        f"    Error Type: {err['error_type']}\n"
        f"    Message: {err['message']}\n"
        f"    Input Value: {err['input_value']}"
        for err in errors
    ])

    logging.error(
        f"Validation error for request {request.method} {request.url.path}:\n"
        f"{error_details_str}"
    )

    content = {
        'status_code': 10422,
        'message': 'Validation failed',
        'details': errors
    }
    return JSONResponse(content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)