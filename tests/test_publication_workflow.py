"""Exercise the workflow's actual embedded status writer without network or Actions."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

WORKFLOW = Path(__file__).resolve().parents[1] / '.github/workflows/runway.yml'

class PublicationWorkflowTests(unittest.TestCase):
    def test_status_writer_preserves_failed_live_stamp_and_records_advisories(self):
        text = WORKFLOW.read_text(encoding='utf-8')
        marker = "          python - <<'PY'\n"
        script = text.split(marker, 1)[1].split('\n          PY', 1)[0]
        script = '\n'.join(line[10:] for line in script.splitlines())
        for outcome in ('success', 'failure', 'skipped'):
            with self.subTest(outcome=outcome), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / 'site/data').mkdir(parents=True)
                (root / 'data').mkdir()
                (root / 'site/data/runway.json').write_text(json.dumps({'sources_checked': 'previous-read'}))
                stamp = root / 'site/data/update-status.json'
                stamp.write_text('{"status":"failure","started_at":"old-failure"}')
                old = stamp.read_bytes()
                env = dict(os.environ, RUN_STARTED='current-attempt', VALIDATE_OUTCOME=outcome,
                           SOURCES_OUTCOME='failure', LINKS_OUTCOME='success', READERS_OUTCOME='failure')
                subprocess.run([sys.executable, '-c', script], cwd=root, env=env, check=True)
                diagnostic = json.loads((root / 'data/run-status.json').read_text())
                self.assertIsNone(diagnostic['published_at'])
                self.assertEqual(diagnostic['outcomes']['readers'], 'failure')
                self.assertEqual(diagnostic['outcomes']['sources'], 'failure')
                if outcome == 'success':
                    self.assertEqual(json.loads(stamp.read_text())['status'], 'issues')
                    env['SOURCES_OUTCOME'] = 'success'
                    subprocess.run([sys.executable, '-c', script], cwd=root, env=env, check=True)
                    self.assertEqual(json.loads(stamp.read_text())['status'], 'success')
                else:
                    self.assertEqual(stamp.read_bytes(), old)
                    self.assertEqual(diagnostic['status'], 'failure')

    def test_only_validated_same_run_artifacts_reach_deploy(self):
        text = WORKFLOW.read_text(encoding='utf-8')
        check, rest = text.split('\n  rebuild:', 1)
        rebuild, deploy = rest.split('\n  deploy:', 1)
        self.assertEqual(text.count('run: node tests/test_daily_status.js'), 2)
        self.assertNotIn('checkout@', deploy)
        self.assertNotIn('upload-pages-artifact@', deploy)
        self.assertIn("if: success() && steps.validate.outcome == 'success'", check)
        self.assertIn('if [ "$VALIDATE_OUTCOME" = success ]; then git add site; fi', check)
        self.assertIn('git add data', check)
        self.assertIn("if: always() && steps.validate.outcome != 'success'", check)
        self.assertLess(rebuild.index('python scripts/validate.py'), rebuild.index('upload-pages-artifact@'))
        self.assertNotIn('workflow_dispatch:', text.split('jobs:', 1)[1])
        for script in ('check.py', 'linkcheck.py'):
            self.assertNotIn(f'{script} &&', check)

if __name__ == '__main__':
    unittest.main()
