from src.core.application_exceptions import ApplicationException


class CreateTaskException(ApplicationException):
    def __init__(self, message="Ошибка при создании задачи", *, cause=None):
        super().__init__(message, status_code=500, cause=cause)

class GetTaskException(ApplicationException):
    def __init__(self, message="Ошибка при получении задачи", *, cause=None):
        super().__init__(message, status_code=500, cause=cause)

class DeleteTaskException(ApplicationException):
    def __init__(self, message="Ошибка при удалении задачи", *, cause=None):
        super().__init__(message, status_code=500, cause=cause)

class ListTaskException(ApplicationException):
    def __init__(self, message="Ошибка получения списка задач", *, cause=None):
        super().__init__(message, status_code=500, cause=cause)

class GetTaskStatusException(ApplicationException):
    def __init__(self, message="Ошибка получения статуса задачи", *, cause=None):
        super().__init__(message, status_code=500, cause=cause)

class UpdateTaskException(ApplicationException):
    def __init__(self, message="Ошибка обновления статуса задачи", *, cause=None):
        super().__init__(message, status_code=500, cause=cause)
