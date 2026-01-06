from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = 'Library-API'
    admin_email: str = ''
    admin_password: str = ''
    admin_name: str = ''

    database_url: str = ''
    test_database_url: str = ''

    hash_algorithm: str = ''
    jwt_algorithm: str = ''
    secret_key: str = ''
    access_token_expire_minutes: int = 15

    test_mode: bool = False

    mock_admin_email: str = ''
    mock_admin_password: str = ''
    mock_admin_name: str = ''

    mock_user_email: str = ''
    mock_user_password: str = ''
    mock_user_name: str = ''

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
