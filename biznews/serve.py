#!/usr/bin/env python3
"""
Simple HTTP server to serve the BizNews static files
This solves CORS issues when opening HTML files directly
"""

import http.server
import os
import socketserver
import sys
import webbrowser
from pathlib import Path

# Get the directory where this script is located
DIR = Path(__file__).parent.absolute()
os.chdir(DIR)

PORT = 8080

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        
        # Deshabilitar caché COMPLETAMENTE para TODOS los archivos durante desarrollo
        # Esto evita tener que usar ?v=X.X en los scripts
        # Headers múltiples para máxima compatibilidad con todos los navegadores
        # Se aplica a todos los archivos: HTML, JS, CSS, imágenes, JSON, etc.
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate, max-age=0, private')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.send_header('X-Content-Type-Options', 'nosniff')
        
        super().end_headers()

    def do_OPTIONS(self):
        # Handle preflight requests
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        # List of public pages that should be in page/ folder
        public_pages = [
            'fuentes.html', 'categorias.html', 'busqueda.html',
            'contact.html', 'detalle_noticias.html', 'category.html'
        ]
        
        # Split path and query string to handle URLs with parameters
        path_parts = self.path.split('?', 1)
        path_only = path_parts[0]
        query_string = path_parts[1] if len(path_parts) > 1 else ''
        
        # If accessing root directory, serve index.html from root
        if path_only == '/' or path_only == '':
            if query_string:
                self.path = f'/index.html?{query_string}'
            else:
                self.path = '/index.html'
        # If accessing a public page directly (without /page/), redirect to page/ folder
        elif path_only.startswith('/') and not path_only.startswith('/page/') and not path_only.startswith('/admin/'):
            filename = path_only.lstrip('/')
            # Check if it's a public page
            if filename in public_pages:
                if query_string:
                    self.path = f'/page/{filename}?{query_string}'
                else:
                    self.path = f'/page/{filename}'
        
        # Call parent method to handle the request
        super().do_GET()

if __name__ == "__main__":
    try:
        with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
            print(f"🚀 Servidor HTTP iniciado en http://localhost:{PORT}")
            print(f"📁 Sirviendo archivos desde: {DIR}")
            print(f"🌐 Abre http://localhost:{PORT} en tu navegador")
            print("⏹️  Presiona Ctrl+C para detener el servidor")
            
            # Try to open browser automatically
            try:
                webbrowser.open(f'http://localhost:{PORT}')
            except:
                pass
                
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido")
        sys.exit(0)
    except OSError as e:
        if e.errno == 10048:  # Port already in use
            print(f"❌ Error: El puerto {PORT} ya está en uso")
            print("💡 Intenta cerrar otros servidores o cambiar el puerto")
        else:
            print(f"❌ Error: {e}")
        sys.exit(1)