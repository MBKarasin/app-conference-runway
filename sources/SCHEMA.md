# Output schema (write valid JSON, UTF-8)
{
 "group": "<group letter>",
 "series": [
  {
   "id": "kebab-case-unique",
   "name": "Meeting name as the organizer prints it",
   "org": "Organizer full name",
   "org_url": "https://organizer home or events page",
   "professions": ["NP","PA","CRNA","CAA","CNS","CNM","RNFA","RN","MD"],   // who the meeting explicitly serves; NP/PA must be justified by the page (registration category, CE/CME for NPs/PAs, or APP track)
   "specialty": ["critical care","emergency","cardiology", "..."],  // free text, lower case
   "audience": ["clinician","leader","academic"],               // your judgment; will be labeled as curator tags
   "kind": "conference|symposium|summit|course|observance",
   "region": "near|us|intl|virtual",   // near = NJ, NY, PA, DE, MD, DC
   "recurrence": "annual, typically <Month>" ,
   "editions": [
    {
     "start": "YYYY-MM-DD", "end": "YYYY-MM-DD",
     "location": "Venue, City, ST" ,
     "format": "in person|virtual|hybrid",
     "theme": null,
     "call": {"status": "open|closed|soon|none|tba", "opens": null, "closes": "YYYY-MM-DD or null", "text": "deadline wording as published, incl. time zone", "url": "https://...",
              "due_time": "HH:MM (optional; only when the organizer publishes a cut-off time)", "tz": "IANA zone for due_time, e.g. America/New_York"},
     "source_url": "https://exact page where the dates were read",
     "evidence": "VERBATIM text copied from that page that contains the dates (<=200 chars). Never paraphrase.",
     "checked": "2026-09-21"
    }
   ]
  }
 ],
 "not_found": [ {"org": "...", "url": "...", "reason": "no dates posted / page unreachable / not relevant"} ]
}

## Curator corrections (`sources/overrides.json`)

Each entry under `series` or `editions` patches fields by id and must carry `_why` (the reason, with the organizer's wording and where it was read) and `reviewed_on` (YYYY-MM-DD); the build gate rejects one without them. Two keys are special:

- `call_patch`: adds or corrects single call fields, for example `{"due_time": "23:59", "tz": "America/Chicago"}`, without restating the whole call.
- `uid`: the calendar-feed identity an edition keeps when its date is corrected, normally the id it was first published under, so a subscriber's event is updated rather than duplicated.
- `"removed": true` drops a wrong edition while keeping the record of it.
