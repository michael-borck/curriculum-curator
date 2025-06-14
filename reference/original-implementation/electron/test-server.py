#!/usr/bin/env python3
"""Mock server for testing Electron app without dependencies."""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import sys

class MockAPIHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {}
        if self.path == '/health':
            response = {"status": "healthy", "message": "Curriculum Curator API is running"}
        elif self.path == '/api/workflows':
            response = {
                "config_workflows": {},
                "predefined_workflows": {
                    "test_workflow": {
                        "name": "test_workflow",
                        "description": "A test workflow for demonstration"
                    }
                }
            }
        elif self.path == '/api/workflows/sessions':
            response = []
        elif self.path == '/api/validators':
            response = {"quality": [{"name": "readability", "implemented": True, "category": "quality"}]}
        elif self.path == '/api/remediators':
            response = {"autofix": [{"name": "format_corrector", "implemented": True, "category": "autofix"}]}
        elif self.path == '/api/prompts':
            response = {"prompts": ["test/prompt.txt"]}
            
        self.wfile.write(json.dumps(response).encode())
    
    def log_message(self, format, *args):
        # Suppress request logs for cleaner output
        pass

if __name__ == '__main__':
    print("Starting mock API server on http://127.0.0.1:8000", flush=True)
    server = HTTPServer(('127.0.0.1', 8000), MockAPIHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down mock server", flush=True)
        sys.exit(0)