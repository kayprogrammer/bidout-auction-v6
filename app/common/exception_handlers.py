from http import HTTPStatus
from starlite import (
    HTTPException,
    ValidationException,
    Response,
    Request,
    status_codes,
)
from starlite.status_codes import HTTP_500_INTERNAL_SERVER_ERROR


class Error(Exception):
    """Base class for exceptions in this module."""

    pass


class RequestError(Error):
    def __init__(
        self, err_msg: str, status_code: int = 400, data: dict = None, *args: object
    ) -> None:
        self.status_code = HTTPStatus(status_code)
        self.err_msg = err_msg
        self.data = data

        super().__init__(*args)


def request_error_handler(_: Request, exc: RequestError):
    err_dict = {
        "status": "failure",
        "message": exc.err_msg,
    }
    if exc.data:
        err_dict["data"] = exc.data
    return Response(status_code=exc.status_code, content=err_dict)


def http_exception_handler(_: Request, exc: HTTPException) -> Response:
    return Response(
        content={"status": "failure", "message": exc.detail},
        status_code=exc.status_code,
    )


def validation_exception_handler(_: Request, exc: ValidationException) -> Response:
    # Get the original 'detail' list of errors
    details = exc.extra
    modified_details = {}
    for error in details:
        try:
            field_name = error["loc"][1]
        except:
            field_name = error["loc"][0]

        modified_details[f"{field_name}"] = error["msg"]
    return Response(
        status_code=status_codes.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "failure",
            "message": "Invalid Entry",
            "data": modified_details,
        },
    )


def internal_server_error_handler(_: Request, exc: Exception) -> Response:
    print(exc)
    return Response(
        content={
            "status": "failure",
            "message": "Server Error",
        },
        status_code=500,
    )


exc_handlers = {
    ValidationException: validation_exception_handler,
    HTTPException: http_exception_handler,
    HTTP_500_INTERNAL_SERVER_ERROR: internal_server_error_handler,
    RequestError: request_error_handler,
}
