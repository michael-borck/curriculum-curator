#!/usr/bin/env python3
"""
Script to rename all Course-related models and files to Unit for consistency
"""

import shutil
from pathlib import Path


def rename_file_content(file_path, replacements):
    """Replace content in a file"""
    with file_path.open() as f:
        content = f.read()

    for old, new in replacements:
        content = content.replace(old, new)

    with file_path.open("w") as f:
        f.write(content)

    print(f"  Updated content in {file_path}")


def main():
    print("Starting Course to Unit renaming...")

    backend_path = Path(__file__).parent

    # Step 1: Rename model file
    old_model_file = backend_path / "app/models/course_outline.py"
    new_model_file = backend_path / "app/models/unit_outline.py"

    if old_model_file.exists():
        # First update the content
        replacements = [
            ("class CourseOutline", "class UnitOutline"),
            ("class CourseStructureStatus", "class UnitStructureStatus"),
            ('__tablename__ = "course_outlines"', '__tablename__ = "unit_outlines"'),
            ("CourseOutline", "UnitOutline"),
            ("CourseStructureStatus", "UnitStructureStatus"),
            ("Course outline", "Unit outline"),
            ("course outline", "unit outline"),
        ]
        rename_file_content(old_model_file, replacements)

        # Then rename the file
        shutil.move(str(old_model_file), str(new_model_file))
        print(f"  Renamed {old_model_file} to {new_model_file}")

    # Step 2: Update models/__init__.py
    init_file = backend_path / "app/models/__init__.py"
    replacements = [
        (
            "from .course_outline import CourseOutline, CourseStructureStatus",
            "from .unit_outline import UnitOutline, UnitStructureStatus",
        ),
        ('"CourseOutline",', '"UnitOutline",'),
        ('"CourseStructureStatus",', '"UnitStructureStatus",'),
    ]
    rename_file_content(init_file, replacements)

    # Step 3: Update all model files that reference course_outlines
    model_files = [
        "app/models/assessment_plan.py",
        "app/models/chat_session.py",
        "app/models/weekly_topic.py",
        "app/models/learning_outcome.py",
    ]

    for model_file in model_files:
        file_path = backend_path / model_file
        if file_path.exists():
            replacements = [
                ('ForeignKey("course_outlines.id")', 'ForeignKey("unit_outlines.id")'),
                ("course_outline_id", "unit_outline_id"),
            ]
            rename_file_content(file_path, replacements)

    # Step 4: Update services and routes
    files_to_update = [
        "app/services/content_workflow_service.py",
        "app/api/routes/course_structure.py",
        "app/api/routes/content_workflow.py",
    ]

    for file_rel_path in files_to_update:
        file_path = backend_path / file_rel_path
        if file_path.exists():
            replacements = [
                ("CourseOutline", "UnitOutline"),
                ("CourseStructureStatus", "UnitStructureStatus"),
                ("course_outline_id", "unit_outline_id"),
                ("course_outline", "unit_outline"),
            ]
            rename_file_content(file_path, replacements)

    # Step 5: Rename route file
    old_route_file = backend_path / "app/api/routes/course_structure.py"
    new_route_file = backend_path / "app/api/routes/unit_structure.py"

    if old_route_file.exists():
        shutil.move(str(old_route_file), str(new_route_file))
        print(f"  Renamed {old_route_file} to {new_route_file}")

    # Step 6: Update main.py to import the renamed route
    main_file = backend_path / "app/main.py"
    replacements = [
        ("course_structure,", "unit_structure,"),
        ("course_structure.router", "unit_structure.router"),
        ('["course-structure"]', '["unit-structure"]'),
    ]
    rename_file_content(main_file, replacements)

    # Step 7: Update frontend components that might reference CourseOutline
    frontend_path = backend_path.parent / "frontend"

    # Find and update TypeScript files
    ts_files = list(frontend_path.glob("src/**/*.tsx")) + list(
        frontend_path.glob("src/**/*.ts")
    )

    for ts_file in ts_files:
        try:
            with ts_file.open() as f:
                content = f.read()

            if "CourseOutline" in content or "CourseStructure" in content:
                replacements = [
                    ("CourseOutline", "UnitOutline"),
                    ("CourseStructure", "UnitStructure"),
                    ("courseOutline", "unitOutline"),
                    ("course_outline", "unit_outline"),
                ]

                for old, new in replacements:
                    content = content.replace(old, new)

                with ts_file.open("w") as f:
                    f.write(content)

                print(f"  Updated {ts_file}")
        except Exception as e:
            print(f"  Warning: Could not update {ts_file}: {e}")

    print("\nRenaming complete!")
    print("\nNext steps:")
    print("1. Drop and recreate the database:")
    print("   rm curriculum_curator.db")
    print("   python init_db.py")
    print("2. Test the application")
    print("3. Commit the changes")


if __name__ == "__main__":
    main()
