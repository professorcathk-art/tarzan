from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://tarzan:tarzan@localhost:5432/tarzan"
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""
    supabase_jwt_secret: str = ""
    cors_origins: str = "http://localhost:3000"

    eodhd_api_key: str = ""
    finnhub_api_key: str = ""
    resend_api_key: str = ""
    resend_from_email: str = "Tarzan Screener <onboarding@resend.dev>"
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_pro: str = ""

    app_url: str = "http://localhost:3000"
    api_url: str = "http://localhost:8000"

    skip_auth: bool = False
    use_finbert: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
