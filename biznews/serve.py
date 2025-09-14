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
        super().end_headers()

    def do_OPTIONS(self):
        # Handle preflight requests
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        # If accessing root directory, redirect to index.html
        if self.path == '/' or self.path == '':
            self.path = '/index.html'
        
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
