const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const mimeTypes = {
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
  '.glb': 'model/gltf-binary'
};

const serverHandler = async (req, res) => {
  const parsedUrl = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  const pathname = parsedUrl.pathname.replace(/\/+$/, '') || '/';

  // API Endpoints backed by Python SQLite database
  if (req.method === 'POST' && pathname === '/api/contact') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', async () => {
      // 1. Check for bound Vercel Service URL (BACKEND_URL)
      const backendBase = process.env.BACKEND_URL;
      if (backendBase) {
        try {
          const targetUrl = new URL('/api/contact', backendBase);
          const response = await fetch(targetUrl, {
            method: 'POST',
            headers: {
              'Content-Type': req.headers['content-type'] || 'application/json'
            },
            body: body
          });
          const text = await response.text();
          res.writeHead(response.status, {
            'Content-Type': response.headers.get('content-type') || 'application/json',
            'Access-Control-Allow-Origin': '*'
          });
          res.end(text);
          return;
        } catch (err) {
          console.error('[Service Binding] Failed to call BACKEND_URL:', err.message);
        }
      }

      // 2. Local fallback using db_helper.py
      let data = {};
      const ct = req.headers['content-type'] || '';
      if (ct.includes('application/json')) {
        try { data = JSON.parse(body); } catch(e) {}
      } else {
        const params = new URLSearchParams(body);
        for (const [k, v] of params.entries()) data[k] = v;
      }

      if (!data.name || (!data.number && !data.phone) || !data.email) {
        res.writeHead(400, { 'Content-Type': 'application/json; charset=utf-8', 'Access-Control-Allow-Origin': '*' });
        res.end(JSON.stringify({ success: false, error: 'Name, phone number, and email are required.' }));
        return;
      }

      const py = spawn('py', ['db_helper.py', 'add'], { cwd: __dirname });
      let out = '';
      let err = '';
      py.stdout.on('data', chunk => { out += chunk; });
      py.stderr.on('data', chunk => { err += chunk; });
      py.on('close', code => {
        if (code === 0 && out) {
          res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8', 'Access-Control-Allow-Origin': '*' });
          res.end(out);
        } else {
          res.writeHead(500, { 'Content-Type': 'application/json; charset=utf-8', 'Access-Control-Allow-Origin': '*' });
          res.end(JSON.stringify({ success: false, error: err || 'Database execution failed' }));
        }
      });
      py.stdin.write(JSON.stringify(data));
      py.stdin.end();
    });
    return;
  }

  if (req.method === 'GET' && pathname === '/api/contacts') {
    // 1. Check for bound Vercel Service URL (BACKEND_URL)
    const backendBase = process.env.BACKEND_URL;
    if (backendBase) {
      try {
        const targetUrl = new URL('/api/contacts', backendBase);
        const response = await fetch(targetUrl);
        const text = await response.text();
        res.writeHead(response.status, {
          'Content-Type': response.headers.get('content-type') || 'application/json',
          'Access-Control-Allow-Origin': '*'
        });
        res.end(text);
        return;
      } catch (err) {
        console.error('[Service Binding] Failed to call BACKEND_URL:', err.message);
      }
    }

    // 2. Local fallback using db_helper.py
    const py = spawn('py', ['db_helper.py', 'get'], { cwd: __dirname });
    let out = '';
    py.stdout.on('data', chunk => { out += chunk; });
    py.on('close', code => {
      res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8', 'Access-Control-Allow-Origin': '*' });
      res.end(out || JSON.stringify({ success: true, contacts: [] }));
    });
    return;
  }

  if (req.method === 'GET' && pathname === '/api/contacts/export') {
    const backendBase = process.env.BACKEND_URL;
    if (backendBase) {
      try {
        const targetUrl = new URL('/api/contacts/export', backendBase);
        const response = await fetch(targetUrl);
        const text = await response.text();
        res.writeHead(response.status, {
          'Content-Type': 'text/csv; charset=utf-8',
          'Content-Disposition': 'attachment; filename="khush_contacts.csv"',
          'Access-Control-Allow-Origin': '*'
        });
        res.end(text);
        return;
      } catch (err) {
        console.error('[Service Binding] Failed to call BACKEND_URL:', err.message);
      }
    }
  }

  // Static file resolution
  const ROOT_DIR = path.join(__dirname, '..');
  let urlPath = decodeURI(pathname);
  if (urlPath === '/' || urlPath.endsWith('/')) urlPath += 'index.html';

  let filePath = path.join(ROOT_DIR, urlPath);

  if (fs.existsSync(filePath) && fs.statSync(filePath).isDirectory()) {
    filePath = path.join(filePath, 'index.html');
  }

  if (!fs.existsSync(filePath) && fs.existsSync(filePath + '.html')) {
    filePath = filePath + '.html';
  }

  if (!fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
    res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('404 Not Found');
    return;
  }

  const stat = fs.statSync(filePath);
  const ext = path.extname(filePath).toLowerCase();
  const contentType = mimeTypes[ext] || 'application/octet-stream';

  const range = req.headers.range;
  if (range && (ext === '.mp4' || ext === '.mp3')) {
    const parts = range.replace(/bytes=/, "").split("-");
    const start = parseInt(parts[0], 10);
    const end = parts[1] ? parseInt(parts[1], 10) : stat.size - 1;
    const chunksize = (end - start) + 1;
    const stream = fs.createReadStream(filePath, { start, end });

    res.writeHead(206, {
      'Content-Range': `bytes ${start}-${end}/${stat.size}`,
      'Accept-Ranges': 'bytes',
      'Content-Length': chunksize,
      'Content-Type': contentType,
      'Access-Control-Allow-Origin': '*'
    });
    stream.pipe(res);
    return;
  }

  res.writeHead(200, {
    'Content-Length': stat.size,
    'Content-Type': contentType,
    'Accept-Ranges': 'bytes',
    'Access-Control-Allow-Origin': '*'
  });
  fs.createReadStream(filePath).pipe(res);
};

const server = http.createServer(serverHandler);

let port = parseInt(process.env.PORT || 8080, 10);

function startServer(p) {
  server.listen(p, () => {
    console.log(`\n======================================================`);
    console.log(`🎮 Khush Salecha's Game Boy Portfolio is LIVE!`);
    console.log(`👉 Open http://localhost:${p} in your web browser`);
    console.log(`👉 Contact Form: http://localhost:${p}/about/#contact-me`);
    console.log(`👉 Database Viewer: http://localhost:${p}/database/`);
    console.log(`======================================================\n`);
  });
}

server.on('error', err => {
  if (err.code === 'EADDRINUSE') {
    console.warn(`Port ${port} is in use, trying port ${port + 1}...`);
    port++;
    startServer(port);
  } else {
    console.error('Server error:', err);
  }
});

// Start listener when executed directly or when PORT is provided
if (process.env.PORT || require.main === module || !process.env.VERCEL) {
  startServer(port);
}

function handler(req, res) {
  return serverHandler(req, res);
}
handler.server = server;

module.exports = handler;
module.exports.default = handler;
