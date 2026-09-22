Write a JSON array, one object per input series (same order, same "id"):
{
 "id": "<input id, unchanged>",
 "archive_url": "https://... organizer page that lists or links PAST editions (e.g. 'Past Conferences', 'Past Meetings', 'Previous Years', 'Archive', proceedings/abstract archive). null if none found.",
 "archive_evidence": "VERBATIM text from that page showing it is a past-meetings page (<=160 chars), or null",
 "proceedings_url": "https://... abstracts/proceedings/journal supplement for past meetings if the organizer links one, else null",
 "past_editions": [   // up to the 3 most recent PAST editions (ended before 2026-09-21) NOT already in known_editions
   {"start":"YYYY-MM-DD","end":"YYYY-MM-DD","location":"City, ST or Country","format":"in person|virtual|hybrid",
    "theme":null,"source_url":"https://exact organizer page","evidence":"VERBATIM text containing the dates",
    "detail_url":"https://organizer page for that specific past edition (program, recordings, abstracts) or null"}
 ],
 "note": "anything contradictory, or why nothing was found"
}
