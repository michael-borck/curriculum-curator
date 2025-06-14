#!/usr/bin/env python3
"""
Basic test script that doesn't require web dependencies.
Tests the structure and basic imports.
"""

import sys
from pathlib import Path

def test_python_structure():
    """Test that Python modules can be imported."""
    print("🐍 Testing Python structure...")
    
    try:
        # Test core imports (should work without web deps)
        import curriculum_curator.cli
        import curriculum_curator.core
        import curriculum_curator.config.utils
        print("✅ Core modules import successfully")
        
        # Test CLI functionality
        from curriculum_curator.cli import app
        print("✅ CLI app loads successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_file_structure():
    """Test that all required files exist."""
    print("\n📁 Testing file structure...")
    
    required_files = [
        "curriculum_curator/web/api.py",
        "curriculum_curator/web/models.py", 
        "web/package.json",
        "web/src/App.tsx",
        "electron/package.json",
        "electron/main.js",
        "build-electron.py",
        "run-dev.py"
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} (missing)")
            all_exist = False
    
    return all_exist

def test_json_configs():
    """Test that JSON configs are valid."""
    print("\n📋 Testing JSON configurations...")
    
    import json
    json_files = [
        "web/package.json",
        "electron/package.json"
    ]
    
    all_valid = True
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                json.load(f)
            print(f"✅ {json_file} (valid JSON)")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"❌ {json_file} (error: {e})")
            all_valid = False
    
    return all_valid

def test_node_setup():
    """Test if Node.js is available."""
    print("\n🟢 Testing Node.js setup...")
    
    import subprocess
    try:
        # Check Node.js
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js {result.stdout.strip()}")
        else:
            print("❌ Node.js not found")
            return False
        
        # Check npm
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ npm {result.stdout.strip()}")
        else:
            print("❌ npm not found")
            return False
        
        return True
    except FileNotFoundError:
        print("❌ Node.js/npm not found in PATH")
        return False

def main():
    """Run all basic tests."""
    print("🔬 Running basic tests for Curriculum Curator Electron app...")
    print("=" * 60)
    
    results = []
    results.append(test_python_structure())
    results.append(test_file_structure())
    results.append(test_json_configs())
    results.append(test_node_setup())
    
    print("\n" + "=" * 60)
    if all(results):
        print("🎉 All basic tests passed!")
        print("\nNext steps to run the full app:")
        print("1. Install web dependencies: pip install -e '.[web]'")
        print("2. Run development mode: python run-dev.py")
        print("\nOr test components individually:")
        print("- API server: uvicorn curriculum_curator.web.api:app --port 8000")
        print("- React app: cd web && npm install && npm start")
        print("- Electron: cd electron && npm install && npm run electron-dev")
    else:
        print("❌ Some tests failed. Check the output above for details.")
    
    return all(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)