#!/usr/bin/env python3
"""
JSON Metadata Extractor
Extracts metadata from JSON files and preserves it in separate metadata files,
while converting the main files to simple arrays.
"""

import os
import json
import glob
import sys
from pathlib import Path
import datetime

class JSONMetadataExtractor:
    def __init__(self):
        self.converted_files = []
        self.error_files = []
        self.skipped_files = []
        self.metadata_files = []

    def extract_metadata(self, filepath):
        """Extract metadata and convert file to simple array."""
        try:
            # Read the current JSON file
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check if it's already an array
            if isinstance(data, list):
                print(f"✅ {filepath} - Already an array, skipping")
                self.skipped_files.append(filepath)
                return False
            
            # Check if it's not a dict
            if not isinstance(data, dict):
                print(f"❌ {filepath} - Unknown format, skipping")
                self.error_files.append((filepath, "Unknown JSON format"))
                return False
            
            # Extract metadata
            metadata = data.get('metadata', {})
            
            # Extract the data array from various possible keys
            extracted_data = None
            data_key = None
            
            # Try different possible array keys
            possible_keys = [
                'abilities', 'virtues', 'flaws', 'houses', 'mechanics',
                'techniques', 'forms', 'arts', 'spells', 'guidelines',
                'data', 'items', 'entries', 'content'
            ]
            
            for key in possible_keys:
                if key in data and isinstance(data[key], list):
                    extracted_data = data[key]
                    data_key = key
                    break
            
            if extracted_data is None:
                print(f"❌ {filepath} - No array data found")
                self.error_files.append((filepath, "No array data found"))
                return False
            
            # Create metadata file if metadata exists
            if metadata:
                metadata_filepath = self._get_metadata_filepath(filepath)
                
                # Enhanced metadata with extraction info
                enhanced_metadata = {
                    **metadata,
                    "extraction_info": {
                        "original_file": os.path.basename(filepath),
                        "extracted_array": data_key,
                        "item_count": len(extracted_data),
                        "extracted_on": datetime.datetime.now().isoformat(),
                        "script_version": "1.0"
                    }
                }
                
                # Write metadata file
                with open(metadata_filepath, 'w', encoding='utf-8') as f:
                    json.dump(enhanced_metadata, f, indent=2, ensure_ascii=False)
                
                print(f"📝 {metadata_filepath} - Created metadata file")
                self.metadata_files.append(metadata_filepath)
            
            # Write the simple array back to the original file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(extracted_data, f, indent=2, ensure_ascii=False)
            
            print(f"🔧 {filepath} - Converted to array ({len(extracted_data)} items)")
            self.converted_files.append((filepath, data_key, len(extracted_data), bool(metadata)))
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ {filepath} - JSON parsing error: {e}")
            self.error_files.append((filepath, f"JSON parsing error: {e}"))
            return False
        except Exception as e:
            print(f"❌ {filepath} - Error: {e}")
            self.error_files.append((filepath, str(e)))
            return False

    def _get_metadata_filepath(self, original_filepath):
        """Generate metadata filename."""
        path = Path(original_filepath)
        return str(path.parent / f"{path.stem}.metadata.json")

    def create_readme(self, directory='.'):
        """Create a README explaining the metadata system."""
        readme_path = os.path.join(directory, "METADATA_README.md")
        
        readme_content = """# Metadata System

This directory uses extracted metadata files to preserve documentation while keeping JSON files as simple arrays.

## File Structure

- `filename.json` - Contains the actual data as a simple array
- `filename.metadata.json` - Contains metadata about the file (title, description, version, etc.)

## Example

**academic_abilities.json:**
```json
[
  {
    "name": "Artes Liberales",
    "category": "Academic",
    "description": "The seven liberal arts..."
  }
]
```

**academic_abilities.metadata.json:**
```json
{
  "title": "Academic Abilities",
  "description": "Scholarly abilities requiring formal education",
  "version": "1.0",
  "source": "Ars Magica 5th Edition",
  "last_updated": "2025-06-13",
  "extraction_info": {
    "original_file": "academic_abilities.json",
    "extracted_array": "abilities",
    "item_count": 6,
    "extracted_on": "2025-06-18T14:30:22",
    "script_version": "1.0"
  }
}
```

## Usage

- The main JSON files are used by applications (Rules Database, etc.)
- The metadata files provide documentation and versioning information
- Both files should be kept in sync when making updates

## Restoration

To restore the original format with embedded metadata, use the restoration script:
```bash
python json_metadata_restorer.py
```
"""
        
        try:
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            print(f"📖 {readme_path} - Created documentation")
            return readme_path
        except Exception as e:
            print(f"❌ Failed to create README: {e}")
            return None

    def extract_directory(self, directory='.', pattern='*.json'):
        """Extract metadata from all JSON files in directory."""
        print(f"🔍 Scanning {directory} for {pattern} files to process...")
        
        # Find all matching files, excluding metadata files
        if directory == '.':
            files = glob.glob(pattern, recursive=True)
            files.extend(glob.glob(f"**/{pattern}", recursive=True))
        else:
            files = glob.glob(os.path.join(directory, pattern), recursive=True)
            files.extend(glob.glob(os.path.join(directory, f"**/{pattern}"), recursive=True))
        
        # Filter out metadata files
        files = [f for f in files if not f.endswith('.metadata.json')]
        
        if not files:
            print(f"❌ No {pattern} files found in {directory}")
            return
        
        print(f"📁 Found {len(files)} files to check")
        
        # Process each file
        for filepath in sorted(files):
            self.extract_metadata(filepath)
        
        # Create documentation
        if self.converted_files or self.metadata_files:
            self.create_readme(directory)
        
        # Validate converted files
        if self.converted_files:
            print(f"\n🔍 Validating converted files...")
            for filepath, _, _, _ in self.converted_files:
                self.validate_json(filepath)
        
        # Summary
        print(f"\n📊 Summary:")
        print(f"   ✅ Converted: {len(self.converted_files)} files")
        print(f"   📝 Metadata files: {len(self.metadata_files)} files")
        print(f"   ⏭️  Skipped: {len(self.skipped_files)} files (already arrays)")
        print(f"   ❌ Errors: {len(self.error_files)} files")
        
        if self.converted_files:
            print(f"\n📝 Converted files:")
            for filepath, data_key, count, had_metadata in self.converted_files:
                metadata_info = " (metadata extracted)" if had_metadata else " (no metadata)"
                print(f"   - {filepath}: {count} items from '{data_key}'{metadata_info}")
        
        if self.error_files:
            print(f"\n❌ Error files:")
            for filepath, error in self.error_files:
                print(f"   - {filepath}: {error}")

    def validate_json(self, filepath):
        """Validate that the converted JSON is syntactically correct."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                print(f"✅ {filepath} - Valid array with {len(data)} items")
                return True
            else:
                print(f"⚠️  {filepath} - Valid JSON but not an array")
                return False
        except json.JSONDecodeError as e:
            print(f"❌ {filepath} - JSON validation failed: {e}")
            return False
        except Exception as e:
            print(f"❌ {filepath} - Validation error: {e}")
            return False

    def create_backup(self, directory='.'):
        """Create backup of files before extracting."""
        import shutil
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"backup_before_metadata_extraction_{timestamp}"
        
        print(f"💾 Creating backup in {backup_dir}...")
        
        try:
            os.makedirs(backup_dir, exist_ok=True)
            
            # Copy all JSON files to backup
            json_files = glob.glob("*.json", recursive=True)
            json_files.extend(glob.glob("**/*.json", recursive=True))
            
            backed_up = 0
            for filepath in json_files:
                if not filepath.endswith('.metadata.json'):
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        # Only backup files that aren't already arrays
                        if not isinstance(data, list):
                            dest_path = os.path.join(backup_dir, os.path.basename(filepath))
                            # Handle duplicate filenames
                            counter = 1
                            while os.path.exists(dest_path):
                                name, ext = os.path.splitext(os.path.basename(filepath))
                                dest_path = os.path.join(backup_dir, f"{name}_{counter}{ext}")
                                counter += 1
                            
                            shutil.copy2(filepath, dest_path)
                            print(f"   📋 Backed up: {filepath}")
                            backed_up += 1
                    except:
                        pass  # Skip files that can't be read
            
            if backed_up > 0:
                print(f"✅ Backup created successfully ({backed_up} files)")
                return backup_dir
            else:
                print(f"ℹ️  No files needed backup (all are already arrays)")
                os.rmdir(backup_dir)  # Remove empty backup dir
                return None
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return None

    def create_restorer_script(self, directory='.'):
        """Create a script to restore the original format."""
        script_path = os.path.join(directory, "json_metadata_restorer.py")
        
        script_content = '''#!/usr/bin/env python3
"""
JSON Metadata Restorer
Restores JSON files by merging arrays with their metadata files.
"""

import os
import json
import glob

def restore_file(json_file):
    """Restore a JSON file by merging with its metadata."""
    metadata_file = json_file.replace('.json', '.metadata.json')
    
    if not os.path.exists(metadata_file):
        print(f"⏭️  {json_file} - No metadata file found, skipping")
        return False
    
    try:
        # Read array data
        with open(json_file, 'r', encoding='utf-8') as f:
            array_data = json.load(f)
        
        # Read metadata
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Remove extraction_info if present
        if 'extraction_info' in metadata:
            extraction_info = metadata.pop('extraction_info')
            data_key = extraction_info.get('extracted_array', 'data')
        else:
            data_key = 'data'
        
        # Create restored format
        restored_data = {
            'metadata': metadata,
            data_key: array_data
        }
        
        # Write restored file
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(restored_data, f, indent=2, ensure_ascii=False)
        
        print(f"🔧 {json_file} - Restored with metadata")
        return True
        
    except Exception as e:
        print(f"❌ {json_file} - Error: {e}")
        return False

def main():
    print("🔄 JSON Metadata Restorer")
    print("=" * 50)
    
    json_files = glob.glob("*.json")
    json_files = [f for f in json_files if not f.endswith('.metadata.json')]
    
    restored = 0
    for json_file in sorted(json_files):
        if restore_file(json_file):
            restored += 1
    
    print(f"\\n📊 Restored {restored} files")

if __name__ == "__main__":
    main()
'''
        
        try:
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            os.chmod(script_path, 0o755)  # Make executable
            print(f"🔄 {script_path} - Created restoration script")
            return script_path
        except Exception as e:
            print(f"❌ Failed to create restorer script: {e}")
            return None

def main():
    extractor = JSONMetadataExtractor()
    
    print("📝 JSON Metadata Extractor")
    print("=" * 50)
    
    # Parse command line arguments
    if len(sys.argv) > 1 and (sys.argv[1] == '--help' or sys.argv[1] == '-h'):
        print("Usage:")
        print("  python json_metadata_extractor.py [options] [directory]")
        print("")
        print("Options:")
        print("  --backup    Create backup before extracting (default)")
        print("  --no-backup Skip backup creation")
        print("  --pattern   File pattern to match (default: *.json)")
        print("")
        print("What this does:")
        print("  1. Extracts metadata from JSON files to separate .metadata.json files")
        print("  2. Converts main JSON files to simple arrays")
        print("  3. Creates documentation and restoration script")
        print("")
        print("Examples:")
        print("  python json_metadata_extractor.py")
        print("  python json_metadata_extractor.py --no-backup")
        print("  python json_metadata_extractor.py ./data")
        return
    
    # Parse arguments
    create_backup = '--no-backup' not in sys.argv
    pattern = '*.json'
    directory = '.'
    
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == '--pattern' and i + 1 < len(sys.argv):
            pattern = sys.argv[i + 1]
        elif arg.startswith('/') or arg.startswith('./') or os.path.isdir(arg):
            directory = arg
    
    # Create backup if requested
    backup_dir = None
    if create_backup:
        backup_dir = extractor.create_backup(directory)
        if backup_dir:
            print(f"💡 Tip: If something goes wrong, restore from {backup_dir}\n")
    
    # Extract metadata
    extractor.extract_directory(directory, pattern)
    
    # Create restoration script
    if extractor.converted_files:
        extractor.create_restorer_script(directory)
    
    # Suggest next steps
    if extractor.converted_files:
        print(f"\n🚀 Next steps:")
        print(f"   1. Test your Rules Database to make sure it loads correctly")
        print(f"   2. Review the .metadata.json files to ensure they look right")
        print(f"   3. Read METADATA_README.md for documentation")
        print(f"   4. If everything works, commit the changes:")
        print(f"      git add .")
        print(f"      git commit -m 'Extracted metadata to separate files'")
        print(f"      git push origin main")
        print(f"   5. To restore original format: python json_metadata_restorer.py")

if __name__ == "__main__":
    main()