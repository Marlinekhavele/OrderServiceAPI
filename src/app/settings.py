from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENV_NAME: str = "local"

    # PostgreSQL
    DB_HOST: str = "localhost"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "password"
    DB_PORT: int = 5432
    DB_NAME: str = "order_service"

    @property
    def DB_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"  # noqa: E231

    @property
    def DB_URL_SYNC(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"  # noqa: E231


settings = Settings()
