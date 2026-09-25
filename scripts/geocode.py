#!/usr/bin/env python3
"""Geocode edition locations and build the client-side ZIP / city lookups.

Inputs (downloaded to .geocache/ on first run; public data):
  US Census 2024 Gazetteer: places and ZCTAs (public domain)
  GeoNames cities15000 + countryInfo (CC BY 4.0, attribution in the site footer)
Outputs:
  sources/geo/locations.json   location string -> {lat, lon, cc, country, continent, state, region, precision}
  site/geo/zip/<zip3>.json     ZCTA centroids, sharded by first three digits (loaded only when someone types a ZIP)
  site/geo/cities.json         world cities of 100,000+ people and US cities of 15,000+, with state or province, for "near a city"
Unresolved locations are listed on stdout; add them by hand to sources/geo/manual.json.
"""
import csv, io, json, re, sys, zipfile, pathlib, urllib.request, unicodedata
ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / ".geocache"; CACHE.mkdir(exist_ok=True)
URLS = {
    "place": "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2024_Gazetteer/2024_Gaz_place_national.zip",
    "zcta": "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2024_Gazetteer/2024_Gaz_zcta_national.zip",
    "cities": "https://download.geonames.org/export/dump/cities15000.zip",
    "countries": "https://download.geonames.org/export/dump/countryInfo.txt",
    "admin1": "https://download.geonames.org/export/dump/admin1CodesASCII.txt",
}
def get(name):
    f = CACHE / URLS[name].rsplit("/", 1)[1]
    if not f.exists():
        urllib.request.urlretrieve(URLS[name], f)
    if f.suffix == ".zip":
        z = zipfile.ZipFile(f); return z.read(z.namelist()[0]).decode("utf-8")
    return f.read_text("utf-8")

STATES = {"AL":"Alabama","AK":"Alaska","AZ":"Arizona","AR":"Arkansas","CA":"California","CO":"Colorado","CT":"Connecticut","DE":"Delaware","DC":"District of Columbia","FL":"Florida","GA":"Georgia","HI":"Hawaii","ID":"Idaho","IL":"Illinois","IN":"Indiana","IA":"Iowa","KS":"Kansas","KY":"Kentucky","LA":"Louisiana","ME":"Maine","MD":"Maryland","MA":"Massachusetts","MI":"Michigan","MN":"Minnesota","MS":"Mississippi","MO":"Missouri","MT":"Montana","NE":"Nebraska","NV":"Nevada","NH":"New Hampshire","NJ":"New Jersey","NM":"New Mexico","NY":"New York","NC":"North Carolina","ND":"North Dakota","OH":"Ohio","OK":"Oklahoma","OR":"Oregon","PA":"Pennsylvania","RI":"Rhode Island","SC":"South Carolina","SD":"South Dakota","TN":"Tennessee","TX":"Texas","UT":"Utah","VT":"Vermont","VA":"Virginia","WA":"Washington","WV":"West Virginia","WI":"Wisconsin","WY":"Wyoming","PR":"Puerto Rico"}
NAME2ST = {v.lower(): k for k, v in STATES.items()}
REGION = {}  # US Census regions
for r, sts in {"Northeast": "CT ME MA NH RI VT NJ NY PA", "Midwest": "IL IN MI OH WI IA KS MN MO NE ND SD",
               "South": "DE DC FL GA MD NC SC VA WV AL KY MS TN AR LA OK TX PR", "West": "AZ CO ID MT NV NM UT WY AK CA HI OR WA"}.items():
    for s in sts.split(): REGION[s] = r
CONT = {"NA": "North America", "SA": "South America", "EU": "Europe", "AS": "Asia", "OC": "Oceania", "AF": "Africa", "AN": "Antarctica"}
ONLINE = re.compile(r"^(virtual|online)\b", re.I)
NOPLACE = re.compile(r"not yet posted|listings in|^nationwide$|^global\b", re.I)
fold = lambda s: unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()

def load():
    places = {}  # (ST) -> list of (name_folded, lat, lon, pop_rank)
    for row in csv.DictReader(io.StringIO(get("place")), delimiter="\t"):
        row = {k.strip(): v.strip() for k, v in row.items()}
        nm = re.sub(r"\s+(city|town|CDP|village|borough|municipality|city and borough|urban county|consolidated government.*|metropolitan government.*|unified government.*|\(balance\))$", "", row["NAME"])
        nm = re.sub(r"\s+(city|town|CDP|village|borough)$", "", nm)
        places.setdefault(row["USPS"], []).append((fold(nm), float(row["INTPTLAT"]), float(row["INTPTLONG"]), float(row["ALAND_SQMI"] or 0)))
    cities, countries = [], {}
    for line in get("countries").splitlines():
        if line.startswith("#") or not line.strip(): continue
        c = line.split("\t"); countries[c[0]] = {"name": c[4], "continent": c[8]}
    for line in get("cities").splitlines():
        c = line.split("\t")
        cities.append({"name": c[1], "ascii": c[2], "alt": c[3], "lat": float(c[4]), "lon": float(c[5]), "cc": c[8], "admin1": c[10], "pop": int(c[14] or 0)})
    return places, cities, countries

