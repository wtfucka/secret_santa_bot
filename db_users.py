"""
Создание БД на sqlite.
"""
import sqlite3

with sqlite3.connect('secret_santa.db') as connection:
    cursor = connection.cursor()
    cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    address TEXT NOT NULL,
    phone_number TEXT NOT NULL,
    other_info TEXT,
    gift_reciever_id INTEGER
);
''')
