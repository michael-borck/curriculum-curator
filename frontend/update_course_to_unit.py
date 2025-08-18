#!/usr/bin/env python3
"""
Script to update all Course references to Unit in the frontend
while keeping API endpoints as /api/courses for backward compatibility
"""

import re
from pathlib import Path


def update_file_content(file_path, replacements, preserve_api=False):
    """Update content in a file with specific replacements"""
    with file_path.open() as f:
        content = f.read()
    
    original_content = content
    
    # Apply replacements
    for pattern, replacement in replacements:
        if preserve_api and '/api/courses' in pattern:
            continue  # Skip API endpoint replacements
        content = re.sub(pattern, replacement, content)
    
    # Only write if content changed
    if content != original_content:
        with file_path.open('w') as f:
            f.write(content)
        return True
    return False


def main():
    frontend_path = Path.cwd()
    
    print("Frontend Course to Unit Terminology Update")
    print("==========================================")
    print(f"Working directory: {frontend_path}")
    
    # Define comprehensive replacements for UI text and labels
    ui_replacements = [
        # Component text and labels
        (r'\bCreate Course\b', 'Create Unit'),
        (r'\bcreate course\b', 'create unit'),
        (r'\bCourse creation\b', 'Unit creation'),
        (r'\bCourse Creation\b', 'Unit Creation'),
        (r'\bCourse Manager\b', 'Unit Manager'),
        (r'\bCourse Dashboard\b', 'Unit Dashboard'),
        (r'\bCourse View\b', 'Unit View'),
        (r'\bCourse Workflow\b', 'Unit Workflow'),
        (r'\bCourse Structure\b', 'Unit Structure'),
        (r'\bcourse structure\b', 'unit structure'),
        (r'\bCourse Settings\b', 'Unit Settings'),
        (r'\bcourse settings\b', 'unit settings'),
        (r'\bCourse Overview\b', 'Unit Overview'),
        (r'\bcourse overview\b', 'unit overview'),
        (r'\bCourse Details\b', 'Unit Details'),
        (r'\bcourse details\b', 'unit details'),
        (r'\bCourse Information\b', 'Unit Information'),
        (r'\bcourse information\b', 'unit information'),
        (r'\bCourse Materials\b', 'Unit Materials'),
        (r'\bcourse materials\b', 'unit materials'),
        (r'\bCourse Content\b', 'Unit Content'),
        (r'\bcourse content\b', 'unit content'),
        (r'\bCourse Stats\b', 'Unit Stats'),
        (r'\bcourse stats\b', 'unit stats'),
        (r'\bCourse Progress\b', 'Unit Progress'),
        (r'\bcourse progress\b', 'unit progress'),
        (r'\bDelete Course\b', 'Delete Unit'),
        (r'\bdelete course\b', 'delete unit'),
        (r'\bEdit Course\b', 'Edit Unit'),
        (r'\bedit course\b', 'edit unit'),
        (r'\bView Course\b', 'View Unit'),
        (r'\bview course\b', 'view unit'),
        (r'\bSelect Course\b', 'Select Unit'),
        (r'\bselect course\b', 'select unit'),
        (r'\bCourse Header\b', 'Unit Header'),
        (r'\bcourse header\b', 'unit header'),
        (r'\bCourse Description\b', 'Unit Description'),
        (r'\bcourse description\b', 'unit description'),
        (r"'Course'", "'Unit'"),
        (r'"Course"', '"Unit"'),
        (r'\bthis course\b', 'this unit'),
        (r'\bThis course\b', 'This unit'),
        (r'\bthe course\b', 'the unit'),
        (r'\bThe course\b', 'The unit'),
        (r'\bof the course\b', 'of the unit'),
        (r'\bfor the course\b', 'for the unit'),
        (r'\bBrief description of the course', 'Brief description of the unit'),
        (r'\bFailed to create course\b', 'Failed to create unit'),
        (r'\bFailed to load course\b', 'Failed to load unit'),
        (r'\bFailed to update course\b', 'Failed to update unit'),
        (r'\bFailed to delete course\b', 'Failed to delete unit'),
        (r'\bAre you sure you want to delete this course\?', 'Are you sure you want to delete this unit?'),
        (r'\bNo courses found\b', 'No units found'),
        (r'\bNo Courses Found\b', 'No Units Found'),
        (r'\bYour courses\b', 'Your units'),
        (r'\bYour Courses\b', 'Your Units'),
        (r'\bMy Courses\b', 'My Units'),
        (r'\bmy courses\b', 'my units'),
        (r'\bAll Courses\b', 'All Units'),
        (r'\ball courses\b', 'all units'),
        (r'\bcourse outline\b', 'unit outline'),
        (r'\bCourse Outline\b', 'Unit Outline'),
        (r'placeholder="Course code"', 'placeholder="Unit code"'),
        (r'placeholder="Course title"', 'placeholder="Unit title"'),
        (r"placeholder='Course code'", "placeholder='Unit code'"),
        (r"placeholder='Course title'", "placeholder='Unit title'"),
    ]
    
    # Type/interface replacements
    type_replacements = [
        (r'\binterface Course\b', 'interface Unit'),
        (r'\btype Course\b', 'type Unit'),
        (r'\bCourse\[\]', 'Unit[]'),
        (r'\b<Course>', '<Unit>'),
        (r'\bCourseCreate\b', 'UnitCreate'),
        (r'\bCourseUpdate\b', 'UnitUpdate'),
        (r'\bCourseResponse\b', 'UnitResponse'),
        (r'\bCourseListResponse\b', 'UnitListResponse'),
        (r'\bCourseData\b', 'UnitData'),
        (r'\bcourseData\b', 'unitData'),
        (r'\bCourseFormData\b', 'UnitFormData'),
        (r'\bcourseFormData\b', 'unitFormData'),
    ]
    
    # Variable name replacements (be careful with these)
    variable_replacements = [
        (r'\bconst courses\b', 'const units'),
        (r'\blet courses\b', 'let units'),
        (r'\bsetCourses\b', 'setUnits'),
        (r'\bcourse\.', 'unit.'),
        (r'\bcourses\.', 'units.'),
        (r'\bcourseId\b', 'unitId'),
        (r'\bcourse_id\b', 'unit_id'),
        (r'deleteCourse\b', 'deleteUnit'),
        (r'fetchCourses\b', 'fetchUnits'),
        (r'loadCourse\b', 'loadUnit'),
        (r'createCourse\b', 'createUnit'),
        (r'updateCourse\b', 'updateUnit'),
        (r'selectedCourse\b', 'selectedUnit'),
        (r'currentCourse\b', 'currentUnit'),
        (r'\{course\}', '{unit}'),
        (r'\(course\)', '(unit)'),
        (r'course =>', 'unit =>'),
        (r'course:', 'unit:'),
    ]
    
    # Route path replacements (updating frontend routes but NOT API endpoints)
    route_replacements = [
        (r"'/courses/", "'/units/"),
        (r'"/courses/', '"/units/'),
        (r'`/courses/', '`/units/'),
        (r'path="/courses', 'path="/units'),
        (r"path='/courses", "path='/units"),
        (r'navigate\(`/courses/', 'navigate(`/units/'),
        (r"navigate\('/courses/", "navigate('/units/"),
        (r'navigate\("/courses/', 'navigate("/units/'),
    ]
    
    # Find all TypeScript/JavaScript files
    ts_files = list(frontend_path.glob("src/**/*.tsx")) + \
               list(frontend_path.glob("src/**/*.ts")) + \
               list(frontend_path.glob("src/**/*.jsx")) + \
               list(frontend_path.glob("src/**/*.js"))
    
    files_updated = 0
    
    for file_path in ts_files:
        # Skip node_modules and build directories
        if 'node_modules' in str(file_path) or 'build' in str(file_path) or 'dist' in str(file_path):
            continue
            
        try:
            # Apply UI text replacements first
            updated = update_file_content(file_path, ui_replacements, preserve_api=True)
            
            # Apply type replacements
            updated = update_file_content(file_path, type_replacements, preserve_api=True) or updated
            
            # Apply variable replacements carefully
            updated = update_file_content(file_path, variable_replacements, preserve_api=True) or updated
            
            # Apply route replacements (but not API endpoints)
            updated = update_file_content(file_path, route_replacements, preserve_api=True) or updated
            
            if updated:
                print(f"✓ Updated: {file_path.relative_to(frontend_path)}")
                files_updated += 1
                
        except Exception as e:
            print(f"✗ Error updating {file_path}: {e}")
    
    # Now handle component file renames
    print("\n" + "="*50)
    print("Component File Renames")
    print("="*50)
    
    # List of files to rename
    files_to_rename = [
        ("src/features/courses/CourseManager.tsx", "src/features/courses/UnitManager.tsx"),
        ("src/features/courses/CourseManager.test.tsx", "src/features/courses/UnitManager.test.tsx"),
        ("src/features/courses/CourseDashboard.tsx", "src/features/courses/UnitDashboard.tsx"),
        ("src/features/courses/CourseView.tsx", "src/features/courses/UnitView.tsx"),
        ("src/features/courses/CourseWorkflow.tsx", "src/features/courses/UnitWorkflow.tsx"),
        ("src/components/CourseStructure/CourseStructureView.tsx", "src/components/UnitStructure/UnitStructureView.tsx"),
    ]
    
    for old_path, new_path in files_to_rename:
        old_file = frontend_path / old_path
        new_file = frontend_path / new_path
        
        if old_file.exists():
            # Create new directory if needed
            new_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Read content and update imports
            with old_file.open() as f:
                content = f.read()
            
            # Update imports in the renamed file
            content = re.sub(r'CourseManager', 'UnitManager', content)
            content = re.sub(r'CourseDashboard', 'UnitDashboard', content)
            content = re.sub(r'CourseView', 'UnitView', content)
            content = re.sub(r'CourseWorkflow', 'UnitWorkflow', content)
            content = re.sub(r'CourseStructureView', 'UnitStructureView', content)
            
            # Write to new location
            with new_file.open('w') as f:
                f.write(content)
            
            # Delete old file
            old_file.unlink()
            
            print(f"✓ Renamed: {old_path} → {new_path}")
    
    # Update imports in other files
    print("\n" + "="*50)
    print("Updating Component Imports")
    print("="*50)
    
    import_replacements = [
        (r"from '\./features/courses/CourseManager'", "from './features/courses/UnitManager'"),
        (r"from '\./features/courses/CourseDashboard'", "from './features/courses/UnitDashboard'"),
        (r"from '\./features/courses/CourseView'", "from './features/courses/UnitView'"),
        (r"from '\./features/courses/CourseWorkflow'", "from './features/courses/UnitWorkflow'"),
        (r"from '\.\./\.\./components/CourseStructure/CourseStructureView'", "from '../../components/UnitStructure/UnitStructureView'"),
        (r'CourseManager', 'UnitManager'),
        (r'CourseDashboard', 'UnitDashboard'),
        (r'CourseView', 'UnitView'),
        (r'CourseWorkflow', 'UnitWorkflow'),
        (r'CourseStructureView', 'UnitStructureView'),
    ]
    
    for file_path in ts_files:
        if 'node_modules' in str(file_path) or 'build' in str(file_path):
            continue
            
        try:
            if update_file_content(file_path, import_replacements, preserve_api=False):
                print(f"✓ Updated imports in: {file_path.relative_to(frontend_path)}")
        except Exception as e:
            print(f"✗ Error updating imports in {file_path}: {e}")
    
    print("\n" + "="*50)
    print(f"Update Complete! {files_updated} files updated.")
    print("="*50)
    print("\nNOTE: API endpoints remain as /api/courses for backward compatibility")
    print("      Frontend routes have been updated to use /units/")
    print("\nNext steps:")
    print("1. Run 'npm run type-check' to verify TypeScript")
    print("2. Run 'npm test' to verify tests")
    print("3. Start the app and test functionality")


if __name__ == "__main__":
    main()