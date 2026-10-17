import json
import check
from pathlib import Path
d=json.loads((check.ROOT/'site/data/runway.json').read_text())
v=json.loads((check.ROOT/'data/verification.json').read_text())
series={s['id']:s for s in d['series']}
eds=[e for e in d['editions'] if e['id'] in v and v[e['id']]['state']!='archived']
frozen=[e for e in d['editions'] if e['id'] in v and v[e['id']]['state']=='archived']
check.write_report(eds,v,[],series,frozen)
