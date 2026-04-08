from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import List, Optional

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    nickname: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Layer schemas
class LayerBase(BaseModel):
    image_data: str

class LayerCreate(LayerBase):
    pass

class LayerResponse(LayerBase):
    id: int
    drawing_id: int
    author_id: int
    author_nickname: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Drawing schemas
class DrawingBase(BaseModel):
    title: str

class DrawingCreate(DrawingBase):
    first_layer_data: str

class DrawingResponse(DrawingBase):
    id: int
    owner_id: int
    owner_email: Optional[str] = None
    owner_nickname: Optional[str] = None
    created_at: datetime
    layers: List[LayerResponse] = []
    likes_count: int = 0

    class Config:
        from_attributes = True

# Feed Drawing
class FeedDrawing(BaseModel):
    id: int
    owner_id: int
    owner_email: Optional[str] = None
    owner_nickname: Optional[str] = None
    title: str
    created_at: datetime
    likes_count: int

    class Config:
        from_attributes = True
