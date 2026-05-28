#!/usr/bin/env python3
"""Servidor HTTP para servir arquivos estáticos do diretório dist e proxy para backend em /api/* e /internal/*"""
import http.server
import socketserver
import os
from urllib.parse import urlparse, urljoin
import urllib.request
import json

DIST_DIR = os.path.join(os.path.dirname(__file__), 'dist')
BACKEND_URL = 'http://127.0.0.1:8080'

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        """_summary_: traduz o caminho para servir arquivos estáticos do diretório dist, ou proxy para backend se for /api/* ou /internal/*

        Args:
            path (_type_): _description_: caminho da requisição

        Returns:
            _type_: _description_: caminho do arquivo a ser servido ou None se for proxy
        """
        if path == '/':
            path = '/index.html'
        return os.path.join(DIST_DIR, path.lstrip('/'))

    def do_GET(self):
        """_summary_: método para lidar com requisições GET, serve arquivos estáticos ou proxy para backend se for /api/* ou /internal/*
        """
        if self.path.startswith('/api/') or self.path.startswith('/internal/'):
            self.proxy_request()
        else:
            super().do_GET()

    def do_POST(self):
        """_summary_: método para lidar com requisições POST, serve arquivos estáticos ou proxy para backend se for /api/* ou /internal/*
        """
        if self.path.startswith('/api/') or self.path.startswith('/internal/'):
            self.proxy_request()
        else:
            super().do_POST()

    def proxy_request(self):
        """_summary_: método para encaminhar requisições para o backend
        """
        target_url = urljoin(BACKEND_URL, self.path)
        
        try:
            if self.command == 'GET':
                req = urllib.request.Request(target_url)
            else:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length) if content_length > 0 else b''
                req = urllib.request.Request(target_url, data=body)
                req.add_header('Content-Type', self.headers.get('Content-Type', 'application/json'))
            
            req.add_header('User-Agent', self.headers.get('User-Agent', 'Python-Proxy'))
            
            with urllib.request.urlopen(req, timeout=10) as response:
                status = response.status
                headers = dict(response.headers)
                body = response.read()
            
            self.send_response(status)
            for key, value in headers.items():
                if key.lower() not in ['transfer-encoding', 'content-encoding']:
                    self.send_header(key, value)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(502)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': f'Proxy error: {str(e)}',
                'target': target_url
            }).encode())

    def do_OPTIONS(self):
        """_summary_: método para lidar com requisições OPTIONS, necessário para CORS
        """
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

if __name__ == '__main__':
    PORT = 5000
    Handler = ProxyHandler
    
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        print(f"Serving {DIST_DIR} at http://127.0.0.1:{PORT}/")
        print(f"Proxying /api/* to {BACKEND_URL}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutdown.")
