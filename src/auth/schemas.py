from pydantic import BaseModel
from typing import Optional
import uuid

# 토큰 응답 모델
class Token(BaseModel):
    access_token: str
    token_type: str
    
# 사용자 기본 모델
class UserModel(BaseModel):
    username: str
    is_active: bool = True
    
# 회원가입용 사용자 모델
class UserCreateModel(BaseModel):
    username : str
    password: str
    
class UserLoginModel(BaseModel):
    username: str
    password: str
    
# API 응답용 사용자 모델
class UserResponseModel(BaseModel):
    id: int
    
    class Config:
        orm_mode = True
        
#DB용 사용자 모델
class UserInDB(BaseModel):
    hashed_password: str
    
class TokenVerifyModel(BaseModel):
    access_token: str
    refresh_token: str

class TokenVerifyResponse(BaseModel):
    message: str
    access_token: Optional[str] = None