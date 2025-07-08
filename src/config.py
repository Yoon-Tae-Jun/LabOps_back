from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # JWT 설정
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRY: int   # 토큰 만료 시간
    
    # 데이터베이스 설정
    DATABASE_URL: str
    
    # .env 파일 설정
    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
Config = Settings()