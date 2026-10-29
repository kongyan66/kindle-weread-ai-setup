#!/usr/bin/env python3
"""Verified USB backups and preview-first WeRead file installation. Python 3.10+."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import sys
import tempfile
import zipfile

ROOTS = {"documents", "extensions", "fonts", "weread"}
MAX_PAYLOAD = 1024 * 1024 * 1024


def digest(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def inside(path, root):
    return path == root or root in path.parents


def is_link(path):
    if path.is_symlink():
        return True
    if path.exists():
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
        return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
    return False


def safe_relative(name):
    if not name or "\\" in name or "\x00" in name:
        raise ValueError("Invalid archive path")
    raw = name.rstrip("/")
    parts = raw.split("/")
    if any(part in ("", ".", "..") or ":" in part for part in parts):
        raise ValueError("Unsafe relative path: " + name)
    if PurePosixPath(raw).is_absolute():
        raise ValueError("Absolute archive path")
    for part in parts:
        if part.endswith((" ", ".")) or any(ord(char) < 32 or char in '<>"|?*' for char in part):
            raise ValueError("Non-portable file name: " + name)
        if part.split(".")[0].upper() in {"CON", "PRN", "AUX", "NUL", *["COM" + str(i) for i in range(1, 10)], *["LPT" + str(i) for i in range(1, 10)]}:
            raise ValueError("Reserved file name: " + name)
    return Path(*parts)


def device_root(value):
    supplied = Path(value).absolute()
    if is_link(supplied) or not supplied.is_dir():
        raise ValueError("Device must be an existing non-symlink directory")
    root = supplied.resolve()
    if not (root / "documents").is_dir() or not (root / "system").is_dir():
        raise ValueError("Expected Kindle documents and system directories; verify device identity")
    return root


def target_path(root, relative):
    target = root / relative
    current = target
    while current != root:
        if is_link(current):
            raise ValueError("Refusing a symlink path: " + str(relative))
        current = current.parent
    if not inside(target.resolve(), root):
        raise ValueError("Path escapes device root")
    return target


def device_files(root):
    pending = [root]
    while pending:
        folder = pending.pop()
        for item in sorted(folder.iterdir()):
            if folder == root and item.name == "System Volume Information":
                continue
            if is_link(item):
                raise ValueError("Refusing symlink during backup: " + str(item.relative_to(root)))
            if item.is_dir():
                pending.append(item)
            elif item.is_file():
                yield item
            else:
                raise ValueError("Unsupported filesystem entry: " + str(item.relative_to(root)))


def backup(device, destination):
    root = device_root(device)
    out = Path(destination).resolve()
    if inside(out, root) or inside(root, out):
        raise ValueError("Backup and device directories must not overlap")
    if out.exists():
        raise ValueError("Use a new backup directory; existing backups are never overwritten")
    if (root / ".active_content_sandbox/store/resource/cachedResources/1").exists():
        raise ValueError("Jailbreak temporary tree detected; do not recurse through it")
    files = list(device_files(root))
    parent = out.parent
    parent.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(parent).free < sum(file.stat().st_size for file in files) + 16 * 1024 * 1024:
        raise ValueError("Insufficient backup space")
    out.mkdir()
    records = []
    for source in files:
        relative = source.relative_to(root)
        target = out / "files" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        before = digest(source)
        shutil.copy2(source, target)
        if digest(target) != before or digest(source) != before:
            raise ValueError("Backup changed or failed verification: " + str(relative))
        records.append({"path": relative.as_posix(), "bytes": target.stat().st_size, "sha256": before})
    manifest = {"format": 1, "complete": True, "device_root": str(root), "full_system_image": False, "excluded": ["System Volume Information"], "files": records}
    write_json(out / "manifest.json", manifest)
    return {"backup": str(out), "files": len(records), "bytes": sum(row["bytes"] for row in records), "verified": True}


def verify_backup(destination):
    out = Path(destination).resolve()
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("format") != 1 or manifest.get("complete") is not True:
        raise ValueError("Backup is not complete")
    for row in manifest["files"]:
        relative = safe_relative(row["path"])
        target = target_path(out, Path("files") / relative)
        if not target.is_file() or target.stat().st_size != row["bytes"] or digest(target) != row["sha256"]:
            raise ValueError("Backup verification failed: " + row["path"])
    return manifest


def package_files(archive):
    seen = set()
    records = []
    total = 0
    with zipfile.ZipFile(archive) as package:
        if len(package.infolist()) > 20000:
            raise ValueError("Archive has too many entries")
        for entry in package.infolist():
            safe_relative(entry.orig_filename)
            relative = safe_relative(entry.filename)
            if stat.S_ISLNK(entry.external_attr >> 16):
                raise ValueError("Archive symlink rejected")
            key = relative.as_posix().casefold()
            if key in seen:
                raise ValueError("Duplicate or case-colliding archive path: " + str(relative))
            seen.add(key)
            if relative.parts[0] not in ROOTS or entry.is_dir() or relative.name == ".DS_Store":
                continue
            total += entry.file_size
            if total > MAX_PAYLOAD or entry.flag_bits & 1:
                raise ValueError("Payload is too large or encrypted")
            checksum = hashlib.sha256()
            with package.open(entry) as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    checksum.update(chunk)
            records.append({"path": relative.as_posix(), "bytes": entry.file_size, "sha256": checksum.hexdigest()})
    paths = {row["path"] for row in records}
    if "weread/start.sh" not in paths or not any(path.startswith("documents/") and path.endswith(".sh") for path in paths):
        raise ValueError("Expected WeRead start script and document entry were not found")
    return records


def copy_member(package, row, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".weread-install-", delete=False) as stream:
            temporary = Path(stream.name)
            with package.open(row["path"]) as source:
                shutil.copyfileobj(source, stream)
        if digest(temporary) != row["sha256"]:
            raise ValueError("Installation hash mismatch: " + row["path"])
        os.replace(temporary, target)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def install(device, archive, backup_dir=None, record_dir=None, apply=False, allow_update=False):
    root = device_root(device)
    archive = Path(archive).resolve()
    rows = package_files(archive)
    for row in rows:
        target = target_path(root, safe_relative(row["path"]))
        if target.exists() and not target.is_file():
            raise ValueError("File target conflicts with a directory: " + row["path"])
        row["action"] = "unchanged" if target.is_file() and digest(target) == row["sha256"] else "replace" if target.exists() else "new"
    plan = {"mode": "apply" if apply else "preview", "files": len(rows), "bytes": sum(row["bytes"] for row in rows), "replacements": [row["path"] for row in rows if row["action"] == "replace"], "archive_sha256": digest(archive), "entries": rows}
    if not apply:
        return plan
    if not backup_dir or not record_dir:
        raise ValueError("Applying requires --backup and --record")
    baseline = verify_backup(backup_dir)
    if baseline.get("device_root") != str(root):
        raise ValueError("Backup is for a different device mount; re-identify and make a new backup")
    if plan["replacements"] and not allow_update:
        raise ValueError("Different existing files found; back up current data and explicitly use --allow-update")
    out = Path(record_dir).resolve()
    if inside(out, root) or inside(root, out) or out.exists():
        raise ValueError("Use a new off-device record directory")
    if shutil.disk_usage(root).free < plan["bytes"] + 16 * 1024 * 1024:
        raise ValueError("Insufficient device space")
    out.mkdir(parents=True)
    for row in rows:
        if row["action"] == "replace":
            source = target_path(root, safe_relative(row["path"]))
            target = out / "previous" / safe_relative(row["path"])
            target.parent.mkdir(parents=True, exist_ok=True)
            before = digest(source)
            shutil.copy2(source, target)
            if digest(target) != before or digest(source) != before:
                raise ValueError("Could not back up current target before update")
    write_json(out / "plan.json", plan)
    written = []
    try:
        with zipfile.ZipFile(archive) as package:
            for row in rows:
                if row["action"] != "unchanged":
                    target = target_path(root, safe_relative(row["path"]))
                    copy_member(package, row, target)
                    written.append(row)
                    if digest(target) != row["sha256"]:
                        raise ValueError("Post-copy verification failed")
    except Exception:
        for row in reversed(written):
            target = target_path(root, safe_relative(row["path"]))
            if digest(target) == row["sha256"]:
                if row["action"] == "replace":
                    shutil.copy2(out / "previous" / safe_relative(row["path"]), target)
                else:
                    target.unlink()
        raise
    write_json(out / "installed.json", {**plan, "verified": True})
    return {"installed_files": len(rows), "verified": True, "record": str(out), "runtime_verified": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    backup_cmd = commands.add_parser("backup")
    backup_cmd.add_argument("--device", required=True)
    backup_cmd.add_argument("--out", required=True)
    verify = commands.add_parser("verify-backup")
    verify.add_argument("--backup", required=True)
    app = commands.add_parser("install")
    for name in ("device", "package"):
        app.add_argument("--" + name, required=True)
    app.add_argument("--backup")
    app.add_argument("--record")
    app.add_argument("--apply", action="store_true")
    app.add_argument("--allow-update", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "backup":
            result = backup(args.device, args.out)
        elif args.command == "verify-backup":
            manifest = verify_backup(args.backup)
            result = {"verified": True, "files": len(manifest["files"])}
        else:
            result = install(args.device, args.package, args.backup, args.record, args.apply, args.allow_update)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        print("ERROR: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
