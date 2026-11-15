import os
import sys
import json
import sqlite3
import mimetypes
from urllib.parse import urlparse, parse_qs
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'contacts.db')

def init_db():
    conn = sqlite3.connect(DB_FILE)
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
    print(f"[DB] Initialized SQLite database at: {DB_FILE}")

# Initialize on startup
init_db()

MIME_MAP = {
    '.html': 'text/html; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.webp': 'image/webp',
    '.svg': 'image/svg+xml',
    '.woff2': 'font/woff2',
    '.mp3': 'audio/mpeg',
    '.mp4': 'video/mp4',
    '.glb': 'model/gltf-binary',
}

class PortfolioHandler(BaseHTTPRequestHandler):
    def send_cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Range')

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors()
        self.end_headers()

    def do_HEAD(self):
        self.do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')

        if path == '/api/contact':
            content_length = int(self.headers.get('Content-Length', 0))
            raw_body = self.rfile.read(content_length).decode('utf-8', errors='replace')
            
            data = {}
            content_type = self.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                try:
                    data = json.loads(raw_body)
                except Exception:
                    data = {}
            else:
                parsed_form = parse_qs(raw_body)
                data = {k: v[0] for k, v in parsed_form.items()}

            name = (data.get('name') or '').strip()
            phone = (data.get('number') or data.get('phone') or '').strip()
            email = (data.get('email') or '').strip()
            message = (data.get('message') or '').strip()

            if not name or not phone or not email:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_cors()
                self.end_headers()
                res = {'success': False, 'error': 'Name, phone number, and email are required.'}
                self.wfile.write(json.dumps(res).encode('utf-8'))
                return

            try:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO contacts (name, phone, email, message) VALUES (?, ?, ?, ?)',
                    (name, phone, email, message)
                )
                conn.commit()
                row_id = cursor.lastrowid
                conn.close()

                print(f"[CONTACT SAVED] #{row_id}: {name} ({email}, {phone})")

                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_cors()
                self.end_headers()
                res = {
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
                }
                self.wfile.write(json.dumps(res).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_cors()
                self.end_headers()
                res = {'success': False, 'error': str(e)}
                self.wfile.write(json.dumps(res).encode('utf-8'))
            return

        self.send_response(404)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_cors()
        self.end_headers()
        self.wfile.write(json.dumps({'error': 'Not found'}).encode('utf-8'))

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # API: Return all contacts from database
        if path.rstrip('/') == '/api/contacts':
            try:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute('SELECT id, name, phone, email, message, created_at FROM contacts ORDER BY id DESC')
                rows = cursor.fetchall()
                conn.close()

                contacts = []
                for r in rows:
                    contacts.append({
                        'id': r[0],
                        'name': r[1],
                        'phone': r[2],
                        'email': r[3],
                        'message': r[4],
                        'created_at': r[5]
                    })

                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({'success': True, 'count': len(contacts), 'contacts': contacts}, indent=2).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode('utf-8'))
            return

        # API: Export CSV
        if path.rstrip('/') == '/api/contacts/export':
            try:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute('SELECT id, name, phone, email, message, created_at FROM contacts ORDER BY id ASC')
                rows = cursor.fetchall()
                conn.close()

                import csv
                import io
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(['ID', 'Name', 'Phone Number', 'Email Address', 'Message', 'Timestamp'])
                for r in rows:
                    writer.writerow(r)
                csv_data = output.getvalue().encode('utf-8')

                self.send_response(200)
                self.send_header('Content-Type', 'text/csv; charset=utf-8')
                self.send_header('Content-Disposition', 'attachment; filename="khush_contacts.csv"')
                self.send_cors()
                self.end_headers()
                self.wfile.write(csv_data)
            except Exception as e:
                self.send_response(500)
                self.send_cors()
                self.end_headers()
                self.wfile.write(str(e).encode('utf-8'))
            return

        # Static file resolution
        url_path = path.lstrip('/')
        if not url_path or url_path.endswith('/'):
            url_path += 'index.html'

        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.normpath(os.path.join(base_dir, url_path))

        # Check safety (prevent directory traversal)
        if not file_path.startswith(base_dir):
            self.send_error(403, "Forbidden")
            return

        # If path is directory, look for index.html
        if os.path.isdir(file_path):
            file_path = os.path.join(file_path, 'index.html')

        # If file not found, try appending .html
        if not os.path.exists(file_path) and os.path.exists(file_path + '.html'):
            file_path = file_path + '.html'

        if not os.path.isfile(file_path):
            self.send_error(404, "File Not Found")
            return

        # Serve static file with Range request support for audio/video
        _, ext = os.path.splitext(file_path)
        content_type = MIME_MAP.get(ext.lower(), mimetypes.guess_type(file_path)[0] or 'application/octet-stream')
        file_size = os.path.getsize(file_path)

        range_header = self.headers.get('Range')
        if range_header and ext.lower() in ('.mp4', '.mp3'):
            try:
                byte_range = range_header.strip().replace('bytes=', '')
                parts = byte_range.split('-')
                start = int(parts[0]) if parts[0] else 0
                end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1
                end = min(end, file_size - 1)
                chunk_length = end - start + 1

                self.send_response(206)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
                self.send_header('Content-Length', str(chunk_length))
                self.send_header('Accept-Ranges', 'bytes')
                self.send_cors()
                self.end_headers()

                with open(file_path, 'rb') as f:
                    f.seek(start)
                    bytes_remaining = chunk_length
                    while bytes_remaining > 0:
                        chunk = f.read(min(bytes_remaining, 65536))
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        bytes_remaining -= len(chunk)
                return
            except Exception:
                pass

        # Standard file send
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(file_size))
        self.send_header('Accept-Ranges', 'bytes')
        self.send_cors()
        self.end_headers()

        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                self.wfile.write(chunk)

def run(start_port=8080):
    port = start_port
    while port < start_port + 20:
        try:
            server = ThreadingHTTPServer(('0.0.0.0', port), PortfolioHandler)
            print("=" * 60)
            print(f"🎮 Khush Salecha's Game Boy Portfolio (Python + SQLite) is LIVE!")
            print(f"👉 Website URL:       http://localhost:{port}")
            print(f"👉 Contact Form:      http://localhost:{port}/about/#contact-form")
            print(f"👉 Database Viewer:   http://localhost:{port}/database/")
            print(f"👉 SQLite Database:   {DB_FILE}")
            print("=" * 60)
            server.serve_forever()
            break
        except OSError as e:
            if getattr(e, 'winerror', None) == 10048 or getattr(e, 'errno', None) == 48:
                print(f"[Port {port} in use, trying {port + 1}...]")
                port += 1
            else:
                raise e

if __name__ == '__main__':
    port_arg = int(os.environ.get('PORT', 8080))
    if len(sys.argv) > 1:
        try:
            port_arg = int(sys.argv[1])
        except ValueError:
            pass
    run(port_arg)
