"""
ClaimForge: Project Packaging Utility for Clean Deployment Uploads
===================================================================
Packages the entire project into a clean, lightweight deployment zip file,
automatically excluding OS-dependent virtual environments, node_modules,
build caches, and local databases.
"""

import os
import zipfile
from pathlib import Path

# Directories to exclude completely
EXCLUDE_DIRS = {
    'venv',
    '.venv',
    'env',
    'ENV',
    'node_modules',
    '.next',
    '__pycache__',
    '.pytest_cache',
    '.git',
    '.vscode',
    '.idea',
}

# File extensions or patterns to exclude
EXCLUDE_EXTS = {
    '.pyc',
    '.pyo',
    '.pyd',
    '.tsbuildinfo',
    '.log',
    '.db',
    '.db-journal',
    '.sqlite3',
    '.zip'
}

def should_exclude(rel_path: Path) -> bool:
    parts = rel_path.parts
    # Check if any parent dir is in exclusion list
    for part in parts:
        if part in EXCLUDE_DIRS:
            return True
    
    # Check file extension
    if rel_path.suffix.lower() in EXCLUDE_EXTS:
        return True
        
    return False

def package_project(output_filename: str = "claimforge_deployment.zip"):
    root_dir = Path(__file__).resolve().parent
    output_path = root_dir / output_filename
    
    print(f"Creating clean deployment package: {output_filename}...")
    file_count = 0
    total_bytes = 0
    
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for foldername, subfolders, filenames in os.walk(root_dir):
            current_path = Path(foldername)
            
            # Prune excluded directories in-place so os.walk does not recurse into them
            subfolders[:] = [d for d in subfolders if d not in EXCLUDE_DIRS]
            
            for filename in filenames:
                file_path = current_path / filename
                rel_path = file_path.relative_to(root_dir)
                
                if should_exclude(rel_path) or file_path == output_path:
                    continue
                
                zipf.write(file_path, arcname=str(rel_path).replace("\\", "/"))
                file_count += 1
                total_bytes += file_path.stat().st_size
                
    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"[SUCCESS] Packaged {file_count} files ({total_bytes / (1024 * 1024):.2f} MB uncompressed).")
    print(f"[READY] Output Archive: {output_path.name} ({size_mb:.2f} MB)")
    print(f"        Ready for upload to any deployment platform or cloud server.")

if __name__ == "__main__":
    package_project()
