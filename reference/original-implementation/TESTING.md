# 🧪 Testing the Electron App

Here are the quickest ways to test your new Electron app:

## ⚡ Quick Tests (No Dependencies)

### 1. **Structure Validation** ✅
```bash
python validate-setup.py
```
**Status**: ✅ Already passed - all files are properly structured!

### 2. **Check Node.js Setup**
```bash
node --version && npm --version
```
**Status**: ✅ Node.js v22.15.0 and npm 10.9.2 detected

## 🔬 Component Testing

### Test 1: React Frontend Only
```bash
cd web
npm install    # Takes ~2-3 minutes first time
npm start      # Opens http://localhost:3000
```
**What you'll see**: React app loads but shows API connection errors (expected without backend)

### Test 2: Minimal API Server
Create a test API without full dependencies:
```bash
# Create simple test server
cat > simple_api.py << 'EOF'
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy"}).encode())
        elif self.path == '/api/workflows':
            self.send_response(200)
            self.send_header('Content-type', 'application/json') 
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {
                "config_workflows": {},
                "predefined_workflows": {
                    "test": {"name": "test", "description": "Test workflow"}
                }
            }
            self.wfile.write(json.dumps(response).encode())

if __name__ == '__main__':
    server = HTTPServer(('localhost', 8000), Handler)
    print("Test API running on http://localhost:8000")
    server.serve_forever()
EOF

# Run it
python simple_api.py
```

### Test 3: Full Frontend + API
With the simple API running:
```bash
# Terminal 1: simple_api.py (from above)
# Terminal 2:
cd web && npm start
```
**Result**: Working React app with basic API responses!

## 🚀 Full Testing (Requires Dependencies)

### Option A: Virtual Environment
```bash
python3 -m venv test_env
source test_env/bin/activate
pip install fastapi uvicorn sqlalchemy alembic pydantic
python run-dev.py
```

### Option B: System Install
```bash
sudo apt install python3-fastapi python3-uvicorn python3-sqlalchemy
python run-dev.py
```

### Option C: Docker (if available)
```bash
# Create Dockerfile for testing
cat > Dockerfile.test << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install fastapi uvicorn sqlalchemy alembic pydantic
RUN cd web && npm install && npm run build
EXPOSE 8000
CMD ["python", "run-dev.py"]
EOF

docker build -f Dockerfile.test -t curriculum-curator-test .
docker run -p 8000:8000 -p 3000:3000 curriculum-curator-test
```

## 🎯 Expected Test Results

### ✅ Working Components:
- **File Structure**: All files in correct places
- **React Build**: Compiles to static files
- **Electron Shell**: Can package and run
- **API Structure**: Endpoints defined correctly

### ⚠️ May Need Setup:
- **Python Dependencies**: FastAPI, uvicorn, etc.
- **Database**: SQLite creation on first run
- **Full Integration**: All components talking together

## 🔧 Troubleshooting

### React Won't Start
```bash
cd web
rm -rf node_modules package-lock.json
npm install
```

### Electron Won't Start
```bash
cd electron  
rm -rf node_modules package-lock.json
npm install
```

### Python Import Errors
```bash
# Use virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -e ".[web]"
```

### Port Conflicts
- React: http://localhost:3000
- API: http://localhost:8000
- Change ports in config if needed

## 🎉 Success Indicators

You'll know it's working when:

1. **React**: ✅ UI loads without errors
2. **API**: ✅ http://localhost:8000/health returns {"status": "healthy"}
3. **Integration**: ✅ Dashboard shows real data
4. **Electron**: ✅ Desktop app opens and functions

## 📱 Testing the Desktop App

Once everything works in browser:
```bash
cd electron
npm run electron-dev    # Development mode
npm run dist           # Build production app
```

The final test: **Double-click the built app and it should just work!**