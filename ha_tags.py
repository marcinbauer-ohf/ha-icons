"""Where Home Assistant uses each icon: writes ha-tags.json.

    python3 ha_tags.py <core checkout> <frontend checkout>

Reads homeassistant/components/*/icons.json from core and src/ from the frontend.
Tags per icon (each only when present):
  domain        domains whose default icon this is
  device_class  "domain.device_class" it is the icon for
  state         "domain: state" or "domain.device_class: state" it shows (core entity components only)
  action        "domain.action" it stands for
  trigger       "domain.trigger"
  condition     "domain.condition"
  entity        entity platforms where integrations use it for their own entities
  integrations  how many integrations use it
  ui            the frontend uses it directly
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

core, frontend = map(Path, sys.argv[1:3])
tags = defaultdict(lambda: defaultdict(set))


def walk(node, path=()):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from walk(v, path + (k,))
    elif isinstance(node, str) and node.startswith("mdi:"):
        yield path, node[4:]


for f in sorted(core.glob("homeassistant/components/*/icons.json")):
    comp = f.parent.name
    for path, icon in walk(json.loads(f.read_text())):
        t = tags[icon]
        t["integrations"].add(comp)
        kind = path[0]
        if kind == "entity_component":
            owner = comp if path[1] == "_" else f"{comp}.{path[1]}"
            if path[2] == "default":
                t["domain" if path[1] == "_" else "device_class"].add(owner)
            elif path[2] == "state":
                t["state"].add(f"{owner}: {path[3]}")
        elif kind == "entity":
            t["entity"].add(path[1])
        elif kind in ("services", "triggers", "conditions"):
            t[{"services": "action", "triggers": "trigger", "conditions": "condition"}[kind]].add(f"{comp}.{path[1]}")

kebab = lambda s: re.sub(r"(?<=[a-z])(?=[A-Z0-9])|(?<=[0-9])(?=[A-Z])", "-", s).lower()
for f in frontend.glob("src/**/*.ts"):
    text = f.read_text()
    for m in set(re.findall(r"\bmdi([A-Z]\w*)", text)):
        tags[kebab(m)]["ui"].add(True)
    if f.name == "icons.ts":  # the frontend's own domain defaults
        block = re.search(r"FALLBACK_DOMAIN_ICONS = \{(.*?)\n\}", text, re.S)
        for domain, m in re.findall(r"(\w+): mdi(\w+)", block.group(1) if block else ""):
            tags[kebab(m)]["domain"].add(domain)

out = {}
for icon, t in sorted(tags.items()):
    out[icon] = {k: len(v) if k == "integrations" else True if k == "ui" else sorted(v) for k, v in sorted(t.items())}
assert out["robot-vacuum"]["domain"] == ["vacuum"], out.get("robot-vacuum")  # the one check: a known domain default
(Path(__file__).parent / "ha-tags.json").write_text(json.dumps(out, indent=0, separators=(",", ":")))
print(len(out), "icons tagged;", sum("domain" in t for t in out.values()), "domain defaults")