def geocode(loc, places, cities, countries, name2cc):
    raw = loc
    loc = re.sub(r"\(.*?\)", " ", loc); loc = re.sub(r",?\s+and online$", "", loc, flags=re.I).strip(" ,")
    parts = [p.strip() for p in loc.split(",") if p.strip()]
    f = fold(loc)
    # United States: a state code or state name in the parts
    st = next((p for p in reversed(parts) if p in STATES), None) or next((NAME2ST[fold(p)] for p in reversed(parts) if fold(p) in NAME2ST), None)
    if st and not any(fold(p) in name2cc and name2cc[fold(p)] != "US" for p in parts[-1:]):
        best = None
        for nm, lat, lon, area in places.get(st, []):
            if len(nm) >= 4 and re.search(r"\b" + re.escape(nm) + r"\b", f):
                if not best or len(nm) > len(best[0]) or (len(nm) == len(best[0]) and area > best[3]): best = (nm, lat, lon, area)
        for c in cities:
            if c["cc"] == "US" and c["admin1"] == st:
                for nm in {fold(c["name"]), fold(c["ascii"])}:
                    if len(nm) >= 4 and re.search(r"\b" + re.escape(nm) + r"\b", f) and (not best or len(nm) > len(best[0])):
                        best = (nm, c["lat"], c["lon"], 0)
        g = {"cc": "US", "country": "United States", "continent": "North America", "state": st, "region": REGION.get(st)}
        if best: return {**g, "lat": round(best[1], 4), "lon": round(best[2], 4), "place": best[0].title(), "precision": "city"}
        pts = places.get(st, [])
        if pts:
            big = sorted(pts, key=lambda p: -p[3])[:25]
            return {**g, "lat": round(sum(p[1] for p in big) / len(big), 3), "lon": round(sum(p[2] for p in big) / len(big), 3), "precision": "state"}
        return {**g, "precision": "state"}
    # elsewhere: last part names a country (or the whole string is a city-state)
    cc = next((name2cc[fold(p)] for p in reversed(parts) if fold(p) in name2cc), None)
    if not cc: return None
    best = None
    for c in cities:
        if c["cc"] != cc: continue
        for nm in {fold(c["name"]), fold(c["ascii"])}:
            if len(nm) >= 4 and re.search(r"\b" + re.escape(nm) + r"\b", f):
                if not best or len(nm) > len(best[0]) or (len(nm) == len(best[0]) and c["pop"] > best[1]["pop"]): best = (nm, c)
    g = {"cc": cc, "country": countries[cc]["name"], "continent": CONT[countries[cc]["continent"]], "region": CONT[countries[cc]["continent"]]}
    if best: return {**g, "lat": round(best[1]["lat"], 4), "lon": round(best[1]["lon"], 4), "place": best[1]["name"], "precision": "city"}
    top = max((c for c in cities if c["cc"] == cc), key=lambda c: c["pop"], default=None)
    return {**g, **({"lat": round(top["lat"], 3), "lon": round(top["lon"], 3)} if top else {}), "precision": "country"}

def main():
    places, cities, countries = load()
    name2cc = {fold(v["name"]): k for k, v in countries.items()}
    name2cc.update({"usa": "US", "united states": "US", "us": "US", "czech republic": "CZ", "uk": "GB", "england": "GB", "scotland": "GB", "korea": "KR", "south korea": "KR"})
    data = json.load(open(ROOT / "site/data/runway.json", encoding="utf-8"))
    manual = json.load(open(ROOT / "sources/geo/manual.json", encoding="utf-8")) if (ROOT / "sources/geo/manual.json").exists() else {}
    out, miss = {}, []
    for loc in sorted({e["location"] for e in data["editions"] if e.get("location")}):
        if ONLINE.search(loc) or NOPLACE.search(loc): continue
        g = manual.get(loc) or geocode(loc, places, cities, countries, name2cc)
        if g: out[loc] = g
        else: miss.append(loc)
    json.dump(out, open(ROOT / "sources/geo/locations.json", "w", encoding="utf-8"), indent=0, ensure_ascii=False, sort_keys=True)
    # client lookups
    zdir = ROOT / "site/geo/zip"; zdir.mkdir(parents=True, exist_ok=True)
    shards = {}
    for row in csv.DictReader(io.StringIO(get("zcta")), delimiter="\t"):
        row = {k.strip(): v.strip() for k, v in row.items()}
        z = row["GEOID"]; shards.setdefault(z[:3], {})[z] = [round(float(row["INTPTLAT"]), 3), round(float(row["INTPTLONG"]), 3)]
    for k, v in shards.items():
        json.dump(v, open(zdir / f"{k}.json", "w", encoding="utf-8"), separators=(",", ":"))
    # Each city carries its state or province (GeoNames admin1 name) so "Springfield, IL" and "Portland, ME"
    # resolve to the right place (red team F05). US cities go down to 15,000 people; elsewhere 100,000.
    admin1 = {}
    for line in get("admin1").splitlines():
        a = line.split("\t")
        if len(a) > 1: admin1[a[0]] = a[1]
    big = sorted((c for c in cities if c["pop"] >= 100000 or (c["cc"] == "US" and c["pop"] >= 15000)), key=lambda c: -c["pop"])
    json.dump([[c["name"], countries[c["cc"]]["name"], round(c["lat"], 3), round(c["lon"], 3), admin1.get(c["cc"] + "." + c["admin1"], "")] for c in big],
              open(ROOT / "site/geo/cities.json", "w", encoding="utf-8"), separators=(",", ":"), ensure_ascii=False)
    prec = {}
    for g in out.values(): prec[g["precision"]] = prec.get(g["precision"], 0) + 1
    print(f"geocoded {len(out)} locations {prec}; zip shards {len(shards)}; cities {len(big)}")
    if miss: print("UNRESOLVED:", *miss, sep="\n  ")

if __name__ == "__main__":
    main()
