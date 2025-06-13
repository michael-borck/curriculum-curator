#!/usr/bin/env python3
"""Simple demo server - no dependencies except standard library."""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import uuid
from datetime import datetime

# In-memory storage
sessions = {}

class DemoHandler(BaseHTTPRequestHandler):
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
            response = {
                "status": "healthy", 
                "message": "Curriculum Curator API is running"
            }
        
        elif self.path == '/api/workflows':
            response = {
                "config_workflows": {
                    "minimal_module": {
                        "name": "minimal_module",
                        "description": "Create a minimal course module with outline and assessment"
                    },
                    "full_course": {
                        "name": "full_course",
                        "description": "Generate complete course materials"
                    }
                },
                "predefined_workflows": {
                    "lecture_content": {
                        "name": "lecture_content",
                        "description": "Generate lecture content from outline"
                    },
                    "assessment_builder": {
                        "name": "assessment_builder",
                        "description": "Create assessments and quizzes"
                    }
                }
            }
        
        elif self.path == '/api/workflows/sessions':
            response = list(sessions.values())
        
        elif self.path.startswith('/api/workflows/sessions/'):
            session_id = self.path.split('/')[-1]
            if session_id in sessions:
                response = sessions[session_id]
            else:
                self.send_response(404)
                response = {"error": "Session not found"}
        
        elif self.path == '/api/prompts':
            response = {
                "prompts": [
                    "assessment/questions.txt",
                    "course/overview.txt", 
                    "module/outline.txt",
                    "lecture/content.txt"
                ]
            }
        
        elif self.path == '/api/validators':
            response = {
                "quality": [
                    {"name": "readability", "implemented": True, "category": "quality"},
                    {"name": "structure", "implemented": True, "category": "quality"}
                ],
                "language": [
                    {"name": "language_detector", "implemented": True, "category": "language"}
                ]
            }
        
        elif self.path == '/api/remediators':
            response = {
                "autofix": [
                    {"name": "format_corrector", "implemented": True, "category": "autofix"}
                ],
                "language": [
                    {"name": "translator", "implemented": False, "category": "language"}
                ]
            }
        
        self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        if self.path == '/api/workflows/run':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            session_id = str(uuid.uuid4())
            sessions[session_id] = {
                "session_id": session_id,
                "workflow_name": request_data.get('workflow', 'unknown'),
                "status": "completed",
                "variables": request_data.get('variables', {}),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "result": {
                    "results": {
                        "output_files": {
                            "markdown": f"/tmp/output_{session_id}.md",
                            "pdf": f"/tmp/output_{session_id}.pdf"
                        }
                    },
                    "context": {
                        "final_usage_report": {
                            "by_model": {
                                "gpt-3.5-turbo": {
                                    "count": 5,
                                    "input_tokens": 1234,
                                    "output_tokens": 5678,
                                    "cost": 0.0234
                                }
                            },
                            "totals": {
                                "count": 5,
                                "input_tokens": 1234,
                                "output_tokens": 5678,
                                "cost": 0.0234
                            }
                        }
                    }
                }
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                "session_id": session_id,
                "status": "completed",
                "message": f"Demo workflow '{request_data.get('workflow')}' completed successfully!"
            }
            self.wfile.write(json.dumps(response).encode())
    
    def log_message(self, format, *args):
        # Suppress logs for cleaner output
        pass

if __name__ == '__main__':
    port = 8100
    print(f"🚀 Starting Curriculum Curator Demo Server")
    print(f"📍 API: http://localhost:{port}")
    print(f"🌐 Health check: http://localhost:{port}/health")
    print(f"\n✨ Ready for demo! Start React with: cd web && npm start")
    print(f"   Then visit: http://localhost:3001")
    print(f"\nPress Ctrl+C to stop")
    
    server = HTTPServer(('localhost', port), DemoHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Demo server stopped")
