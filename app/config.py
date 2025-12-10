from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = 'Library-API'
    admin_email: str = ''
    database_url: str = ''

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')