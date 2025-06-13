#!/usr/bin/env python3
"""
Validation script for Curriculum Curator Electron setup.
Checks that all required files and structure are in place.
"""

from pathlib import Path
import json

def check_file_exists(path, description):
    """Check if a file exists and report."""
    if Path(path).exists():
        print(f"✅ {description}: {path}")
        return True
    else:
        print(f"❌ {description}: {path} (missing)")
        return False

def check_directory_exists(path, description):
    """Check if a directory exists and report."""
    if Path(path).is_dir():
        print(f"✅ {description}: {path}")
        return True
    else:
        print(f"❌ {description}: {path} (missing)")
        return False

def validate_json_file(path, description):
    """Validate a JSON file."""
    if not Path(path).exists():
        print(f"❌ {description}: {path} (missing)")
        return False
    
    try:
        with open(path, 'r') as f:
            json.load(f)
        print(f"✅ {description}: {path} (valid JSON)")
        return True
    except json.JSONDecodeError as e:
        print(f"❌ {description}: {path} (invalid JSON: {e})")
        return False

def main():
    """Main validation function."""
    print("🔍 Validating Curriculum Curator Electron setup...")
    print()
    
    all_good = True
    
    # Check core Python structure
    print("📦 Core Python Package:")
    all_good &= check_directory_exists("curriculum_curator", "Main package")
    all_good &= check_directory_exists("curriculum_curator/web", "Web module")
    all_good &= check_file_exists("curriculum_curator/web/__init__.py", "Web __init__.py")
    all_good &= check_file_exists("curriculum_curator/web/api.py", "FastAPI server")
    all_good &= check_file_exists("curriculum_curator/web/models.py", "Database models")
    print()
    
    # Check React frontend
    print("⚛️  React Frontend:")
    all_good &= check_directory_exists("web", "Web directory")
    all_good &= validate_json_file("web/package.json", "React package.json")
    all_good &= check_directory_exists("web/src", "React src directory")
    all_good &= check_directory_exists("web/src/components", "React components")
    all_good &= check_directory_exists("web/src/pages", "React pages")
    all_good &= check_file_exists("web/src/App.tsx", "Main App component")
    all_good &= check_file_exists("web/src/index.tsx", "React entry point")
    print()
    
    # Check Electron setup
    print("🖥️  Electron Application:")
    all_good &= check_directory_exists("electron", "Electron directory")
    all_good &= validate_json_file("electron/package.json", "Electron package.json")
    all_good &= check_file_exists("electron/main.js", "Electron main process")
    all_good &= check_file_exists("electron/preload.js", "Electron preload script")
    print()
    
    # Check build scripts
    print("🔧 Build Scripts:")
    all_good &= check_file_exists("build-electron.py", "Build script")
    all_good &= check_file_exists("run-dev.py", "Development runner")
    all_good &= check_file_exists("README-ELECTRON.md", "Documentation")
    print()
    
    # Check configuration
    print("⚙️  Configuration:")
    all_good &= check_file_exists("pyproject.toml", "Python project config")
    all_good &= check_file_exists("web/.env", "React environment config")
    all_good &= check_file_exists("web/tailwind.config.js", "Tailwind config")
    print()
    
    # Summary
    print("=" * 50)
    if all_good:
        print("🎉 All checks passed! Your Electron setup looks good.")
        print()
        print("Next steps:")
        print("1. Install web dependencies: pip install -e '.[web]'")
        print("2. Run development: python run-dev.py")
        print("3. Build for production: python build-electron.py")
    else:
        print("❌ Some checks failed. Please fix the missing files/directories.")
        print("   Refer to the implementation steps or README-ELECTRON.md")
    
    return all_good

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)