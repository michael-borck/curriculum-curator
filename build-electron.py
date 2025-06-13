#!/usr/bin/env python3
"""
Build script for Curriculum Curator Electron app.
This script handles the complete build process including Python bundling.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None, check=True):
    """Run a command and handle errors."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        if check:
            sys.exit(1)
        return e

def build_react_app():
    """Build the React frontend."""
    print("Building React frontend...")
    web_dir = Path("web")
    
    if not web_dir.exists():
        print("Error: web directory not found")
        sys.exit(1)
    
    # Install dependencies if needed
    if not (web_dir / "node_modules").exists():
        run_command(["npm", "install"], cwd=web_dir)
    
    # Build the React app
    run_command(["npm", "run", "build"], cwd=web_dir)
    
    build_dir = web_dir / "build"
    if not build_dir.exists():
        print("Error: React build failed - build directory not found")
        sys.exit(1)
    
    print("React frontend built successfully")

def setup_electron():
    """Setup Electron dependencies."""
    print("Setting up Electron...")
    electron_dir = Path("electron")
    
    if not electron_dir.exists():
        print("Error: electron directory not found")
        sys.exit(1)
    
    # Install Electron dependencies
    if not (electron_dir / "node_modules").exists():
        run_command(["npm", "install"], cwd=electron_dir)
    
    print("Electron setup complete")

def create_python_bundle():
    """Create a Python bundle for the application."""
    print("Creating Python bundle...")
    
    # For now, we'll just copy the Python files
    # In a full production setup, you might want to use PyInstaller
    # or create a virtual environment bundle
    
    bundle_dir = Path("electron/python-server")
    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)
    
    bundle_dir.mkdir(parents=True)
    
    # Copy Python package
    shutil.copytree("curriculum_curator", bundle_dir / "curriculum_curator")
    
    # Copy essential files
    files_to_copy = ["pyproject.toml", "config.yaml"]
    for file_name in files_to_copy:
        src = Path(file_name)
        if src.exists():
            shutil.copy2(src, bundle_dir / file_name)
    
    # Copy prompts directory if it exists
    prompts_dir = Path("prompts")
    if prompts_dir.exists():
        shutil.copytree(prompts_dir, bundle_dir / "prompts")
    
    print("Python bundle created")

def build_electron_app():
    """Build the Electron application."""
    print("Building Electron application...")
    electron_dir = Path("electron")
    
    # Build for current platform
    run_command(["npm", "run", "dist"], cwd=electron_dir)
    
    print("Electron application built successfully")

def main():
    """Main build process."""
    print("Starting Curriculum Curator Electron build process...")
    
    # Check if we're in the right directory
    if not Path("curriculum_curator").exists():
        print("Error: Please run this script from the curriculum-curator root directory")
        sys.exit(1)
    
    try:
        # Step 1: Build React frontend
        build_react_app()
        
        # Step 2: Setup Electron
        setup_electron()
        
        # Step 3: Create Python bundle
        create_python_bundle()
        
        # Step 4: Build Electron app
        build_electron_app()
        
        print("\n🎉 Build completed successfully!")
        print("Built applications can be found in the electron/dist directory")
        
    except Exception as e:
        print(f"Build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()