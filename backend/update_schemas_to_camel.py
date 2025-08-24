#!/usr/bin/env python3
"""
Update all Pydantic schemas to use CamelModel base class
"""
import re
from pathlib import Path


def update_file(filepath):
    """Update a schema file to use CamelModel"""
    file_path = Path(filepath)
    content = file_path.read_text()

    original = content

    # Skip if already using CamelModel
    if 'from app.schemas.base import CamelModel' in content:
        print(f"  ✓ Already updated: {filepath}")
        return False

    # Skip base.py itself
    if filepath.endswith('base.py'):
        return False

    # Add import if file has BaseModel classes
    if 'from pydantic import' in content and 'BaseModel' in content:
        # Add CamelModel import
        if 'from pydantic import BaseModel' in content:
            content = content.replace(
                'from pydantic import BaseModel',
                'from pydantic import BaseModel\nfrom app.schemas.base import CamelModel'
            )
            # Replace class definitions
            content = re.sub(r'class (\w+)\(BaseModel\):', r'class \1(CamelModel):', content)
        else:
            # BaseModel is imported differently
            import_match = re.search(r'from pydantic import ([^;\n]+)', content)
            if import_match:
                imports = import_match.group(1)
                # Remove BaseModel from imports
                imports_list = [i.strip() for i in imports.split(',')]
                if 'BaseModel' in imports_list:
                    imports_list.remove('BaseModel')
                new_imports = ', '.join(imports_list)
                content = content.replace(
                    f'from pydantic import {imports}',
                    f'from pydantic import {new_imports}\nfrom app.schemas.base import CamelModel'
                )
                # Replace class definitions
                content = re.sub(r'class (\w+)\(BaseModel\):', r'class \1(CamelModel):', content)

    # Special handling for certain schemas that should keep specific fields
    if 'auth.py' in filepath:
        # OAuth2 standard fields should remain snake_case
        # We'll handle these with Field aliases
        pass

    if content != original:
        file_path.write_text(content)
        print(f"  ✅ Updated: {filepath}")
        return True
    return False

def main():
    schemas_dir = 'app/schemas'
    updated_files = []

    print("Updating Pydantic schemas to use CamelModel...")
    print("=" * 50)

    schemas_path = Path(schemas_dir)
    updated_files = []

    for filepath in schemas_path.rglob('*.py'):
        if filepath.name != '__init__.py' and update_file(str(filepath)):
            updated_files.append(str(filepath))

    print(f"\n📊 Updated {len(updated_files)} files")

    # Handle special cases
    print("\n⚠️  Note: Some schemas may need manual review:")
    print("  - auth.py: Check OAuth2 standard fields (access_token, token_type)")
    print("  - Any schema with explicit Field aliases")

if __name__ == '__main__':
    main()
