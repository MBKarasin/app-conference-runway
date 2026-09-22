Write a JSON array, one object per input series (same order, same "id"):
{
 "id": "<input id>",
 "found": [
   {"start":"YYYY-MM-DD","end":"YYYY-MM-DD","location":"Venue, City, ST / City, Country","format":"in person|virtual|hybrid",
    "theme":null,"source_url":"https://organizer page OR https://web.archive.org/web/<timestamp>/<organizer page>",
    "evidence":"VERBATIM text from that page containing the dates (<=200 chars)",
    "detail_url":"https://page for that edition's program/abstracts/recordings, or null",
    "via":"organizer|wayback"}
 ],
 "still_missing": [2023, 2025],      // years from missing_years you could not fill
 "archive_url": "https://organizer past-meetings page if you found one not already given, else null",
 "note": "why a year is missing (not held that year / biennial / not findable / domain blocked) — be specific"
}
