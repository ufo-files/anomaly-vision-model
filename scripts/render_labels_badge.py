"""Render a repository-hosted badge from published model metadata."""
import json
from pathlib import Path
import re
import sys
from urllib.parse import quote
import subprocess
import xml.etree.ElementTree as ET

source, destination = map(Path, sys.argv[1:])
badge = json.loads(source.read_text())
message = badge.get("message")
if (badge.get("schemaVersion") != 1 or badge.get("label") != "cropped labels"
        or not isinstance(message, str)
        or not re.fullmatch(r"(?:[0-9]{1,3}(?:,[0-9]{3})*|[0-9]+|not recorded)", message)):
    raise ValueError("Invalid published crop-count metadata")
url = "https://img.shields.io/badge/cropped%20labels-" + quote(message, safe="") + "-blue?style=flat"
svg = subprocess.check_output(["curl", "--fail", "--silent", "--show-error", "--location", "--max-time", "20", "--retry", "2", url], text=True, timeout=70)
root = ET.fromstring(svg)
if root.tag != "{http://www.w3.org/2000/svg}svg" or root.attrib.get("aria-label") != "cropped labels: " + message:
    raise ValueError("Unexpected badge response")
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(svg)
