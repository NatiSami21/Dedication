# auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

#from . import models, schemas, database
import models, schemas, database   # absolute imports for Docker
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

load_dotenv()

router = APIRouter(prefix="/auth", tags=["Authentication"])

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    if isinstance(password, bytes):
        password = password.decode("utf-8", errors="ignore")
    return pwd_context.hash(password[:72])


def verify_password(plain: str, hashed: str) -> bool:
    if isinstance(plain, bytes):
        plain = plain.decode("utf-8", errors="ignore")
    return pwd_context.verify(plain[:72], hashed)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/register", response_model=schemas.StudentOut)
def register_student(student: schemas.StudentCreate, db: Session = Depends(database.get_db)):
    if db.query(models.Student).filter(models.Student.email == student.email).first():
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


@router.post("/login", response_model=schemas.Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.Student).filter(models.Student.email == form.username).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token(
        {"sub": user.email},
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.Student).filter(models.Student.email == email).first()
    if not user:
        raise credentials_exception
    return user
