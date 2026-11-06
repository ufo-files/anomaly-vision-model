"""Render a repository-hosted badge from published model metadata."""
import json
from pathlib import Path
import re
import sys
from xml.sax.saxutils import escape

source, destination = map(Path, sys.argv[1:])
badge = json.loads(source.read_text())
message = badge.get("message")
if (badge.get("schemaVersion") != 1 or badge.get("label") != "cropped labels"
        or not isinstance(message, str)
        or not re.fullmatch(r"(?:[0-9]{1,3}(?:,[0-9]{3})*|[0-9]+|not recorded)", message)):
    raise ValueError("Invalid published crop-count metadata")
message = escape(message)
right_width = max(90, len(message) * 8 + 16)
width = 100 + right_width
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="20" role="img" aria-label="cropped labels: {message}">
<title>cropped labels: {message}</title>
<rect width="{width}" height="20" rx="3" fill="#555"/>
<path fill="#007ec6" d="M100 0h{right_width-3}q3 0 3 3v14q0 3-3 3H100z"/>
<g fill="#fff" text-anchor="middle" font-family="Verdana,DejaVu Sans,sans-serif" font-size="11">
<text x="50" y="14">cropped labels</text><text x="{100+right_width/2:g}" y="14">{message}</text>
</g></svg>
'''
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(svg)
