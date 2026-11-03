"""Reproduce the nightly no-quote failure without inventing organizer evidence."""
import datetime as dt
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
IDENTITY = "ba1fd203973c"


class UnsupportedFCCSTest(unittest.TestCase):
    def test_unsupported_edition_is_withheld_without_erasing_history(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for folder in ("scripts", "sources", "data", "site"):
                shutil.copytree(ROOT / folder, root / folder)
            for document in ROOT.glob("*.md"):
                shutil.copy2(document, root / document.name)
            override_path = root / "sources/overrides.json"
            overrides = json.loads(override_path.read_text(encoding="utf-8"))
            disposition = overrides["editions"].pop(IDENTITY)
            # Move only this unsupported fixture into the future. Rewinding the
            # entire catalog resurrects ended records whose archived checks no
            # longer contain snippets, blocking unrelated nightly publication.
            today = dt.datetime.now(ZoneInfo("America/New_York")).date()
            start = (today + dt.timedelta(days=1)).isoformat()
            end = (today + dt.timedelta(days=2)).isoformat()
            overrides["editions"][IDENTITY] = {"start": start, "end": end}
            override_path.write_text(json.dumps(overrides), encoding="utf-8")
            verification_path = root / "data/verification.json"
            verification = json.loads(verification_path.read_text(encoding="utf-8"))
            verification[IDENTITY] = {
                "state": "not_found", "checked": "2026-10-20T10:34:19Z",
                "url": "https://sccm.org/education-center/conference-calendar",
                "why": "No matching RWJUH FCCS organizer quote",
            }
            verification_path.write_text(json.dumps(verification), encoding="utf-8")
            env = {**os.environ, "RUNWAY_TODAY": today.isoformat()}
            run = lambda script: subprocess.run(
                [sys.executable, str(root / "scripts" / script)], capture_output=True, text=True, env=env)
            self.assertEqual(run("build.py").returncode, 0)
            gate = run("validate.py")
            self.assertNotEqual(gate.returncode, 0)
            self.assertIn(f"{start}: upcoming record has no evidence quote", gate.stdout + gate.stderr)
            ledger_path = root / "data/ledger.json"
            retained = json.loads(ledger_path.read_text(encoding="utf-8"))[IDENTITY]
            self.assertIsNone(retained["edition"]["evidence"])
            overrides["editions"][IDENTITY] = disposition
            override_path.write_text(json.dumps(overrides), encoding="utf-8")
            self.assertEqual(run("build.py").returncode, 0)
            gate = run("validate.py")
            self.assertEqual(gate.returncode, 0, gate.stdout + gate.stderr)
            public = json.loads((root / "site/data/runway.json").read_text(encoding="utf-8"))
            self.assertNotIn(IDENTITY, {e["id"] for e in public["editions"]})
            self.assertEqual(json.loads(ledger_path.read_text(encoding="utf-8"))[IDENTITY], retained)
            self.assertNotIn("UID:" + IDENTITY + "@app-conference-runway",
                             (root / "site/runway.ics").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
