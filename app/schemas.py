from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Any

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str = Field(min_length=6)

class UserOut(UserBase):
    id: int
    is_pro: bool
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AnalysisCreate(BaseModel):
    title: str
    content: str

class AnalysisOut(BaseModel):
    id: int
    title: str
    input_summary: str
    result_json: Any
    class Config:
        from_attributes = True
