/* Status of the 4 a.m. America/New_York update, independent of data-quality indices. */
window.runwayDailyStatus = function (run, now) {
  const local = date => Object.fromEntries(new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/New_York', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', hourCycle: 'h23'
  }).formatToParts(date).filter(p => p.type !== 'literal').map(p => [p.type, p.value]));
  const current = local(now || new Date());
  const due = new Date(Date.UTC(+current.year, +current.month - 1, +current.day - (+current.hour < 4 ? 1 : 0)));
  const dueDate = due.toISOString().slice(0, 10);
  const started = run && run.started_at && new Date(run.started_at);
  if (!started || !Number.isFinite(started.getTime())) return { tone: 'bad', label: 'Daily update has not run', detail: 'No run is recorded for the latest scheduled 4 a.m. Eastern update.' };
  const parts = local(started);
  const runDate = `${parts.year}-${parts.month}-${parts.day}`;
  if (runDate < dueDate || (runDate === dueDate && +parts.hour < 4)) return { tone: 'bad', label: 'Daily update missed', detail: 'The latest scheduled 4 a.m. Eastern update has not run.' };
  if (run.status === 'success' && run.published_at && run.sources_checked_at) return { tone: 'ok', label: 'Daily update successful', detail: 'The scheduled source check, validation and publication all completed successfully.' };
  return { tone: 'warn', label: run.status === 'running' ? 'Daily update in progress' : 'Daily update needs attention', detail: run.status === 'running' ? 'The daily update started and has not yet completed.' : 'The daily update ran, but checking, validation or publication reported an issue.' };
};
