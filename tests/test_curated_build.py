"""Semantic regressions for curated additions and post-curation call normalization."""
import datetime as dt
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]


class CuratedBuildTest(unittest.TestCase):
    def test_curated_records_receive_current_processing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for folder in ("scripts", "sources", "data", "site"):
                shutil.copytree(ROOT / folder, root / folder)
            curated = json.loads((root / "sources/curated.json").read_text(encoding="utf-8"))
            added = curated["add"]["9e2cce1712a8"]
            geo_path = root / "sources/geo/locations.json"
            geo = json.loads(geo_path.read_text(encoding="utf-8"))
            geo[added["location"]] = {"place": "Myrtle Beach", "lat": 33.69, "lon": -78.89}
            geo_path.write_text(json.dumps(geo), encoding="utf-8")
            student_path = root / "sources/student_opportunities.json"
            students = json.loads(student_path.read_text(encoding="utf-8"))
            students["editions"][added["id"]] = {"category": "fixture", "detail": "Regression marker"}
            student_path.write_text(json.dumps(students), encoding="utf-8")
            stamp = dt.datetime.now(dt.timezone.utc).isoformat()
            verification_path = root / "data/verification.json"
            verification = json.loads(verification_path.read_text(encoding="utf-8"))
            verification[added["id"]] = {
                "url": added["source_url"], "checked": stamp,
                "last_verified": stamp, "state": "verified",
            }
            verification_path.write_text(json.dumps(verification), encoding="utf-8")
            subprocess.run([sys.executable, str(root / "scripts/build.py")], check=True, capture_output=True)
            output = json.loads((root / "site/data/runway.json").read_text(encoding="utf-8"))
            editions = {e["id"]: e for e in output["editions"]}
            current = editions[added["id"]]
            self.assertEqual(current["student"]["detail"], "Regression marker")
            self.assertTrue(current.get("machine"), "fresh machine check must reach a curated addition")
            self.assertEqual(current["start"], added["start"], "checker must preserve curated dates")
            self.assertEqual(current["verify"]["state"], "announced")
            self.assertEqual(current["verify"]["checked"], added["reviewed_on"])
            self.assertIsNotNone(current.get("geo"), "curated locations must receive geocoding")
            self.assertEqual(editions["fff7c127c15a"]["call"]["status"], "closed")
            today = dt.datetime.now(ZoneInfo("America/New_York")).date().isoformat()
            expired = [e["id"] for e in editions.values() if
                       (e.get("call") or {}).get("status") in ("open", "urgent", "soon") and
                       (e.get("call") or {}).get("closes") and e["call"]["closes"] < today]
            self.assertEqual(expired, [])
            overrides = json.loads((root / "sources/overrides.json").read_text(encoding="utf-8"))["editions"]
            for identity in ("ee76d4c7f3bf", "60b19fa7fb93", "79d298e81fa1"):
                self.assertEqual(editions[identity]["location"], overrides[identity]["location"])
                self.assertIsNotNone(editions[identity]["geo"])
            for identity in ("45504b46ea75", "6b3653108bcd", "6cfadbc4e525", "97a2b66704e8"):
                self.assertEqual(editions[identity]["call"]["text"], overrides[identity]["call"]["text"])
            self.assertEqual(editions["b9f577965d09"]["call"]["due_time"], "23:59")
            self.assertEqual(editions["c3d8a04559de"]["call"]["opens"], "2026-12-01")
            paea = [e for e in editions.values() if "paea-education-forum" in e["series"] and e["start"][:4] == "2027"]
            self.assertEqual(len(paea), 1)
            self.assertTrue(paea[0]["month_only"])
            self.assertEqual(current["check_note"]["checked"], stamp)
            self.assertNotIn("_why", current)
            self.assertNotIn("_derived_id", current)
            self.assertNotIn("attend", current, "missing current attendance must not inherit an old fee summary")

            ledger = json.loads((root / "data/ledger.json").read_text(encoding="utf-8"))
            self.assertIn(added["id"], ledger, "curated additions must enter the durable ledger")
            # A prior-source result must not confirm the curated replacement, including
            # on subsequent builds where the durable ledger already contains this ID.
            verification[added["id"]]["url"] = "https://example.org/superseded-source"
            verification_path.write_text(json.dumps(verification), encoding="utf-8")
            subprocess.run([sys.executable, str(root / "scripts/build.py")], check=True, capture_output=True)
            rebuilt = json.loads((root / "site/data/runway.json").read_text(encoding="utf-8"))
            current = next(e for e in rebuilt["editions"] if e["id"] == added["id"])
            self.assertFalse(current.get("machine", False))
            self.assertEqual(current["start"], added["start"])
            self.assertEqual(current["verify"]["state"], "announced")

            # When normal source ingestion learns the same series/date, preserve
            # the already-published ID and calendar UID rather than adding a twin.
            source_series = dict(next(s for s in rebuilt["series"] if s["id"] == added["series"]))
            source_series["editions"] = [dict(added), dict(added)]
            ledger_path = root / "data/ledger.json"
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            historical = {"series": added["series"], "edition": dict(added),
                          "first_seen": "2026-10-17T08:00:00Z", "last_seen": "2026-10-17T08:00:00Z"}
            ledger[added["_derived_id"]] = historical
            ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
            (root / "sources/group_zz_identity_fixture.json").write_text(
                json.dumps({"group": "identity-fixture", "series": [source_series]}), encoding="utf-8")
            subprocess.run([sys.executable, str(root / "scripts/build.py")], check=True, capture_output=True)
            rebuilt = json.loads((root / "site/data/runway.json").read_text(encoding="utf-8"))
            matches = [e for e in rebuilt["editions"] if (e["series"], e["start"]) == (added["series"], added["start"])]
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0]["id"], added["id"])
            retained = json.loads(ledger_path.read_text(encoding="utf-8"))
            self.assertEqual(retained[added["_derived_id"]], historical,
                             "suppressed ledger alias must remain unchanged as historical provenance")
            calendar = (root / "site/runway.ics").read_text(encoding="utf-8")
            self.assertEqual(calendar.count("UID:" + added["id"] + "@app-conference-runway"), 1)



if __name__ == "__main__":
    unittest.main()
