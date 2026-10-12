import os, http.server, subprocess, json, sys, pathlib, urllib.parse

ROOT = pathlib.Path(__file__).parent
ESBUILD = '/opt/npm-tools/node_modules/.bin/esbuild'
SKELETON = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top);padding-bottom:env(safe-area-inset-bottom)}body{margin:0;font:14px system-ui;background:#fafafa}img{max-width:100%}[hidden]{display:none!important}</style></head><body>"""


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body, ctype):
        b = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        p = urllib.parse.urlparse(self.path).path
        if p in ('/', '/index.html'):
            html = pathlib.Path(os.environ.get('DIST_HTML', str(ROOT.parent / 'dist' / 'index.html'))).read_text()
            return self.send(200, SKELETON + html + '</body></html>', 'text/html')
        return self.send(404, 'nf', 'text/plain')

    def do_POST(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        n = int(self.headers['Content-Length'])
        src = self.rfile.read(n).decode()
        fname = q.get('f', ['x.jsx'])[0]
        loader = 'tsx' if fname.endswith('.tsx') else 'ts' if fname.endswith('.ts') else 'jsx'
        r = subprocess.run([ESBUILD, '--loader=' + loader, '--format=cjs', '--jsx=transform', '--sourcefile=' + fname, '--log-level=error'],
                           input=src, capture_output=True, text=True)
        if r.returncode != 0:
            return self.send(400, r.stderr, 'text/plain')
        return self.send(200, r.stdout, 'text/javascript')


if __name__ == '__main__':
    http.server.ThreadingHTTPServer(('127.0.0.1', int(sys.argv[1])), H).serve_forever()
