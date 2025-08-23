#!/usr/bin/env python3
"""
Revert all snake_case field references back to camelCase in frontend
"""
import os
import re

# Field mappings - reverse of what we did before
field_mappings = {
    'pedagogy_type': 'pedagogyType',
    'difficulty_level': 'difficultyLevel', 
    'duration_weeks': 'durationWeeks',
    'credit_points': 'creditPoints',
    'owner_id': 'ownerId',
    'created_by_id': 'createdById',
    'updated_by_id': 'updatedById',
    'created_at': 'createdAt',
    'updated_at': 'updatedAt',
    'progress_percentage': 'progressPercentage',
    'module_count': 'moduleCount',
    'material_count': 'materialCount',
    'lrd_count': 'lrdCount',
    'learning_hours': 'learningHours',
    'unit_metadata': 'unitMetadata',
    'generation_context': 'generationContext',
    'is_active': 'isActive',
    'is_verified': 'isVerified',
    'full_name': 'fullName',
    'user_id': 'userId',
    'unit_id': 'unitId',
    'material_id': 'materialId',
    'lrd_id': 'lrdId',
    'task_id': 'taskId',
    'total_tasks': 'totalTasks',
    'completed_tasks': 'completedTasks',
    'teaching_philosophy': 'teachingPhilosophy',
    'delivery_mode': 'deliveryMode',
    'teaching_pattern': 'teachingPattern',
    'is_complete': 'isComplete',
    'completion_percentage': 'completionPercentage',
    'parent_version_id': 'parentVersionId',
    'is_latest': 'isLatest',
    'validation_results': 'validationResults',
    'quality_score': 'qualityScore',
    'word_count': 'wordCount',
    'change_summary': 'changeSummary',
    'created_by': 'createdBy',
    'current_stage': 'currentStage',
    'message_count': 'messageCount',
    'decisions_made': 'decisionsMade',
    'can_generate_structure': 'canGenerateStructure',
    'duration_minutes': 'durationMinutes',
    'completed_count': 'completedCount',
    'recent_materials': 'recentMaterials',
    'pending_tasks': 'pendingTasks',
    'last_login': 'lastLogin',
    'estimated_duration': 'estimatedDuration',
    'material_count': 'materialCount',
    'task_count': 'taskCount',
    'task_lists': 'taskLists',
}

# Also fix is_active function to isActive
special_replacements = [
    ('is_active\\(', 'isActive('),  # Function name
]

def fix_file(filepath):
    """Fix snake_case to camelCase in a file"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    
    # Replace field references (e.g., unit.pedagogy_type -> unit.pedagogyType)
    for snake, camel in field_mappings.items():
        # Match object.field patterns
        pattern = r'(\w+)\.' + re.escape(snake) + r'\b'
        replacement = r'\1.' + camel
        content = re.sub(pattern, replacement, content)
        
        # Match destructured fields (e.g., { pedagogy_type } -> { pedagogyType })
        pattern = r'(\{[^}]*)\b' + re.escape(snake) + r'\b([^}]*\})'
        replacement = r'\1' + camel + r'\2'
        content = re.sub(pattern, replacement, content)
        
        # Match in template literals
        pattern = r'\$\{([^}]*)\.' + re.escape(snake) + r'\}'
        replacement = r'${\1.' + camel + '}'
        content = re.sub(pattern, replacement, content)
    
    # Apply special replacements
    for old, new in special_replacements:
        content = re.sub(old, new, content)
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False

def main():
    frontend_dir = 'src'
    fixed_files = []
    
    print("Reverting snake_case to camelCase in frontend...")
    print("=" * 50)
    
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