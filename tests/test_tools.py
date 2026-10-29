import importlib.util
import json
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("kindle_tools", ROOT / "skills/kindle-weread-setup/scripts/kindle_tools.py")
tools = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tools)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        fixture_root = ROOT / "tests/.tmp"
        fixture_root.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=fixture_root)
        self.base = Path(self.temp.name)
        self.device = self.base / "Kindle"
        (self.device / "documents").mkdir(parents=True)
        (self.device / "system").mkdir()
        (self.device / "documents/我的书.txt").write_text("personal book", encoding="utf-8")
        (self.device / ".hidden").write_bytes(b"hidden data")
        (self.device / "System Volume Information").mkdir()
        (self.device / "System Volume Information/skip").write_bytes(b"skip")
        self.archive = self.base / "app.zip"
        self.make_zip()
        self.backup = self.base / "backup"

    def tearDown(self):
        self.assertTrue(self.base.resolve().is_relative_to((ROOT / "tests/.tmp").resolve()))
        self.temp.cleanup()

    def make_zip(self, extras=None):
        with zipfile.ZipFile(self.archive, "w") as archive:
            archive.writestr("weread/start.sh", "#!/bin/sh\necho app\n")
            archive.writestr("documents/微信读书.sh", "#!/bin/sh\nsh /mnt/us/weread/start.sh\n")
            archive.writestr("fonts/example.ttf", b"fixture-font-not-a-real-font")
            archive.writestr("安装说明.md", "Fixture documentation")
            archive.writestr("__MACOSX/._file", b"metadata")
            archive.writestr("weread/.DS_Store", b"metadata")
            for name, data in (extras or {}).items():
                info = zipfile.ZipInfo("fixture")
                info.filename = name
                archive.writestr(info, data)

    def test_backup_hidden_files_verified_and_corruption_detected(self):
        result = tools.backup(self.device, self.backup)
        self.assertEqual(result["files"], 2)
        manifest = tools.verify_backup(self.backup)
        self.assertFalse(manifest["full_system_image"])
        (self.backup / "files/.hidden").write_bytes(b"tampered")
        with self.assertRaises(ValueError):
            tools.verify_backup(self.backup)

    def test_preview_does_not_write_and_apply_preserves_books(self):
        preview = tools.install(self.device, self.archive)
        self.assertEqual(preview["files"], 3)
        self.assertFalse((self.device / "weread").exists())
        tools.backup(self.device, self.backup)
        result = tools.install(self.device, self.archive, self.backup, self.base / "record", apply=True)
        self.assertTrue(result["verified"])
        self.assertFalse(result["runtime_verified"])
        self.assertEqual((self.device / "documents/我的书.txt").read_text(encoding="utf-8"), "personal book")
        self.assertFalse((self.device / "weread/.DS_Store").exists())
        self.assertEqual((self.device / "documents/微信读书.sh").read_text(), "#!/bin/sh\nsh /mnt/us/weread/start.sh\n")

    def test_apply_without_verified_backup_fails_before_writes(self):
        with self.assertRaises(ValueError):
            tools.install(self.device, self.archive, apply=True)
        self.assertFalse((self.device / "weread").exists())

    def test_update_requires_flag_and_saves_current_target(self):
        (self.device / "weread").mkdir()
        old = self.device / "weread/start.sh"
        old.write_bytes(b"old version")
        tools.backup(self.device, self.backup)
        with self.assertRaises(ValueError):
            tools.install(self.device, self.archive, self.backup, self.base / "refused", apply=True)
        self.assertEqual(old.read_bytes(), b"old version")
        tools.install(self.device, self.archive, self.backup, self.base / "update", apply=True, allow_update=True)
        self.assertEqual((self.base / "update/previous/weread/start.sh").read_bytes(), b"old version")

    def test_zip_escape_case_collision_and_symlink_rejected(self):
        for name in ("../outside.txt", "/absolute.txt", "weread/../escape", "weread\\escape", "weread/CON.txt", "weread/Start.sh"):
            with self.subTest(name=name):
                self.make_zip({name: b"bad"})
                with self.assertRaises(ValueError):
                    tools.package_files(self.archive)
        self.make_zip()
        with zipfile.ZipFile(self.archive, "a") as archive:
            info = zipfile.ZipInfo("weread/link")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(info, "../../outside")
        with self.assertRaises(ValueError):
            tools.package_files(self.archive)

    def test_mid_install_failure_rolls_back_new_files(self):
        tools.backup(self.device, self.backup)
        original_copy = tools.copy_member
        calls = []

        def failing_copy(package, row, target):
            calls.append(row["path"])
            if len(calls) == 2:
                raise OSError("simulated USB disconnect")
            original_copy(package, row, target)

        with patch.object(tools, "copy_member", failing_copy):
            with self.assertRaises(OSError):
                tools.install(self.device, self.archive, self.backup, self.base / "failed", apply=True)
        self.assertFalse((self.device / "weread/start.sh").exists())
        self.assertTrue((self.device / "documents/我的书.txt").exists())

    def test_deep_jailbreak_tree_not_backed_up(self):
        (self.device / ".active_content_sandbox/store/resource/cachedResources/1").mkdir(parents=True)
        with self.assertRaises(ValueError):
            tools.backup(self.device, self.backup)
        self.assertFalse(self.backup.exists())

    def test_backup_and_device_cannot_overlap(self):
        with self.assertRaises(ValueError):
            tools.backup(self.device, self.device / "backup")

    def test_other_mount_backup_rejected(self):
        tools.backup(self.device, self.backup)
        manifest_path = self.backup / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["device_root"] = str(self.base / "other-device")
        tools.write_json(manifest_path, manifest)
        with self.assertRaises(ValueError):
            tools.install(self.device, self.archive, self.backup, self.base / "record", apply=True)


if __name__ == "__main__":
    unittest.main()
