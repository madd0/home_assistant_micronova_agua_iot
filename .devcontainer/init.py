"""
Initialize container with modules used by aguaiot component
"""

import json
import os
import subprocess
import sys

# Install system dependencies
print("Installing system dependencies...")
try:
    subprocess.check_call(["sudo", "apt-get", "update"])
    subprocess.check_call([
        "sudo", "apt-get", "install", "-y",
        "libpcap-dev",
        "ffmpeg",
        "libturbojpeg0-dev",
        "libyaml-dev",
        "pkg-config",
        "libavformat-dev",
        "libavcodec-dev",
        "libavdevice-dev",
        "libavutil-dev",
        "libswscale-dev",
        "libswresample-dev",
        "libavfilter-dev"
    ])
except subprocess.CalledProcessError as e:
    print(f"Failed to install system dependencies: {e}")
    # Continue anyway, maybe some are already installed or not needed for basic run

# Install requirements
PIP_ARGUMENTS = [sys.executable, "-m", "pip", "install", "--user", "homeassistant", "black"]
MANIFEST_PATH = "custom_components/aguaiot/manifest.json"


if os.path.exists(MANIFEST_PATH):
    with open(MANIFEST_PATH, "r", encoding="utf8") as MANIFEST_FILE:
        MANIFEST = json.load(MANIFEST_FILE)
        REQUIREMENTS: list[str] = MANIFEST.get("requirements", [])

    if REQUIREMENTS:
        print(f"Installing requirements: {REQUIREMENTS}")
        subprocess.check_call(PIP_ARGUMENTS + REQUIREMENTS)
    
    # Always install homeassistant
    subprocess.check_call(PIP_ARGUMENTS)

else:
    print(f"Manifest not found at {MANIFEST_PATH}")
    # Still install homeassistant
    subprocess.check_call(PIP_ARGUMENTS)
