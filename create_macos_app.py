#!/usr/bin/env python3
"""
WhisperLocal macOS App Creator
Creates a native-looking macOS app bundle without Xcode
"""

import os
import sys
import shutil
import json
from pathlib import Path

def create_app_bundle():
    """Create a macOS .app bundle from Python components"""
    
    print("🚀 Creating WhisperLocal macOS App...")
    
    # Paths
    project_root = Path.cwd()
    app_name = "WhisperLocal.app"
    app_path = project_root / app_name
    
    # Clean existing app
    if app_path.exists():
        shutil.rmtree(app_path)
        print(f"✅ Removed existing {app_name}")
    
    # Create app bundle structure
    contents = app_path / "Contents"
    macos_dir = contents / "MacOS"
    resources = contents / "Resources"
    
    macos_dir.mkdir(parents=True)
    resources.mkdir(parents=True)
    
    print("✅ Created app bundle structure")
    
    # Create Info.plist
    info_plist = {
        "CFBundleDisplayName": "Whisper Local",
        "CFBundleExecutable": "whisper_local",
        "CFBundleIconFile": "AppIcon",
        "CFBundleIdentifier": "com.github.cubetribe.whisper-transcription-tool",
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundleName": "WhisperLocal",
        "CFBundlePackageType": "APPL",
        "CFBundleShortVersionString": "0.9.7",
        "CFBundleVersion": "1",
        "LSApplicationCategoryType": "public.app-category.productivity",
        "LSMinimumSystemVersion": "12.0",
        "NSHighResolutionCapable": True,
        "NSRequiresAquaSystemAppearance": False
    }
    
    with open(contents / "Info.plist", "w") as f:
        # Convert to plist format (simplified)
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n')
        f.write('<plist version="1.0">\n<dict>\n')
        for key, value in info_plist.items():
            f.write(f'\t<key>{key}</key>\n')
            if isinstance(value, bool):
                f.write(f'\t<{"true" if value else "false"}/>\n')
            else:
                f.write(f'\t<string>{value}</string>\n')
        f.write('</dict>\n</plist>\n')
    
    print("✅ Created Info.plist")
    
    # Create executable script
    executable_content = f'''#!/bin/bash
# WhisperLocal macOS App Launcher
cd "$(dirname "$0")"/../Resources
export PATH="$PWD/venv_new/bin:$PATH"
python3 -m src.whisper_transcription_tool.main web --port 8090 &
sleep 2
open "http://localhost:8090"
wait
'''
    
    executable_path = macos_dir / "whisper_local"
    with open(executable_path, "w") as f:
        f.write(executable_content)
    
    # Make executable
    os.chmod(executable_path, 0o755)
    print("✅ Created executable launcher")
    
    # Copy Python source
    src_dest = resources / "src"
    if (project_root / "src").exists():
        shutil.copytree(project_root / "src", src_dest)
        print("✅ Copied Python source")
    
    # Copy virtual environment
    venv_src = project_root / "venv_new"
    if venv_src.exists():
        shutil.copytree(venv_src, resources / "venv_new")
        print("✅ Copied virtual environment")
    
    # Copy other required files
    for item in ["models", "deps", "requirements.txt", "macos_cli.py"]:
        src_path = project_root / item
        if src_path.exists():
            if src_path.is_dir():
                shutil.copytree(src_path, resources / item)
            else:
                shutil.copy2(src_path, resources / item)
            print(f"✅ Copied {item}")
    
    print(f"\n🎉 WhisperLocal.app created successfully!")
    print(f"📍 Location: {app_path}")
    print(f"🚀 Double-click to run the app")
    
    return app_path

if __name__ == "__main__":
    create_app_bundle()