from datetime import datetime, timedelta  # Used for handling token expiration times in JWT
from typing import Annotated  # Used for type hinting and dependency injection in FastAPI
from fastapi import Depends, HTTPException, APIRouter, status  # Core FastAPI features: dependency injection, error handling, routing, and status codes
from pydantic import BaseModel  # For defining request/response data models with validation
from sqlalchemy.orm import Session  # For database session management with SQLAlchemy ORM
# Removed unused import: Request from starlette.requests
from database import SessionLocal  # Custom import: provides a database session instance
from database_models import Users  # Custom import: ORM model for user data
from passlib.context import CryptContext  # For securely hashing and verifying passwords
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm  # Implements OAuth2 authentication flows in FastAPI
from jose import jwt  # For encoding, decoding, and handling JWT tokens


router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

SECRET_KEY = '19b8f6e3b4c3d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5g6h7i8j9k0l'
ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

class CreateUserRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@router.post('/', status_code=status.HTTP_201_CREATED)
def create_user(db: Session = Depends(get_db), create_user_request: CreateUserRequest = Depends()):
    password = create_user_request.password[:72]  # Truncate password to 72 bytes
    create_user_model = Users(
        username=create_user_request.username,
        hashed_password=bcrypt_context.hash(password),
    )
    db.add(create_user_model)
    db.commit()

def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    token = create_access_token(user.id, expires_delta=timedelta(minutes=30))
    return {'access_token': token, 'token_type': 'bearer'}
    return {'access_token': token, 'token_type': 'bearer'}


def authenticate_user(db, username: str, password: str):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    password = password[:72]  # Truncate password to 72 bytes
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user
from datetime import timezone

def create_access_token(user_id: int, expires_delta: timedelta | None = None):
    encode = {'sub': str(user_id)}
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    encode.update({'exp': expire})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)
    