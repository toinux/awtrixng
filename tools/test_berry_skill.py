"""Offline tests with synthetic ZIPs; no upstream prose is stored here."""

import hashlib
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile


TOOLS = Path(__file__).resolve().parent
INSTALLER = runpy.run_path(str(TOOLS / "berry-skill.py"))
RULES = INSTALLER["SECTIONS"]
SKILL = "awtrix-berry-app"
ENTRY = (
    "---\nname: awtrix-berry-app\ndescription: Test skill\n"
    'license: PolyForm-Noncommercial-1.0.0\nmetadata:\n  author: Blueforcer\n  version: "test"\n---\n'
)


class BerrySkillTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.tools = self.root / "tools"
        self.tools.mkdir()
        for name in ("berry-skill.py", "berry-skill.md"):
            shutil.copyfile(TOOLS / name, self.tools / name)
        self.destination = self.root / ".agents" / "skills" / SKILL
        self.archive = self.root / "official.zip"

    def write_archive(self, version, *, drift=False, extra=False):
        sections = {}
        for name, headings in RULES.items():
            body = f"Fixture {version} — {name}\r\n"
            sections[name] = "".join(f"{heading}\r\n{body}\r\n" for heading in headings)
        sections["drawing"] += "```berry\r\n## Not a heading\r\n```\r\n"
        sections["voice"] = sections["voice"].rstrip()
        reference = "".join(sections.values())
        if drift:
            reference = reference.replace("### 5.2 Text", "### 5.2 Font and text")
        with ZipFile(self.archive, "w") as archive:
            archive.writestr(f"{SKILL}/SKILL.md", ENTRY + "# Upstream instructions")
            archive.writestr(f"{SKILL}/references/awtrix-api.md", reference)
            if extra:
                archive.writestr("../unexpected", "untrusted member")
        return sections

    def cli(self, action, status, message):
        result = subprocess.run(
            [sys.executable, self.tools / "berry-skill.py", action, "--archive", self.archive],
            cwd=self.root.parent,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, status, result.stdout + result.stderr)
        self.assertIn(message, result.stdout + result.stderr)

    def test_check_install_and_update(self):
        sections = self.write_archive("initial")
        self.cli("check", 1, "not installed")
        self.assertFalse(self.destination.parent.exists())
        self.cli("install", 0, "installed")
        self.cli("check", 0, "up to date")
        for name, content in sections.items():
            self.assertEqual(
                (self.destination / "references" / f"{name}.md").read_bytes(),
                content.encode(),
            )
        entry = self.destination / "SKILL.md"
        self.assertTrue(entry.read_text().startswith(ENTRY))
        mtime = entry.stat().st_mtime_ns
        self.cli("install", 0, "up to date")
        self.assertEqual(entry.stat().st_mtime_ns, mtime)

        self.write_archive("updated")
        digest = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        self.cli("check", 1, "update available")
        self.assertEqual(entry.stat().st_mtime_ns, mtime)
        self.cli("install", 0, "updated")
        self.cli("check", 0, "up to date")
        self.assertIn(digest, (self.destination / "UPSTREAM.md").read_text())
        self.assertIn("Fixture updated", (self.destination / "references" / "drawing.md").read_text())

    def test_bad_archive_keeps_existing_prototype(self):
        self.destination.mkdir(parents=True)
        prototype = self.destination / "SKILL.md"
        prototype.write_text("Previous local prototype")
        for options, message in (
            ({"drift": True}, "reference heading changed"),
            ({"extra": True}, "unexpected ZIP contents"),
        ):
            with self.subTest(options=options):
                self.write_archive("broken", **options)
                self.cli("check", 2, message)
                self.cli("install", 2, message)
                self.assertEqual(list(self.destination.iterdir()), [prototype])
                self.assertEqual(prototype.read_text(), "Previous local prototype")

    def test_failed_publish_restores_previous_skill(self):
        self.destination.mkdir(parents=True)
        prototype = self.destination / "SKILL.md"
        prototype.write_text("Previous local prototype")
        rename = Path.rename

        def fail_on_candidate(path, target):
            if path.name == "candidate":
                raise OSError("cannot publish candidate")
            return rename(path, target)

        with patch.object(Path, "rename", fail_on_candidate):
            with self.assertRaisesRegex(OSError, "cannot publish candidate"):
                INSTALLER["install"](self.destination, {"SKILL.md": b"Replacement"})
        self.assertEqual(prototype.read_text(), "Previous local prototype")


if __name__ == "__main__":
    unittest.main()
