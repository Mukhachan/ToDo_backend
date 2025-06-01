import json
import os
import sqlite3

from database import DataBase

params = json.load(open('params.json'))
# Секретный ключ для кодирования JWT токенов
SECRET_KEY = params["SECRET_KEY"]  # В продакшене использовать переменные окружения или менеджер секретов
ALGORITHM = params["ALGORITHM"]
ACCESS_TOKEN_EXPIRE_MINUTES = params["ACCESS_TOKEN_EXPIRE_MINUTES"]

DB_NAME = "our.db"


def db_connect():
    if os.path.exists(DB_NAME):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        return DataBase(conn, cur)
    else:
        conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        cur = conn.cursor()
        return DataBase(conn, cur) 
    