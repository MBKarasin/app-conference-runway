const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const scope = {window: {}};
vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../site/assets/daily-status.js'), 'utf8'), scope);
const status = scope.window.runwayDailyStatus;
const now = new Date('2026-10-20T12:00:00Z');
const run = {status: 'success', started_at: '2026-10-20T06:00:00Z',
  completed_at: '2026-10-20T06:20:00Z', sources_checked_at: '2026-10-20T06:19:00Z', published_at: null};
assert.equal(status(run, now).tone, 'ok', 'live validated status needs no fabricated publication receipt');
assert.equal(status({...run, completed_at: null}, now).tone, 'warn');
assert.equal(status({...run, status: 'issues'}, now).tone, 'warn');
assert.equal(status({...run, status: 'running'}, now).tone, 'warn');
assert.equal(status({...run, started_at: '2026-10-18T06:00:00Z'}, now).tone, 'bad');
assert.equal(status(null, now).tone, 'bad');
console.log('Daily status regression checks passed');
