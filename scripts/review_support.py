import datetime as dt
def evidence_current(e,today):
    when=e.get("reviewed_on") or e.get("compiled")
    try: age=(dt.date.fromisoformat(today)-dt.date.fromisoformat(when[:10])).days
    except (ValueError,TypeError,AttributeError): return False
    return bool(e.get("source_reviewed") and e.get("evidence") and 0 <= age <= 90)
