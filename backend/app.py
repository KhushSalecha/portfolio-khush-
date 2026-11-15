import os
import sqlite3
import csv
import io
from flask import Flask, request, jsonify, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Use directory of app or persistent path for SQLite database
# On Vercel serverless / ephemeral containers, /tmp is writable
DB_PATH = os.environ.get('DATABASE_PATH')
if not DB_PATH:
    if os.environ.get('VERCEL'):
        DB_PATH = '/tmp/contacts.db'
        seed_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'contacts.db')
        if os.path.exists(seed_path) and not os.path.exists(DB_PATH):
            try:
                import shutil
                shutil.copyfile(seed_path, DB_PATH)
            except Exception:
                pass
    else:
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

# Initialize DB safely on start
try:
    init_db()
except Exception as e:
    print(f"Warning: initial DB creation deferred: {e}")

@app.route('/health', methods=['GET'])
@app.route('/', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'backend',
        'framework': 'flask',
        'db': DB_PATH
    })

@app.route('/api/contact', methods=['POST'])
@app.route('/contact', methods=['POST'])
def save_contact():
    data = request.get_json(silent=True) or request.form.to_dict()
    if not data:
        return jsonify({'success': False, 'error': 'No input data provided'}), 400

    name = (data.get('name') or '').strip()
    phone = (data.get('number') or data.get('phone') or '').strip()
    email = (data.get('email') or '').strip()
    message = (data.get('message') or '').strip()

    if not name or not phone or not email:
        return jsonify({'success': False, 'error': 'Name, phone number, and email are required.'}), 400

    try:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO contacts (name, phone, email, message) VALUES (?, ?, ?, ?)',
            (name, phone, email, message)
        )
        conn.commit()
        row_id = cursor.lastrowid
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Your contact details have been successfully saved to Khush’s database!',
            'id': row_id,
            'contact': {
                'id': row_id,
                'name': name,
                'phone': phone,
                'email': email,
                'message': message
            }
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/contacts', methods=['GET'])
@app.route('/contacts', methods=['GET'])
def get_contacts():
    try:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, phone, email, message, created_at FROM contacts ORDER BY id DESC')
        rows = cursor.fetchall()
        conn.close()

        contacts = [
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
        return jsonify({'success': True, 'count': len(contacts), 'contacts': contacts}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/contacts/export', methods=['GET'])
@app.route('/contacts/export', methods=['GET'])
def export_contacts():
    try:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, phone, email, message, created_at FROM contacts ORDER BY id ASC')
        rows = cursor.fetchall()
        conn.close()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Name', 'Phone Number', 'Email Address', 'Message', 'Timestamp'])
        for r in rows:
            writer.writerow(r)

        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=khush_contacts.csv"}
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

