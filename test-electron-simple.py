#!/usr/bin/env python3
"""
Simple Electron app test that focuses on what can be tested without dependencies.
"""

import subprocess
import sys
from pathlib import Path

def test_react_setup():
    """Test if we can set up and build the React app."""
    print("⚛️  Testing React setup...")
    
    web_dir = Path("web")
    if not web_dir.exists():
        print("❌ Web directory not found")
        return False
    
    try:
        # Install React dependencies
        print("📦 Installing React dependencies...")
        result = subprocess.run(['npm', 'install'], cwd=web_dir, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ npm install failed: {result.stderr}")
            return False
        print("✅ React dependencies installed")
        
        # Test React build
        print("🔨 Testing React build...")
        result = subprocess.run(['npm', 'run', 'build'], cwd=web_dir, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ React build failed: {result.stderr}")
            return False
        print("✅ React build successful")
        
        # Check if build directory was created
        build_dir = web_dir / "build"
        if build_dir.exists():
            print("✅ React build output found")
            return True
        else:
            print("❌ React build directory not created")
            return False
        
    except Exception as e:
        print(f"❌ Error during React setup: {e}")
        return False

def test_electron_setup():
    """Test if we can set up Electron."""
    print("\n🖥️  Testing Electron setup...")
    
    electron_dir = Path("electron")
    if not electron_dir.exists():
        print("❌ Electron directory not found")
        return False
    
    try:
        # Install Electron dependencies
        print("📦 Installing Electron dependencies...")
        result = subprocess.run(['npm', 'install'], cwd=electron_dir, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ npm install failed: {result.stderr}")
            return False
        print("✅ Electron dependencies installed")
        
        # Check if electron is available
        result = subprocess.run(['npx', 'electron', '--version'], cwd=electron_dir, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Electron {result.stdout.strip()} available")
            return True
        else:
            print("❌ Electron not available")
            return False
        
    except Exception as e:
        print(f"❌ Error during Electron setup: {e}")
        return False

def create_minimal_api_server():
    """Create a minimal API server for testing."""
    print("\n🌐 Creating minimal API server for testing...")
    
    minimal_api = '''
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Test API")

@app.get("/health")
def health():
    return {"status": "healthy", "message": "Test API is running"}

@app.get("/api/workflows")
def list_workflows():
    return {
        "config_workflows": {},
        "predefined_workflows": {
            "test_workflow": {
                "name": "test_workflow",
                "description": "A test workflow for demonstration"
            }
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
'''
    
    test_api_path = Path("test_api.py")
    with open(test_api_path, 'w') as f:
        f.write(minimal_api)
    
    print("✅ Created test_api.py")
    return True

def show_testing_instructions():
    """Show instructions for testing the app."""
    print("\n" + "=" * 60)
    print("🎯 TESTING INSTRUCTIONS")
    print("=" * 60)
    
    print("\n1️⃣  TEST REACT FRONTEND ONLY:")
    print("   cd web")
    print("   npm start")
    print("   # Opens http://localhost:3000 (will show API connection errors)")
    
    print("\n2️⃣  TEST WITH MINIMAL API:")
    print("   # Terminal 1: Start test API")
    print("   pip install fastapi uvicorn  # or use pipx")
    print("   python test_api.py")
    print("   ")
    print("   # Terminal 2: Start React")
    print("   cd web && npm start")
    
    print("\n3️⃣  TEST ELECTRON (after React build):")
    print("   cd electron")
    print("   npm run electron-dev")
    print("   # Will try to start but may fail due to missing Python server")
    
    print("\n4️⃣  FULL TESTING (requires Python dependencies):")
    print("   # Install in virtual environment:")
    print("   python3 -m venv venv")
    print("   source venv/bin/activate")
    print("   pip install fastapi uvicorn sqlalchemy alembic")
    print("   python run-dev.py")
    
    print("\n5️⃣  PRODUCTION BUILD TEST:")
    print("   python build-electron.py")
    print("   # Check electron/dist/ for built applications")

def main():
    """Main test function."""
    print("🧪 Curriculum Curator Electron - Simple Test")
    print("=" * 60)
    
    # Check basic requirements
    if not Path("web").exists() or not Path("electron").exists():
        print("❌ Missing web or electron directories")
        return False
    
    results = []
    
    # Test React setup
    results.append(test_react_setup())
    
    # Test Electron setup  
    results.append(test_electron_setup())
    
    # Create minimal API for testing
    results.append(create_minimal_api_server())
    
    # Show testing instructions
    show_testing_instructions()
    
    print("\n" + "=" * 60)
    if all(results):
        print("🎉 Setup tests completed successfully!")
        print("You can now test individual components using the instructions above.")
    else:
        print("❌ Some setup steps failed. Check the output above.")
    
    return all(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)