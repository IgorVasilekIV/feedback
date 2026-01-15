import sqlite3

# Имя файла базы данных
DB_NAME = 'bot_database.db'

def init_db():
    """Создает таблицу, если её нет"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS banned_users (
                user_id INTEGER PRIMARY KEY
            )
        ''')
        conn.commit()

def add_ban(user_id: int):
    """Добавляет пользователя в бан"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # INSERT OR IGNORE, чтобы не было ошибки, если он уже там
        cursor.execute('INSERT OR IGNORE INTO banned_users (user_id) VALUES (?)', (user_id,))
        conn.commit()

def remove_ban(user_id: int):
    """Убирает пользователя из бана"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM banned_users WHERE user_id = ?', (user_id,))
        conn.commit()

def is_banned(user_id: int) -> bool:
    """Проверяет, забанен ли пользователь"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM banned_users WHERE user_id = ?', (user_id,))
        return cursor.fetchone() is not None
