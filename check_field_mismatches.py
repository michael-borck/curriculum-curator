#!/usr/bin/env python3
"""
Check for field mismatches between frontend TypeScript interfaces and backend Pydantic models
"""

import os
import re
from pathlib import Path
from typing import Set, Dict, List

def find_typescript_interfaces(frontend_dir: str) -> Dict[str, Set[str]]:
    """Find all TypeScript interfaces and their fields"""
    interfaces = {}
    
    for root, _, files in os.walk(frontend_dir):
        for file in files:
            if file.endswith(('.ts', '.tsx')):
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    content = f.read()
                    
                    # Find interface definitions
                    interface_pattern = r'interface\s+(\w+)\s*\{([^}]+)\}'
                    for match in re.finditer(interface_pattern, content, re.MULTILINE | re.DOTALL):
                        interface_name = match.group(1)
                        interface_body = match.group(2)
                        
                        # Extract field names
                        field_pattern = r'^\s*(\w+)[\?]?\s*:'
                        fields = set(re.findall(field_pattern, interface_body, re.MULTILINE))
                        
                        if interface_name not in interfaces:
                            interfaces[interface_name] = fields
                        else:
                            interfaces[interface_name].update(fields)
    
    return interfaces

def find_pydantic_models(backend_dir: str) -> Dict[str, Set[str]]:
    """Find all Pydantic models and their fields"""
    models = {}
    
    for root, _, files in os.walk(backend_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    content = f.read()
                    
                    # Find class definitions that inherit from BaseModel
                    class_pattern = r'class\s+(\w+)\([^)]*BaseModel[^)]*\):(.*?)(?=class\s|\Z)'
                    for match in re.finditer(class_pattern, content, re.MULTILINE | re.DOTALL):
                        class_name = match.group(1)
                        class_body = match.group(2)
                        
                        # Extract field names (Pydantic style)
                        field_pattern = r'^\s*(\w+)\s*[:=]'
                        fields = set(re.findall(field_pattern, class_body, re.MULTILINE))
                        
                        # Remove special fields
                        fields.discard('Config')
                        fields.discard('__tablename__')
                        
                        if class_name not in models:
                            models[class_name] = fields
                        else:
                            models[class_name].update(fields)
    
    return models

def find_api_calls(frontend_dir: str) -> List[str]:
    """Find all API calls in frontend"""
    api_calls = []
    
    for root, _, files in os.walk(frontend_dir):
        for file in files:
            if file.endswith(('.ts', '.tsx')):
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    content = f.read()
                    
                    # Find API calls
                    patterns = [
                        r'api\.(get|post|put|delete|patch)\([\'"`]([^\'"`]+)',
                        r'fetch\([\'"`]([^\'"`]+)',
                    ]
                    
                    for pattern in patterns:
                        for match in re.finditer(pattern, content):
                            if len(match.groups()) == 2:
                                api_calls.append(f"{match.group(1).upper()} {match.group(2)}")
                            else:
                                api_calls.append(match.group(1))
    
    return api_calls

def check_common_issues():
    """Check for common issues"""
    print("\n🔍 Checking for Common Issues:")
    print("-" * 60)
    
    issues = []
    
    # Check for UUID vs string issues
    backend_dir = "/home/michael/Downloads/curriculum-curator/generated_project/backend"
    frontend_dir = "/home/michael/Downloads/curriculum-curator/generated_project/frontend/src"
    
    # Find all files with potential UUID issues
    print("\n1. Checking for UUID to string conversion issues...")
    for root, _, files in os.walk(backend_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    content = f.read()
                    if 'UUID(' in content and 'response_model' in content:
                        # Check if UUID fields are being converted
                        if 'str(' not in content:
                            rel_path = os.path.relpath(filepath, backend_dir)
                            issues.append(f"Potential UUID issue in {rel_path}")
    
    # Check for field name mismatches
    print("\n2. Checking for common field name patterns...")
    common_mismatches = [
        ('chat_history', 'messages'),
        ('course_id', 'unit_id'),
        ('course', 'unit'),
        ('created_at', 'createdAt'),
        ('updated_at', 'updatedAt'),
    ]
    
    for old_name, new_name in common_mismatches:
        # Check frontend
        count = 0
        for root, _, files in os.walk(frontend_dir):
            for file in files:
                if file.endswith(('.ts', '.tsx')):
                    filepath = os.path.join(root, file)
                    with open(filepath, 'r') as f:
                        content = f.read()
                        if old_name in content:
                            count += 1
        
        if count > 0:
            issues.append(f"Found {count} files with '{old_name}' (should be '{new_name}'?)")
    
    return issues

def main():
    print("🔍 Field Mismatch Detection Tool")
    print("=" * 60)
    
    backend_dir = "/home/michael/Downloads/curriculum-curator/generated_project/backend"
    frontend_dir = "/home/michael/Downloads/curriculum-curator/generated_project/frontend/src"
    
    # Find interfaces and models
    print("\n📋 Scanning TypeScript interfaces...")
    interfaces = find_typescript_interfaces(frontend_dir)
    print(f"   Found {len(interfaces)} interfaces")
    
    print("\n📋 Scanning Pydantic models...")
    models = find_pydantic_models(backend_dir)
    print(f"   Found {len(models)} models")
    
    # Find potential matches
    print("\n🔗 Checking for potential mismatches...")
    print("-" * 60)
    
    # Common naming patterns to match
    matches = []
    for ts_name, ts_fields in interfaces.items():
        # Try to find matching Pydantic model
        potential_matches = []
        
        # Direct match
        if ts_name in models:
            potential_matches.append(ts_name)
        
        # Response/Request variants
        for suffix in ['Response', 'Request', 'Create', 'Update', 'Base']:
            if ts_name + suffix in models:
                potential_matches.append(ts_name + suffix)
            if ts_name.endswith(suffix):
                base_name = ts_name[:-len(suffix)]
                if base_name in models:
                    potential_matches.append(base_name)
        
        # Check for field mismatches
        for model_name in potential_matches:
            model_fields = models[model_name]
            
            # Fields in TypeScript but not in Python
            ts_only = ts_fields - model_fields
            # Fields in Python but not in TypeScript
            py_only = model_fields - ts_fields
            
            if ts_only or py_only:
                matches.append((ts_name, model_name, ts_only, py_only))
    
    # Report mismatches
    if matches:
        print("\n⚠️  Potential Field Mismatches Found:")
        for ts_name, py_name, ts_only, py_only in matches[:10]:  # Show first 10
            print(f"\n   {ts_name} ↔ {py_name}:")
            if ts_only:
                print(f"      Frontend only: {', '.join(sorted(ts_only)[:5])}")
            if py_only:
                print(f"      Backend only: {', '.join(sorted(py_only)[:5])}")
    
    # Check common issues
    issues = check_common_issues()
    if issues:
        print("\n⚠️  Common Issues Found:")
        for issue in issues:
            print(f"   - {issue}")
    
    # Find API calls
    print("\n📡 API Calls in Frontend:")
    api_calls = find_api_calls(frontend_dir)
    unique_calls = set(api_calls)
    print(f"   Found {len(unique_calls)} unique API endpoints")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Summary:")
    print(f"   TypeScript interfaces: {len(interfaces)}")
    print(f"   Pydantic models: {len(models)}")
    print(f"   Potential mismatches: {len(matches)}")
    print(f"   Common issues: {len(issues)}")
    
    print("\n💡 Recommendations:")
    print("   1. Run test_all_endpoints.py to check API availability")
    print("   2. Review field mismatches above")
    print("   3. Check UUID to string conversions")
    print("   4. Ensure consistent naming (camelCase vs snake_case)")

if __name__ == "__main__":
    main()