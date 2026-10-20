/* Status of the nightly update (GitHub Actions, scheduled 4 a.m. America/New_York; GitHub may start it a few hours late).
   Red when the latest recorded run started more than 30 hours ago. Independent of the data-quality indices. */
window.runwayDailyStatus = function (run, now) {
  const started = run && run.started_at && new Date(run.started_at);
  if (!started || !Number.isFinite(started.getTime())) return { tone: 'bad', label: 'Daily update has not run', detail: 'No nightly update is recorded.' };
  const hours = ((now || new Date()) - started) / 36e5;
  if (hours > 30) return { tone: 'bad', label: 'Daily update overdue', detail: 'The latest nightly update started more than 30 hours ago.' };
  if (run.status === 'success' && run.completed_at && run.sources_checked_at) return { tone: 'ok', label: 'Daily update successful', detail: 'The nightly source check and validation completed. This status accompanies the site you are viewing.' };
  return { tone: 'warn', label: run.status === 'running' ? 'Daily update in progress' : 'Daily update needs attention', detail: run.status === 'running' ? 'The nightly update started and has not yet completed.' : 'The nightly update ran, but checking or validation reported an issue.' };
};
