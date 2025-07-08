from fastapi import Request, status
from fastapi.security import HTTPBearer
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.exceptions import HTTPException
from .utils import decode_token

def get_token() -> None:
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
    
    return oauth2_scheme

class TokenBearer(HTTPBearer):
    def __init__(self, auto_error=True):
        super().__init__(auto_error=auto_error)
        
    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        creds = await super().__call__(request)
        
        token = creds.credentials
        
        token_data = decode_token(token)
        
        if not self.token_valid(token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error":"This token is invalid or expired",
                    "resolution":"Please get new token"
                }
            )
            
        self.verify_token_data(token_data)
        
        return token_data
    def token_valid(self, token: str) -> bool:
        token_data = decode_token(token)
        
        return token_data is not True
        
    def verify_token_data(self, token_data):
        raise NotImplementedError("Please Override this method in child classes")
        
class AccessTokenBearer(TokenBearer):
    def verify_token_data(self, token_data:dict) -> None:
        if token_data and token_data['refresh']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please provide an access token"
            )

class RefreshTokenBearer(TokenBearer):
    def verify_token_data(self, token_data:dict) -> None:
        if token_data and not token_data['refresh']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please provide an refresh token"
            )