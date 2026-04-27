from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class DrawingReadModel(BaseModel):
    id: str
    title: str
    owner_id: str
    created_at: datetime
    # Зверніть увагу: ми повертаємо не список об'єктів користувачів, які поставили лайк, 
    # а лише їхню кількість, оскільки для відображення стрічки цього зазвичай достатньо.
    likes_count: int 

class UserReadModel(BaseModel):
    id: str
    email: str
