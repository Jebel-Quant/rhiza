#!/usr/bin/env python3
import sys

import yaml


def check_file(filepath):
    with open(filepath, 'r') as f:
        try:
            content = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            print(f"Error parsing YAML {filepath}: {exc}")
            return False
            
    if not isinstance(content, dict):
        # Empty file or not a dict
        return True

    name = content.get('name')
    if not name:
        print(f"Error: {filepath} missing 'name' field.")
        return False
        
    if not name.startswith('(RHIZA) '):
        print(f"Updating {filepath}: name '{name}' -> '(RHIZA) {name}'")
        
        # Read file lines to perform replacement while preserving comments
        with open(filepath, 'r') as f_read:
            lines = f_read.readlines()
        
        with open(filepath, 'w') as f_write:
            replaced = False
            for line in lines:
                # Replace only the top-level name field (assumes it starts at beginning of line)
                if not replaced and line.startswith('name:'):
                    # Check if this line corresponds to the extracted name. 
                    # Simple check: does it contain reasonable parts of the name?
                    # Or just blinding replace top-level name:
                    # We'll use quotes to be safe
                    f_write.write(f'name: "(RHIZA) {name}"\n')
                    replaced = True
                else:
                    f_write.write(line)
        
        return False # Fail so pre-commit knows files were modified
        
    return True

def main():
    files = sys.argv[1:]
    failed = False
    for f in files:
        if not check_file(f):
            failed = True
            
    if failed:
        sys.exit(1)

if __name__ == "__main__":
    main()
