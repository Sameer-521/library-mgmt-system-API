from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError
from app.core.config import Settings
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app import crud
from app.utils import generate_admin_id
from app.core.database import get_session
from app.models import User
from passlib.context import CryptContext

settings = Settings()

HASH_ALGORITHM = settings.hash_algorithm
JWT_ALGORITHM = settings.jwt_algorithm
SECRET_KEY = settings.secret_key

pwd_context = CryptContext(schemes=[HASH_ALGORITHM], deprecated='auto')

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/login')

credentials_exception = HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        detail='Invalid credentials',
        headers={'WWW-Authenticate': 'Bearer'}
    )

token_expire_exception = HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail='Token has expired. Please login again'
        )

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, user: User, expires_delta: Optional[timedelta] = None):
    role = None
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    if user.is_staff and user.is_superuser:
        role = 'admin'
    elif user.is_staff:
        role = 'staff'
    else:
        role = 'user'
    to_encode.update({'exp': expire, 'role': role})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, JWT_ALGORITHM)
    return encoded_jwt

def decode_token(token: str, verify_exp: bool=True):
    payload = jwt.decode(token, SECRET_KEY, 
                         algorithms=[JWT_ALGORITHM], options={'verify_exp': verify_exp})
    return payload
    
async def authenticate_user(
        credentials: dict,
        db: AsyncSession=Depends(get_session)
        ):
    exceptions = []
    user = None
    try:
        user_password = credentials['password']
        user_email = credentials['email']
        
        user = await crud.get_user_by_email(db, user_email)
        print(user)
        if not user or not verify_password(user_password, user.password):
            exceptions.append(credentials_exception)
    except Exception as e:
        print(f'Error: {e}')
    finally:
        return user, exceptions

async def get_current_user(
        token: str=Depends(oauth2_scheme), 
        db: AsyncSession=Depends(get_session)
        ):
    exceptions = []
    user = None
    role = ''
    try:
        payload = decode_token(token)
        email = payload.get('sub')
        #user_uid = payload.get('user_uid')
        role = payload.get('role')
        if not email:
            exceptions.append(token_expire_exception)
        else:
            user = await crud.get_user_by_email(db, email)
        if not user:
            exceptions.append(credentials_exception)
    except ExpiredSignatureError:
        exceptions.append(token_expire_exception)
    except JWTError as e:
        print(f'JWTError: {e}')
        exceptions.append(credentials_exception)
    finally:
        return user, role, exceptions

async def get_current_active_user(user_role_exc: tuple = Depends(get_current_user)):
    current_user, role, exc = user_role_exc
    if not current_user:
        exc.append(credentials_exception)
        return current_user, role, exc
    if not current_user.is_active:
        exc.append(HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail='Inactive user'
        ))
    return current_user, role, exc

async def get_current_staff_user(user_role_exc: tuple = Depends(get_current_active_user)):
    current_user, role, exc = user_role_exc
    if not current_user:
        exc.append(credentials_exception)
        return current_user, role, exc
    if role not in ['staff', 'admin']:
        exc.append(HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail='Not enough previliges'
        ))
    return current_user, role, exc

async def get_current_admin_user(user_role_exc: tuple = Depends(get_current_active_user)):
    current_user, role, exc = user_role_exc
    if not current_user:
        exc.append(credentials_exception)
        return current_user, role, exc
    if role != 'admin':
        exc.append(HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail='Not enough previliges'
        ))
    return current_user, role, exc

async def create_superuser(
        db: AsyncSession, 
        email=settings.admin_email,
        password=settings.admin_password,
        full_name=settings.admin_name
        ):
    try:
        superuser = await crud.get_default_superuser(db, email)
        if not superuser:
            data = {
                'full_name': full_name,
                'user_uid': generate_admin_id(),
                'password': hash_password(password),
                'email': email,
                'is_staff': True,
                'is_superuser': True
            }
            admin_user = User(**data)
            await crud.create_default_superuser(db, admin_user)
        print('Superuser initialized')
    except SQLAlchemyError as e:
        await db.rollback()
        print(f'DataBase error initializing admin_user: {e}')
    else:
        await db.commit()

async def create_mock_superuser(
        db: AsyncSession, 
        email=settings.mock_admin_email,
        password=settings.mock_admin_password,
        full_name=settings.mock_admin_name
        ):
    try:
        data = {
            'full_name': full_name,
            'password': hash_password(password),
            'email': email,
            'is_staff': True,
            'is_superuser': True
        }
        mock_admin_user = User(**data)
        await crud.create_default_superuser(db, mock_admin_user)
        print('Mock Superuser initialized for testing')
    except SQLAlchemyError as e:
        await db.rollback()
        print(f'DataBase error initializing mock_admin_user: {e}')
    else:
        await db.commit()
