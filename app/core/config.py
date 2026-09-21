from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Library-API"
    admin_email: str = ""
    admin_password: str = ""
    admin_name: str = ""

    database_url: str = ""
    db_echo: bool = True

    hash_algorithm: str = ""
    jwt_algorithm: str = ""
    secret_key: str = ""
    access_token_expire_minutes: int = 15

    base_upload_path: str = ""
    profile_pic_max_bytes: int = 2 * 1024 * 1024
    audit_enabled: bool | None = None
    late_fee_per_day: int = 100

    mock_admin_email: str = ""
    mock_admin_password: str = ""
    mock_admin_name: str = ""

    mock_user_email: str = ""
    mock_user_password: str = ""
    mock_user_name: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    seed_books: bool = False


settings = Settings()
