#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import http.server, socketserver, socket, os, zipfile, signal, http.client, json
import argparse
from textwrap import dedent
from typing import Optional
from pathlib import Path

# ========= CONFIG =========
# Valores por defecto (pueden sobreescribirse por CLI o variables de entorno)
ESP32_HOST  = os.environ.get("ESP32_HOST", "10.224.113.103")   # <-- PON AQUÍ la IP REAL del ESP32 (monitor serie)
ESP32_PORT  = int(os.environ.get("ESP32_PORT", "80"))
PUERTO_BASE = int(os.environ.get("SERVIDOR_PUERTO", "8080"))  # <-- Tu servidor local (Windows / VM)
SERVIDOR_BIND = os.environ.get("SERVIDOR_BIND", "0.0.0.0")    # Escuchar en todas las interfaces por defecto
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

def resolve_web_dir(arg_dir: Optional[str]) -> Path:
    if arg_dir:
        manual = Path(arg_dir).expanduser().resolve()
        if manual.is_dir():
            return manual
        raise SystemExit(f"[ERROR] La ruta indicada en --web-dir no existe: {manual}")
    return auto_web_dir()

def print_help_banner(listen_host: str, listen_port: int, esp32_host: str, esp32_port: int, web_dir: Path):
    primary_host = "localhost" if listen_host in {"0.0.0.0", "127.0.0.1"} else listen_host
    ip_visibles = sorted({listen_host, IP_SERVIDOR, "127.0.0.1", primary_host})
    print("=" * 72)
    print(" Proxy local listo ")
    print("=" * 72)
    print(f"- Sitio web:   http://{primary_host}:{listen_port}")
    for ip in ip_visibles:
        if ip in ("0.0.0.0", "127.0.0.1"):
            continue
        print(f"               http://{ip}:{listen_port}")
    print(f"- Archivos:    {web_dir}")
    print(f"- API bridge:  http://{esp32_host}:{esp32_port}/api/*")
    print("- Para detener presiona CTRL+C")
    print("=" * 72)

def get_lan_ip(default="127.0.0.1"):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return default

def parse_args():
    parser = argparse.ArgumentParser(
        description="Proxy HTTP + servidor de archivos estáticos para el proyecto ESP32.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent(
            """Ejemplos:
              python servidor_final.py --esp32 192.168.1.120 --port 8081
              ESP32_HOST=192.168.1.120 python servidor_final.py
            """
        ),
    )
    parser.add_argument("--esp32", dest="esp32_host", default=ESP32_HOST, help="IP o hostname del ESP32")
    parser.add_argument("--esp32-port", dest="esp32_port", type=int, default=ESP32_PORT, help="Puerto HTTP del ESP32")
    parser.add_argument("--port", dest="listen_port", type=int, default=PUERTO_BASE, help="Puerto público para el proxy")
    parser.add_argument("--bind", dest="listen_host", default=SERVIDOR_BIND, help="Dirección de escucha (0.0.0.0 por defecto)")
    parser.add_argument("--web-dir", dest="web_dir", default=None, help="Ruta manual a la carpeta dist a servir")
    return parser.parse_args()

IP_SERVIDOR = get_lan_ip()

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    esp32_host = ESP32_HOST
    esp32_port = ESP32_PORT

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
            target_host = getattr(self, "esp32_host", ESP32_HOST)
            target_port = getattr(self, "esp32_port", ESP32_PORT)
            conn = http.client.HTTPConnection(target_host, target_port, timeout=5)
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
    args = parse_args()
    web_dir = resolve_web_dir(args.web_dir)
    os.chdir(str(web_dir))

    port = pick_free_port(args.listen_host, args.listen_port, 1)

    # Actualizamos valores utilizados por el handler
    ProxyHandler.esp32_host = args.esp32_host
    ProxyHandler.esp32_port = args.esp32_port

    httpd = ThreadedHTTPServer((args.listen_host, port), ProxyHandler)

    print_help_banner(args.listen_host, port, args.esp32_host, args.esp32_port, web_dir)

    def _stop(sig, frm):
        print("\n[INFO] Deteniendo…")
        httpd.shutdown()
    signal.signal(signal.SIGINT,  _stop)
    signal.signal(signal.SIGTERM, _stop)

    httpd.serve_forever()

if __name__=="__main__":
    run()
