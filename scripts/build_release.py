#!/usr/bin/env python3
"""Package only the reviewed public source allowlist, never device/user data."""
import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    "README.md", "LICENSE", ".gitignore",
    "skills/kindle-weread-setup/SKILL.md",
    "skills/kindle-weread-setup/sources.json",
    "skills/kindle-weread-setup/references/guide.md",
    "skills/kindle-weread-setup/scripts/kindle_tools.py",
    "skills/kindle-weread-setup/scripts/download_springbreak.py",
    "scripts/build_release.py", "tests/test_tools.py",
]


def build():
    out = ROOT / "dist"
    out.mkdir(exist_ok=True)
    package = out / "kindle-weread-ai-setup-v1.0.0.zip"
    with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in FILES:
            path = ROOT / name
            if path.is_symlink() or not path.is_file():
                raise ValueError("Missing or linked release source: " + name)
            archive.write(path, "kindle-weread-ai-setup/" + name)
    checksum = hashlib.sha256(package.read_bytes()).hexdigest()
    (out / "SHA256SUMS.txt").write_text(checksum + "  " + package.name + "\n", encoding="ascii")
    print(str(package))
    print("SHA256: " + checksum)
    return package


if __name__ == "__main__":
    build()
