#!/usr/bin/env python3
"""
Fix all snake_case to camelCase references in frontend
"""

import re
import os

def fix_file(filepath):
    """Fix snake_case to camelCase in a file"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    
    # Field name mappings
    replacements = [
        # Direct property access
        (r'\.credit_points\b', '.creditPoints'),
        (r'\.duration_weeks\b', '.durationWeeks'),
        (r'\.pedagogy_type\b', '.pedagogyType'),
        (r'\.difficulty_level\b', '.difficultyLevel'),
        (r'\.learning_hours\b', '.learningHours'),
        (r'\.progress_percentage\b', '.progressPercentage'),
        (r'\.module_count\b', '.moduleCount'),
        (r'\.material_count\b', '.materialCount'),
        (r'\.lrd_count\b', '.lrdCount'),
        (r'\.owner_id\b', '.ownerId'),
        (r'\.created_at\b', '.createdAt'),
        (r'\.updated_at\b', '.updatedAt'),
        (r'\.user_id\b', '.userId'),
        (r'\.unit_id\b', '.unitId'),
        (r'\.default_credit_points\b', '.defaultCreditPoints'),
        (r'\.default_duration_weeks\b', '.defaultDurationWeeks'),
        
        # Object keys
        (r'\bcredit_points:', 'creditPoints:'),
        (r'\bduration_weeks:', 'durationWeeks:'),
        (r'\bpedagogy_type:', 'pedagogyType:'),
        (r'\bdifficulty_level:', 'difficultyLevel:'),
        (r'\blearning_hours:', 'learningHours:'),
        (r'\bprogress_percentage:', 'progressPercentage:'),
        (r'\bmodule_count:', 'moduleCount:'),
        (r'\bmaterial_count:', 'materialCount:'),
        (r'\blrd_count:', 'lrdCount:'),
        (r'\bowner_id:', 'ownerId:'),
        (r'\bcreated_at:', 'createdAt:'),
        (r'\bupdated_at:', 'updatedAt:'),
        (r'\buser_id:', 'userId:'),
        (r'\bunit_id:', 'unitId:'),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False

def main():
    frontend_dir = "/home/michael/Downloads/curriculum-curator/generated_project/frontend/src"
    
    fixed_files = []
    
    for root, _, files in os.walk(frontend_dir):
        for file in files:
            if file.endswith(('.tsx', '.ts')):
                filepath = os.path.join(root, file)
                if fix_file(filepath):
                    fixed_files.append(filepath)
    
    print(f"Fixed {len(fixed_files)} files:")
    for f in fixed_files:
        print(f"  - {os.path.relpath(f, frontend_dir)}")

if __name__ == "__main__":
    main()