#!/bin/bash
# Full PCB build: generate -> fill zones -> restore project DRC rules.
set -e
cd "$(dirname "$0")"
KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
$KPY -u gen_pcb.py 2>/dev/null | grep -E 'wrote|STAGE: save'
$KPY -u fill_zones.py 2>/dev/null | tail -1
# pcbnew.SaveBoard overwrites the .kicad_pro with defaults; restore ours
cd ..
git checkout plant-hub-v1.0.kicad_pro
python3 - <<'PYEOF'
import json
from pathlib import Path
p = Path("plant-hub-v1.0.kicad_pro")
d = json.loads(p.read_text())
for c in d["net_settings"]["classes"]:
    if c["name"] == "Power":
        c["clearance"] = 0.2
d["board"]["design_settings"]["rules"]["min_resolved_spokes"] = 1
p.write_text(json.dumps(d, indent=2))
PYEOF
