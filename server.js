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

const server = http.createServer((req, res) => {
  const parsedUrl = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  const pathname = parsedUrl.pathname.replace(/\/+$/, '') || '/';

  // API Endpoints backed by Python SQLite database
  if (req.method === 'POST' && pathname === '/api/contact') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
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
    const py = spawn('py', ['db_helper.py', 'get'], { cwd: __dirname });
    let out = '';
    py.stdout.on('data', chunk => { out += chunk; });
    py.on('close', code => {
      res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8', 'Access-Control-Allow-Origin': '*' });
      res.end(out || JSON.stringify({ success: true, contacts: [] }));
    });
    return;
  }

  // Static file resolution
  let urlPath = decodeURI(pathname);
  if (urlPath === '/' || urlPath.endsWith('/')) urlPath += 'index.html';

  let filePath = path.join(__dirname, urlPath);

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
});

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

startServer(port);
