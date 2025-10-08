from pydantic import BaseModel, EmailStr
from typing import Optional

class StudentCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    student_id: Optional[str] = None


class StudentLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class StudentOut(BaseModel):
    id: int
    email: str
    full_name: Optional[str]

    class Config:
        orm_mode = True
