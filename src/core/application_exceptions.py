class ApplicationException(Exception):
    def __init__(self, message, status_code=400, *, cause=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.cause = cause


class DatabaseException(ApplicationException):
    def __init__(self, message="Ошибка базы данных", *, cause=None):
        super().__init__(message, status_code=500, cause=cause)

