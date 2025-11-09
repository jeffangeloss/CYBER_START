#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import http.server, socketserver, socket, threading, os, zipfile, signal, http.client, json
from pathlib import Path

# ========= CONFIG =========
ESP32_HOST  = "10.224.113.103"   # <-- PON AQUÍ la IP REAL del ESP32 (monitor serie)
ESP32_PORT  = 80
PUERTO_BASE = 8080               # <-- Tu servidor local (Windows / VM)
# ==========================

BASE_DIR = Path(__file__).parent.resolve()
ZIP_PATH = BASE_DIR / "PaginaSemaforos.zip"

# Intentamos detectar automáticamente la carpeta 'dist' del front:
def auto_web_dir() -> Path:
    # Prioridades comunes:
    #   /PaginaSemaforos/PaginaSemaforos/dist
    #   /PaginaSemaforos/dist
    #   /dist
    candidatos = [
        BASE_DIR / "PaginaSemaforos" / "PaginaSemaforos" / "dist",
        BASE_DIR / "PaginaSemaforos" / "dist",
        BASE_DIR / "dist",
    ]
    for p in candidatos:
        if (p/"index.html").is_file() or (p/"index.htm").is_file():
            return p

    # Si hay un zip con el proyecto, lo extraemos
    if ZIP_PATH.is_file():
        try:
            with zipfile.ZipFile(ZIP_PATH, 'r') as z:
                z.extractall(BASE_DIR)
        except Exception as e:
            print(f"[WARN] No se pudo descomprimir {ZIP_PATH}: {e}")

    # Búsqueda superficial de 'dist' con index.html (3 niveles)
    for root, dirs, files in os.walk(BASE_DIR):
        if len(Path(root).relative_to(BASE_DIR).parts) > 3:
            continue
        low = {f.lower() for f in files}
        if "index.html" in low or "index.htm" in low:
            # preferimos 'dist' si aparece en la ruta
            if "dist" in Path(root).parts:
                return Path(root)

    # Último recurso: servir BASE_DIR (mostrará listing si no hay index)
    return BASE_DIR

WEB_DIR = auto_web_dir()

def get_lan_ip(default="127.0.0.1"):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return default

IP_SERVIDOR = get_lan_ip()

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    # CORS abierto para que el front pueda llamar /api desde el mismo host:puerto
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        if self.path.startswith("/api/"):
            self.send_response(204)
            self.end_headers()
            return
        return super().do_OPTIONS()

    def proxy_to_esp32(self, method="GET", body=None):
        # Reenvía /api/* al ESP32 (mismo path y query)
        try:
            conn = http.client.HTTPConnection(ESP32_HOST, ESP32_PORT, timeout=5)
            headers = {}
            conn.request(method, self.path, body=body, headers=headers)
            resp = conn.getresponse()
            data = resp.read()
            ctype = resp.getheader("Content-Type") or "application/json"
            self.send_response(resp.status)
            self.send_header("Content-Type", ctype)
            self.end_headers()
            self.wfile.write(data)
            conn.close()
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            msg = json.dumps({"error":"Bad Gateway","detail":str(e)}).encode()
            self.wfile.write(msg)

    def do_GET(self):
        if self.path.startswith("/api/"):
            return self.proxy_to_esp32("GET")
        return super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/"):
            l = int(self.headers.get("Content-Length","0") or "0")
            body = self.rfile.read(l) if l>0 else None
            return self.proxy_to_esp32("POST", body)
        return super().do_POST()

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    allow_reuse_address = True

def pick_free_port(ip, start, tries=1):
    # Fijamos 8080; si está ocupado y tries>1, podrías probar 8081+, pero lo dejamos fijo.
    return start

def run():
    os.chdir(str(WEB_DIR))
    port = pick_free_port(IP_SERVIDOR, PUERTO_BASE, 1)
    httpd = ThreadedHTTPServer((IP_SERVIDOR, port), ProxyHandler)

    print(f"[HTTP] Sirviendo {WEB_DIR} en http://{IP_SERVIDOR}:{port}")
    print(f"[API ] Proxy → http://{ESP32_HOST}:{ESP32_PORT}/api/*")

    def _stop(sig, frm):
        print("\n[INFO] Deteniendo…")
        httpd.shutdown()
    signal.signal(signal.SIGINT,  _stop)
    signal.signal(signal.SIGTERM, _stop)

    httpd.serve_forever()

if __name__=="__main__":
    run()