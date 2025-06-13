#!/usr/bin/env python3
"""
Development runner for Curriculum Curator Electron app.
This script starts both the React dev server and the Python API server.
"""

import os
import subprocess
import sys
import time
import signal
from pathlib import Path
from threading import Thread

processes = []

def run_react_dev():
    """Run the React development server."""
    print("Starting React development server...")
    web_dir = Path("web")
    
    if not web_dir.exists():
        print("Error: web directory not found")
        return
    
    try:
        proc = subprocess.Popen(
            ["npm", "start"], 
            cwd=web_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        processes.append(proc)
        
        # Stream output
        for line in proc.stdout:
            print(f"[React] {line.strip()}")
            
    except Exception as e:
        print(f"Error starting React dev server: {e}")

def run_python_api():
    """Run the Python API server."""
    print("Starting Python API server...")
    
    try:
        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "curriculum_curator.web.api:app", 
             "--host", "127.0.0.1", "--port", "8000", "--reload"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        processes.append(proc)
        
        # Stream output
        for line in proc.stdout:
            print(f"[API] {line.strip()}")
            
    except Exception as e:
        print(f"Error starting Python API server: {e}")

def run_electron():
    """Run Electron in development mode."""
    print("Starting Electron...")
    electron_dir = Path("electron")
    
    if not electron_dir.exists():
        print("Error: electron directory not found")
        return
    
    # Wait a bit for servers to start
    time.sleep(5)
    
    try:
        proc = subprocess.Popen(
            ["npm", "run", "electron-dev"], 
            cwd=electron_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        processes.append(proc)
        
        # Stream output
        for line in proc.stdout:
            print(f"[Electron] {line.strip()}")
            
    except Exception as e:
        print(f"Error starting Electron: {e}")

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\nShutting down development servers...")
    for proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except:
            proc.kill()
    sys.exit(0)

def main():
    """Main development runner."""
    print("Starting Curriculum Curator development environment...")
    
    # Check if we're in the right directory
    if not Path("curriculum_curator").exists():
        print("Error: Please run this script from the curriculum-curator root directory")
        sys.exit(1)
    
    # Install dependencies if needed
    web_dir = Path("web")
    electron_dir = Path("electron")
    
    if web_dir.exists() and not (web_dir / "node_modules").exists():
        print("Installing React dependencies...")
        subprocess.run(["npm", "install"], cwd=web_dir)
    
    if electron_dir.exists() and not (electron_dir / "node_modules").exists():
        print("Installing Electron dependencies...")
        subprocess.run(["npm", "install"], cwd=electron_dir)
    
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Start servers in separate threads
        react_thread = Thread(target=run_react_dev, daemon=True)
        api_thread = Thread(target=run_python_api, daemon=True)
        electron_thread = Thread(target=run_electron, daemon=True)
        
        react_thread.start()
        api_thread.start()
        electron_thread.start()
        
        print("\n🚀 Development environment started!")
        print("- React: http://localhost:3000")
        print("- API: http://localhost:8000")
        print("- Electron app should open automatically")
        print("\nPress Ctrl+C to stop all servers")
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
    except Exception as e:
        print(f"Development environment failed: {e}")
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main()