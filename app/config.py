from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+psycopg2://mentoria_admin:adminmentoria%402025@170.78.97.36:5464/mentoria"
    )
    access_token_ttl_minutes: int = 60 * 24

    model_config = SettingsConfigDict(env_file=".env", env_prefix="MENTORIA_", extra="allow")


settings = Settings()
