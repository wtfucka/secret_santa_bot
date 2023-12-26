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
    gift_reciever_chat_id INTEGER,
    gift_reciever_full_name TEXT,
    gift_reciever_address TEXT,
    gift_reciever_phone_number TEXT,
    gift_reciever_other_info TEXT
);
''')
