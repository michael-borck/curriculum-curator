#!/usr/bin/env python3
"""
Fix all camelCase field references to snake_case in frontend
"""
import os
import re

# Field mappings
field_mappings = {
    'pedagogyType': 'pedagogy_type',
    'difficultyLevel': 'difficulty_level', 
    'durationWeeks': 'duration_weeks',
    'creditPoints': 'credit_points',
    'ownerId': 'owner_id',
    'createdById': 'created_by_id',
    'updatedById': 'updated_by_id',
    'createdAt': 'created_at',
    'updatedAt': 'updated_at',
    'progressPercentage': 'progress_percentage',
    'moduleCount': 'module_count',
    'materialCount': 'material_count',
    'lrdCount': 'lrd_count',
    'learningHours': 'learning_hours',
    'unitMetadata': 'unit_metadata',
    'generationContext': 'generation_context',
    'isActive': 'is_active',
    'isVerified': 'is_verified',
    'fullName': 'full_name',
}

def fix_file(filepath):
    """Fix camelCase to snake_case in a file"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    
    # Replace field references (e.g., unit.pedagogyType -> unit.pedagogy_type)
    for camel, snake in field_mappings.items():
        # Match object.field patterns
        pattern = r'(\w+)\.' + re.escape(camel) + r'\b'
        replacement = r'\1.' + snake
        content = re.sub(pattern, replacement, content)
        
        # Match destructured fields (e.g., { pedagogyType } -> { pedagogy_type })
        pattern = r'(\{[^}]*)\b' + re.escape(camel) + r'\b([^}]*\})'
        replacement = r'\1' + snake + r'\2'
        content = re.sub(pattern, replacement, content)
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False

def main():
    frontend_dir = 'frontend/src'
    fixed_files = []
    
    for root, dirs, files in os.walk(frontend_dir):
        # Skip node_modules and other irrelevant directories
        dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', 'dist']]
        
        for file in files:
            if file.endswith(('.tsx', '.ts', '.jsx', '.js')):
                filepath = os.path.join(root, file)
                if fix_file(filepath):
                    fixed_files.append(filepath)
    
    print(f"Fixed {len(fixed_files)} files:")
    for f in fixed_files:
        print(f"  - {f}")

if __name__ == '__main__':
    main()