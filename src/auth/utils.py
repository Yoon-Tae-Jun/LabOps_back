from passlib.context import CryptContext
from datetime import timedelta, datetime, timezone
import jwt
from src.config import Config
import uuid
import logging

ACCESS_TOKEN_EXPIRY=1

passwd_context = CryptContext(
    schemes=['bcrypt']
)

def generate_password_hash(password: str) -> str:
    hashed_pw=passwd_context.hash(password)
    
    return hashed_pw

def verify_password(password: str, hashed_pw: str) -> bool:
    return passwd_context.verify(password, hashed_pw)

def create_access_token(user_data: dict, expiry: timedelta = None, refresh: bool = False):
    payload = {}
    
    payload['user'] = user_data
    payload['exp'] = datetime.now(timezone.utc) + (
        expiry if expiry is not None else timedelta(hours=ACCESS_TOKEN_EXPIRY))
    
    payload['jti'] = str(uuid.uuid4())
    payload['refresh'] = refresh
    
    token = jwt.encode(
        payload=payload,
        key=Config.JWT_SECRET_KEY,
        algorithm=Config.JWT_ALGORITHM
    )

    return token

def decode_token(token: str) -> dict:
    try:
        token_data = jwt.decode(
            jwt=token,
            key=Config.JWT_SECRET_KEY,
            algorithms=[Config.JWT_ALGORITHM]
        )
        
        return token_data
    except jwt.PyJWTError as e:
        logging.exception(e)
        return None
    

