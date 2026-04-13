import sqlite3

DB_NAME = 'bot_database.db'

def get_db_conn():
    return sqlite3.connect(DB_NAME)


def init_db():
    """Создает таблицы, если их нет"""
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS banned_users (
                user_id INTEGER PRIMARY KEY
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS spec_permissions (
                user_id INTEGER PRIMARY KEY,
                ban INTEGER DEFAULT 0,
                unban INTEGER DEFAULT 0,
                answer INTEGER DEFAULT 0
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



def get_default_spec_permissions():
    """Возвращает базовые настройки прав для SPEC"""
    return {'ban': False, 'unban': False, 'answer': False}

def get_spec_permissions(user_id: int):
    """Возвращает права SPEC пользователя. Если нет записи - возвращает базовые"""
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT ban, unban, answer FROM spec_permissions WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        if result:
            return {'ban': bool(result[0]), 'unban': bool(result[1]), 'answer': bool(result[2])}
        return get_default_spec_permissions()

def update_spec_permission(user_id: int, permission: str, value: bool):
    """Обновляет конкретное право для SPEC пользователя"""
    if permission not in ['ban', 'unban', 'answer']:
        raise ValueError(f"Неизвестное право: {permission}")
    
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM spec_permissions WHERE user_id = ?', (user_id,))
        if cursor.fetchone():
            cursor.execute(f'UPDATE spec_permissions SET {permission} = ? WHERE user_id = ?', (int(value), user_id))
        else:
            permissions = get_default_spec_permissions()
            permissions[permission] = value
            cursor.execute(
                'INSERT INTO spec_permissions (user_id, ban, unban, answer) VALUES (?, ?, ?, ?)',
                (user_id, int(permissions['ban']), int(permissions['unban']), int(permissions['answer']))
            )
        conn.commit()

def get_all_specs():
    """Возвращает список всех SPEC пользователей с их правами"""
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, ban, unban, answer FROM spec_permissions")
        return [{'user_id': row[0], 'ban': bool(row[1]), 'unban': bool(row[2]), 'answer': bool(row[3])} for row in cursor.fetchall()]

def addspec(user_id: int):
    """Добавляет пользователя в список SPEC с базовыми правами"""
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO spec_permissions (user_id, ban, unban, answer) VALUES (?, 0, 0, 0)', (user_id,))
        conn.commit()