from abc import ABC, abstractmethod


class CustomHTTPException(Exception, ABC):
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    @abstractmethod
    def get_error_code(self):
        pass


class BadRequestException(CustomHTTPException):
    def __init__(self, message: str):
        super().__init__(message, status_code=400)

    def get_error_code(self):
        return 400


class ConflictException(CustomHTTPException):
    def __init__(self, message):
        super().__init__(message=message, status_code=409)

    def get_error_code(self):
        return 409


class InternalServerError(CustomHTTPException):
    def __init__(self, message):
        super().__init__(message=message, status_code=500)

    def get_error_code(self):
        return 500


class NotFoundException(CustomHTTPException):
    def __init__(self, message):
        super().__init__(message=message, status_code=404)

    def get_error_code(self):
        return 404
