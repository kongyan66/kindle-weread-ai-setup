#!/usr/bin/env python3
"""Download a pinned official SpringBreak ZIP, verify it, and never execute it."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    metadata = json.loads((Path(__file__).resolve().parents[1] / "sources.json").read_text(encoding="utf-8"))["springbreak"]
    target = Path(args.out).resolve()
    if target.exists():
        raise ValueError("Destination already exists; verify or choose a new filename")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        checksum = hashlib.sha256()
        request = urllib.request.Request(metadata["url"], headers={"User-Agent": "kindle-weread-ai-setup/1.0"})
        with urllib.request.urlopen(request, timeout=60) as response, tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
            temporary = Path(stream.name)
            total = 0
            for chunk in iter(lambda: response.read(1024 * 1024), b""):
                total += len(chunk)
                if total > 100 * 1024 * 1024:
                    raise ValueError("Download exceeded size limit")
                checksum.update(chunk)
                stream.write(chunk)
        if checksum.hexdigest() != metadata["sha256"]:
            raise ValueError("Official archive SHA-256 mismatch; do not run it")
        temporary.replace(target)
        print(json.dumps({"version": metadata["version"], "path": str(target), "sha256": checksum.hexdigest(), "executed": False}, indent=2))
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("ERROR: " + str(error), file=sys.stderr)
        raise SystemExit(1)
