from pprint import pprint
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from uuid import UUID, uuid4
from jose import JWTError, jwt
from datetime import timedelta, datetime


from config import *
from models import (
    UserCreate,
    User,
    UserInDB,
    Token,
    TaskCreate,
    Task,
    TaskUpdate,
)
from auth_utils import (
    verify_password,
    get_password_hash,
    create_access_token,
)

from fastapi.security import OAuth2PasswordBearer

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
# Создаём таблиц
db_connect().init_tables()


def get_user_by_email(email: str) -> UserInDB | None:
    """Получить пользователя из БД по email, вернуть модель UserInDB"""
    conn = db_connect()
    row = conn.get_user_by_email(email)
    if not row:
        return None
    
    return UserInDB(id=UUID(row["id"]), email=row["email"], hashed_password=row["hashed_password"])

def get_user_by_id(user_id: UUID) -> UserInDB | None:
    """Получить пользователя из БД по id, вернуть модель UserInDB"""
    conn = db_connect()
    row = conn.get_user_by_id(user_id)
    if not row:
        return None
    return UserInDB(id=UUID(row["id"]), email=row["email"], hashed_password=row["hashed_password"])

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    """Получить текущего пользователя по JWT токену"""

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception
    user = get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    return user


@app.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate):
    existing_user = get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")
    conn = db_connect()
    user_id = uuid4()
    hashed_password = get_password_hash(user.password)
    conn.create_user(user_id=user_id, email=user.email, hashed_password=hashed_password)
    return User(id=user_id, email=user.email, hashed_password="string")

@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Неправильный email или пароль")
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token, 
        "token_type": "bearer"
    }

@app.post("/tasks/", response_model=Task)
def create_task(task: TaskCreate, current_user: UserInDB = Depends(get_current_user)):
    task_id = uuid4()
    created_at = datetime.now()
    conn = db_connect()
    conn.create_task(
        task_id=task_id,
        owner_id=current_user.id,
        title=task.title,
        description=task.description,
        status=task.status,
        created_at=created_at,
    )
    return Task(
        id=task_id,
        owner_id=current_user.id,
        title=task.title,
        description=task.description,
        status=task.status,
        created_at=created_at,
    )

@app.get("/tasks/", response_model=List[Task])
def read_tasks(current_user: UserInDB = Depends(get_current_user)):
    conn = db_connect()
    rows = conn.get_tasks_by_owner(current_user.id, sorting="ASC")
    tasks: List[Task] = []
    for i,r in enumerate(rows):

        tasks.append(
            Task(
                num=i+1,
                id=UUID(hex=r["id"]),
                owner_id=UUID(hex=r["owner_id"]),
                title=r["title"],
                description=r["description"],
                status=bool(r["status"]),
                created_at=datetime.fromisoformat(r["created_at"]),
            )
        )
    return tasks

@app.get("/tasks/{task_id}", response_model=Task)
def read_task(task_id: UUID, current_user: UserInDB = Depends(get_current_user)):
    conn = db_connect()
    row = conn.get_task_by_id(task_id)
    if not row or UUID(row["owner_id"]) != current_user.id:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return Task(
        id=UUID(row["id"]),
        owner_id=UUID(row["owner_id"]),
        title=row["title"],
        description=row["description"],
        status=bool(row["status"]),
        created_at=datetime.fromisoformat(row["created_at"]),
    )

@app.put("/tasks/{task_id}", response_model=Task)
def update_task(
    task_id: UUID, task_update: TaskUpdate, current_user: UserInDB = Depends(get_current_user)
    ):
    conn = db_connect()
    row = conn.get_task_by_id(task_id)

    if not row or UUID(row["owner_id"]) != current_user.id:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    conn.update_task(
        task_id=task_id,
        title=task_update.title,
        description=task_update.description,
        status=task_update.status,
    )
    updated_row = conn.get_task_by_id(task_id)
    return Task(
        num=1,
        id=UUID(updated_row["id"]),
        owner_id=UUID(updated_row["owner_id"]),
        title=updated_row["title"],
        description=updated_row["description"],
        status=bool(updated_row["status"]),
        created_at=datetime.fromisoformat(updated_row["created_at"]),
    )

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: UUID, current_user: UserInDB = Depends(get_current_user)):
    conn = db_connect()
    row = conn.get_task_by_id(task_id)
    if not row or UUID(row["owner_id"]) != current_user.id:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    conn.delete_task(task_id)
    return

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": str(current_user.id)}, expires_delta=access_token_expires
    )
    return User(id=current_user.id, email=current_user.email, hashed_password=access_token)

