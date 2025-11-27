from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    RABBITMQ_URL: str = Field("amqp://gosdep:gosdep@rabbitmq:5672/")
    MAX_ATTEMPTS: int = Field(5)
    RETRY_DELAYS_MS: str = Field("30")
    EXCHANGE_TASKS: str = Field("tasks_exchange")
    OUTBOX_EXCHANGE: str = Field("tasks")

    QUEUE_HIGH: str = Field("high")
    QUEUE_MEDIUM: str = Field("medium")
    QUEUE_LOW: str = Field("low")

    DLX: str = Field("tasks_dlx")
    DLQ: str = Field("tasks_dlq")

    ROUTING_KEY_HIGH: str = Field("high")
    ROUTING_KEY_MEDIUM: str = Field("medium")
    ROUTING_KEY_LOW: str = Field("low")

    DEFAULT_PREFETCH_COUNT: int = Field(10)
    WORKER_CONCURRENCY: int = Field(4)
    PREFETCH_COUNT: int = Field(10)

    PAGE_SIZE: int = Field(20)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        env_nested_delimiter = "__"
        env_prefix = ""


settings = Settings()
