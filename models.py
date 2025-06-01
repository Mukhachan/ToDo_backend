from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
# Модель пользователя
class User(BaseModel):
    id: UUID
    email: EmailStr
    hashed_password: str

# Модель для регистрации пользователя
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)

# Модель пользователя для хранения в БД
class UserInDB(User):
    pass

# Модель токена доступа
class Token(BaseModel):
    access_token: str
    token_type: str

# Базовая модель задачи
class TaskBase(BaseModel):
    title: str = Field(..., min_length=0, max_length=100)
    description: Optional[str] = Field(None, min_length=0,  max_length=500)
    status: bool = False  # False - не выполнено, True - выполнено

# Модель для создания задачи
class TaskCreate(TaskBase):
    title: str
    description: str
    status: bool

# Модель для обновления задачи (частичная)
class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    status: Optional[bool]

# Полная модель задачи с дополнительными полями
class Task(TaskBase):
    num: int
    id: UUID
    owner_id: UUID
    created_at: datetime

class Sorting(BaseModel):
    sorting: str
