import os
import sys
import json
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'contacts.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_contact(name, phone, email, message=""):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO contacts (name, phone, email, message) VALUES (?, ?, ?, ?)',
        (name.strip(), phone.strip(), email.strip(), message.strip())
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def get_all_contacts():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, phone, email, message, created_at FROM contacts ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            'id': r[0],
            'name': r[1],
            'phone': r[2],
            'email': r[3],
            'message': r[4],
            'created_at': r[5]
        }
        for r in rows
    ]

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'init'
    if cmd == 'init':
        init_db()
        print(json.dumps({'success': True, 'db': DB_PATH}))
    elif cmd == 'add':
        # payload passed via stdin
        raw = sys.stdin.read()
        data = json.loads(raw)
        row_id = add_contact(
            data.get('name', ''),
            data.get('number', '') or data.get('phone', ''),
            data.get('email', ''),
            data.get('message', '')
        )
        print(json.dumps({'success': True, 'id': row_id, 'message': 'Saved to contacts.db'}))
    elif cmd == 'get':
        print(json.dumps({'success': True, 'contacts': get_all_contacts()}))

