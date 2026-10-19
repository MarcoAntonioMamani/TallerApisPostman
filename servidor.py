"""Servidor local del taller.

Igual que `python -m http.server`, pero le indica al navegador que no guarde
copias en caché: así, al editar un .html, siempre se ve la última versión.

Uso (desde esta carpeta):  python servidor.py          -> http://127.0.0.1:8765/
                           python servidor.py 9000     -> otro puerto
"""
import functools
import http.server
import os
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
ROOT = os.path.dirname(os.path.abspath(__file__))


class SinCache(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()


if __name__ == "__main__":
    handler = functools.partial(SinCache, directory=ROOT)
    with http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler) as srv:
        print(f"Taller disponible en http://127.0.0.1:{PORT}/index.html  (Ctrl+C para detener)")
        srv.serve_forever()
