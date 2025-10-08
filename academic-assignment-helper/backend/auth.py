from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from . import models, schemas, database
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Security configs
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# --- Helper functions ---
def hash_password(password: str) -> str:
    # bcrypt has a 72-byte limit; 
    if isinstance(password, bytes):
        password = password.decode("utf-8", errors="ignore")
    password = password[:72]  # truncate if necessary
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if isinstance(plain_password, bytes):
        plain_password = plain_password.decode("utf-8", errors="ignore")
    plain_password = plain_password[:72]
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# --- Register ---
@router.post("/register", response_model=schemas.StudentOut)
def register_student(student: schemas.StudentCreate, db: Session = Depends(database.get_db)):
    existing = db.query(models.Student).filter(models.Student.email == student.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = hash_password(student.password)
    new_student = models.Student(
        email=student.email,
        password_hash=hashed_pw,
        full_name=student.full_name,
        student_id=student.student_id,
    )
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student


# --- Login ---
@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.Student).filter(models.Student.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


# --- Current user dependency ---
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.Student).filter(models.Student.email == email).first()
    if user is None:
        raise credentials_exception
    return user
