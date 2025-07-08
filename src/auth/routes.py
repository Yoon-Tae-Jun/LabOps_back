from fastapi import APIRouter, Depends, status, Response
from fastapi import HTTPException, Header
from typing import Optional
from fastapi.responses import JSONResponse
from .schemas import UserCreateModel, UserModel, UserLoginModel, TokenVerifyModel, TokenVerifyResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db import get_session
from .service import UserService
from .utils import verify_password, create_access_token, decode_token
from datetime import timedelta, datetime, timezone
from .dependencies import AccessTokenBearer, RefreshTokenBearer

auth_router = APIRouter()
user_service = UserService()

REFRESH_TOKEN_EXPIRY = 1

@auth_router.post("/signup", response_model=UserModel, status_code=status.HTTP_200_OK)
async def create_user_account(
    user_data: UserCreateModel,
    session: AsyncSession = Depends(get_session)
):
    username = user_data.username
    
    user_exists = await user_service.user_exists(username, session)
    
    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User with username already exists"
        )
    
    new_user = await user_service.create_user(user_data, session)
    
    return new_user

@auth_router.post('/login')
async def login_users(login_data:UserLoginModel, session: AsyncSession = Depends(get_session)):
    username = login_data.username
    password = login_data.password
    
    user = await user_service.get_user_by_username(username, session)
    
    if user is not None:
        password_valid = verify_password(password, user.password_hash)
        
        if password_valid:
            access_token = create_access_token(
                user_data={
                    'username' : user.username,
                    'user_uid' : str(user.uid)
                }
            )
            
            refresh_token = create_access_token(
                user_data={
                    'username' : user.username,
                    'user_uid' : str(user.uid)
                },
                refresh = True,
                expiry=timedelta(days=REFRESH_TOKEN_EXPIRY)
            )
            
            return JSONResponse(
                content={
                    "message" : "Login successful",
                    "access_token" : access_token,
                    "refresh_token" : refresh_token,
                    "user" : {
                        "username" : user.username,
                        "uid": str(user.uid)
                    }
                }
            ) #{"access_token": access_token, "token_type": "bearer"}
            
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid username or Password"
    )
   
""" 
@auth_router.get('/token')
async def get_new_access_token( response: Response,
                               Authorization: str = Header(..., description="Bearer access_token"),
                               refresh_token: Optional[str] = Header(alias="refresh", description="refresh_token")
):
    
    # 1. Authorization 헤더 형식 검증
    if not Authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is required"
        )
    
    if not Authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected 'Bearer <token>'"
        )
    
    # Bearer 다음에 토큰이 실제로 있는지 확인
    access_token = Authorization.split(" ", 1)
    if len(access_token) != 2 or not access_token[1].strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must contain a valid token after 'Bearer '"
        )
    
    # 2. Access token 추출 및 디코딩
    access_token = access_token[1].strip()
    access_token_details = decode_token(access_token)
    # 2. Refresh token 디코딩
    refresh_token_details = decode_token(refresh_token)
    
    access_token_exp = access_token_details.get("exp")
    refresh_token_exp = refresh_token_details.get("exp")
    
    #expiry_timestamp = token_details['exp']
    #token_expiry = datetime.fromtimestamp(expiry_timestamp)
    
    # 1. access token 유효
    if access_token_exp and datetime.fromtimestamp(access_token_exp) > datetime.now(timezone.utc):
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            
            content={
                "message" : "Access token is still valid. No need to refresh."
            }
        )
                
    # 2. refresh token 만료 -> 재로그인
    if refresh_token_exp is None or (datetime.fromtimestamp(refresh_token_exp) <= datetime.now(timezone.utc)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired. Please login again."
        )
        
    # 3. access token 만료, refresh 토큰 유효 -> 새 access token 발급
    new_access_token = create_access_token(
                user_data=refresh_token_details['user']
            )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            'access_token': new_access_token
        })
    
    # scenario 2
    if token_expiry <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Or expired refresh token. Please login again."
        )
    
    # scenario 3
    new_access_token = create_access_token(user_data=token_details['user'])
    
    if datetime.fromtimestamp(expiry_timestamp) > datetime.now(timezone.utc):
        new_access_token = create_access_token(
            user_data=token_details['user']
        )
        
        
        new_refresh_token = create_access_token(
            user_data=token_details['user'],
            refresh=True
        )
        
        
        return JSONResponse(content={
            'access_token': new_access_token
            #'refresh_token': new_refresh_token
            })
        
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid Or expired token"
    )
"""

@auth_router.post('/verify')
async def get_new_access_token( response: Response,
                               token_data: TokenVerifyModel
                               #Authorization: str = Header(..., description="Bearer access_token"),
                               #refresh_token: Optional[str] = Header(alias="refresh", description="refresh_token")
):
    # 1. Request Body에서 토큰 추출
    access_token = token_data.access_token.strip()
    refresh_token = token_data.refresh_token.strip()
    
    # 2. 토큰 존재 여부 확인
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Access token is required"
        )
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token is required"
        )
    
    # 3. Access token 디코딩
    access_token_details = decode_token(access_token)
    
    # 4. Refresh token 디코딩
    refresh_token_details = decode_token(refresh_token)
    
    """
    # 5. 토큰 유효성 기본 검사
    if access_token_details is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or malformed access token"
        )
    
    if refresh_token_details is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or malformed refresh token"
        )
    """
    # 7. 만료 시간 추출
    try:
        access_token_exp = access_token_details.get("exp")
        refresh_token_exp = refresh_token_details.get("exp")
    except:
        # 8. 시나리오별 처리
        
        # 시나리오 1: access, refresh 만료 재로그인
        if access_token_details is None:
            if refresh_token_details is None:
                raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired. Please login again."
            )
            # 시나리오 2: aceess 만료 refresh 유효 -> access 토큰 재발급
            else:
                new_access_token = create_access_token(
                user_data=refresh_token_details['user']
            )
            
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content={
                        "status_code": status.HTTP_200_OK,
                        "message": "New access token issued successfully.",
                        "access_token": new_access_token
                    }
                )
    # 시나리오 3: access token 유효
    if access_token_exp and datetime.fromtimestamp(access_token_exp, tz=timezone.utc) > datetime.now(timezone.utc):
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status_code": status.HTTP_200_OK,
                "message": "Access token is still valid. No need to refresh.",
                "expires_in": int(access_token_exp - datetime.now(timezone.utc).timestamp())
            }
        )
        