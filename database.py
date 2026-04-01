import sqlite3

DB_NAME = 'bot_database.db'

def get_db_conn():
    return sqlite3.connect(DB_NAME)


def init_db():
    """Создает таблицу, если её нет"""
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS banned_users (
                user_id INTEGER PRIMARY KEY
            )
        ''')
        conn.commit()

def add_ban(user_id: int):
    """Добавляет пользователя в бан"""
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO banned_users (user_id) VALUES (?)', (user_id,))
        conn.commit()

def remove_ban(user_id: int):
    """Убирает пользователя из бана"""
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM banned_users WHERE user_id = ?', (user_id,))
        conn.commit()

def is_banned(user_id: int) -> bool:
    """Проверяет, забанен ли пользователь"""
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM banned_users WHERE user_id = ?', (user_id,))
        return cursor.fetchone() is not None

def get_total_users() -> int:
    """Возвращает общее количество пользователей в бане"""
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM banned_users')
        return cursor.fetchone()[0]

def get_banned():
    """Возвращает айди пользователей в бане"""
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM banned_users")
        result = [row[0] for row in cursor.fetchall()]
        return result