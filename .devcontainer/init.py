"""
Initialize container with modules used by volkswage_we_connect_id component
"""

import json
import pip

PIP_ARGUMENTS = ["install", "--user", "homeassistant", "black"]
MANIFEST_PATH = "custom_components/aguaiot/manifest.json"

with open(MANIFEST_PATH, "r", encoding="utf8") as MANIFEST_FILE:
    MANIFEST = json.load(MANIFEST_FILE)
    REQUIREMENTS: list[str] = MANIFEST["requirements"]

pip.main(PIP_ARGUMENTS + REQUIREMENTS)
