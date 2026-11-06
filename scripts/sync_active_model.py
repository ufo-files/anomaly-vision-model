"""Sync the README badge from the same runtime status used by the app header.

Run on the trusted station controller; requires gh authentication and access to
its private status endpoint. Network failures leave the last confirmed badge.
"""
import argparse
import base64
import json
import re
import subprocess
import urllib.request
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET
from pathlib import Path


def svg(version):
    if not re.fullmatch(r"[a-f0-9]{64}", version):
        raise ValueError("Invalid active model hash")
    url = "https://img.shields.io/badge/active%20model-" + version[:12] + "-brightgreen?style=flat"
    rendered = subprocess.check_output(["curl", "--fail", "--silent", "--show-error", "--location", "--max-time", "20", "--retry", "2", url], text=True, timeout=70)
    root = ET.fromstring(rendered)
    if root.tag != "{http://www.w3.org/2000/svg}svg" or root.attrib.get("aria-label") != "active model: " + version[:12]:
        raise ValueError("Unexpected badge response")
    return re.sub(r"<title>.*?</title>", lambda _: "<title>Active model: " + escape(version) + "</title>", rendered, count=1)



def api(repo, path, payload=None):
    args = ["gh", "api", f"repos/{repo}/{path}"]
    if payload is not None:
        args += ["--method", "PUT", "--input", "-"]
    result = subprocess.run(args, input=json.dumps(payload) if payload is not None else None,
                            capture_output=True, text=True, timeout=45)
    if result.returncode:
        if payload is None and "HTTP 404" in result.stderr:
            return None
        raise RuntimeError("GitHub badge synchronization failed")
    return json.loads(result.stdout)


def update(repo, path, content, current):
    if current and base64.b64decode(current['content']).decode() == content:
        return
    payload = dict(message="Update active model badge from station runtime", branch="main",
                   content=base64.b64encode(content.encode()).decode())
    if current:
        payload['sha'] = current['sha']
    api(repo, "contents/" + path, payload)


def sync(repo, status_url, state):
    with urllib.request.urlopen(status_url, timeout=8) as response:
        version = json.load(response).get('active_model_hash')
    if not isinstance(version, str) or not re.fullmatch(r"[a-f0-9]{64}", version):
        raise ValueError("Station has not confirmed an active model")
    if state.exists() and state.read_text().strip() == version:
        return version
    readme = api(repo, 'contents/README.md')
    content = base64.b64decode(readme['content']).decode()
    line = f"[![Active model](badges/active-model.svg)](https://github.com/{repo}/releases/tag/model-{version})"
    pattern = r"^\[!\[Active model\].*$"
    if re.search(pattern, content, re.M):
        content = re.sub(pattern, lambda _: line, content, flags=re.M)
    else:
        raise ValueError("README active-model badge placeholder is missing")
    update(repo, 'badges/active-model.svg', svg(version), api(repo, 'contents/badges/active-model.svg'))
    update(repo, 'README.md', content, readme)
    state.parent.mkdir(parents=True, exist_ok=True)
    temp = state.with_suffix('.tmp')
    temp.write_text(version + "\n")
    temp.replace(state)
    return version


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', required=True)
    parser.add_argument('--status-url', required=True)
    parser.add_argument('--state', type=Path, required=True)
    args = parser.parse_args()
    print(sync(args.repo, args.status_url, args.state))
