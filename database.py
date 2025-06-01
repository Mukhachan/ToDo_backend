import sqlite3
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class DataBase:
    def __init__(self, connection: sqlite3.Connection, cursor: sqlite3.Cursor):
        self.conn = connection
        self.cursor = cursor
        # Для того чтобы получать данные в виде списка словарей
        self.conn.row_factory = sqlite3.Row
        self.cursor.row_factory = sqlite3.Row

    def init_tables(self) -> bool:
        """ Создаём таблицы в базе данных если их нет"""
        try:
            self.cursor.executescript(open("sql_db.sql").read())
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error in DataBase.init_tables: {e}")
            return False

    def get_user_by_email(self, email: str) -> Optional[sqlite3.Row]:
        """ Получаем пользователя по email """
        sql = (
            "SELECT * FROM users WHERE email = ?"
        )
        try:
            self.cursor.execute(sql, (email,))
            return self.cursor.fetchone()
        except Exception as e:
            print(f"Error in DataBase.get_user_by_email: {e}")
            return None
        
    def get_user_by_id(self, user_id: UUID) -> Optional[sqlite3.Row]:
        """ Получаем пользователя по id """
        sql = (
            "SELECT * FROM users WHERE id = ?"
        )
        try:
            self.cursor.execute(sql, (str(user_id),))
            return self.cursor.fetchone()
        except Exception as e:
            print(f"Error in DataBase.get_user_by_id: {e}")
            return None

    def create_user(self, user_id: UUID, email: str, hashed_password: str) -> bool:
        """ Создаём пользователя """
        sql = (
            "INSERT INTO users (id, email, hashed_password) VALUES (?, ?, ?)"
        )
        try:
            self.cursor.execute(
                sql, (str(user_id), email, hashed_password)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error in DataBase.create_user: {e}")
            self.conn.rollback()
            return False
            
    def create_task(self, task_id: UUID, owner_id: UUID, title: str, description: Optional[str],
                    status: bool, created_at: datetime) -> bool:
        """ Создаём задачу """
        sql = (
            "INSERT INTO tasks (id, owner_id, title, description, status, created_at) VALUES (?, ?, ?, ?, ?, ?)"
        )
        try:
            self.cursor.execute(
                sql, (str(task_id), str(owner_id), title, description, int(status), created_at.isoformat())
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error in DataBase.create_task: {e}")
            self.conn.rollback()
            return False
        
    def get_tasks_by_owner(self, owner_id: UUID, sorting = "ASC") -> List[sqlite3.Row] | list:
        """ Получаем задачи пользователя """
        sql = "SELECT * FROM tasks WHERE owner_id = ? ORDER BY created_at {}".format(sorting)
        try:    
            self.cursor.execute(sql, (str(owner_id),))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error in DataBase.get_tasks_by_owner: {e}")
            return []

    def get_task_by_id(self, task_id: UUID) -> Optional[sqlite3.Row] | list:
        """ Получаем задачу по id """
        sql = (
            "SELECT * FROM tasks WHERE id = ?"
        )
        try:
            self.cursor.execute(sql, (str(task_id),))
            return self.cursor.fetchone()
        except Exception as e:
            print(f"Error in DataBase.get_task_by_id: {e}")
            return []

    def update_task(self, task_id: UUID, title: Optional[str], description: Optional[str], status: Optional[bool]) -> bool:
        """ Обновляем задачу """
        fields = []
        params = []
        if title is not None:
            fields.append("title = ?")
            params.append(title)
        if description is not None:
            fields.append("description = ?")
            params.append(description)
        if status is not None:
            fields.append("status = ?")
            params.append(int(status))
        params.append(str(task_id))
        sql = f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?"
        try:
            self.cursor.execute(sql, tuple(params))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error in DataBase.update_task: {e}")
            self.conn.rollback()
            return False
        
    def delete_task(self, task_id: UUID) -> bool:
        """ Удаляем задачу """
        sql = (
            "DELETE FROM tasks WHERE id = ?"
        )
        try:
            self.cursor.execute(sql, (str(task_id),))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error in DataBase.delete_task: {e}")
            self.conn.rollback()
            return False
        