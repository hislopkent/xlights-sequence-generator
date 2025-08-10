from typing import Dict, List
from .parsers import NodeInfo

# Heuristics for common props; tune as you see them in real layouts.
KEYWORDS = {
  "mega_tree": ["mega", "megatree", "tree"],
  "arches": ["arch","arches"],
  "matrix": ["matrix","panel","screen"],
  "windows": ["window","windows"],
  "roofline": ["roof","eaves","gutter","ridge"],
  "garland": ["garland","swag"],
  "spinner": ["spinner","starburst"],
  "stars": ["star","stars"]
}

def recommend_groups(tree: NodeInfo):
    # Output: list of {"name": str, "members": [model_name,...], "reason": str}
    models: List[NodeInfo] = []
    def rec(n):
        if n.type=="model": models.append(n)
        for c in n.children: rec(c)
    rec(tree)

    names = [(m.name.lower(), m) for m in models]
    recs = []

    # 1) Keyword-based groupings
    for gname, kws in KEYWORDS.items():
        members = [m.name for n,m in names if any(k in n for k in kws)]
        if len(members) >= 2:
            recs.append({"name": gname, "members": sorted(set(members)), "reason": "keyword-match"})

    # 2) Prefix-based “family” grouping, e.g., Tree-1, Tree-2...
    prefix_map: Dict[str, List[str]] = {}
    for m in models:
        parts = m.name.replace(":", "-").split("-")
        if len(parts)>=2:
            prefix = parts[0].strip()
            prefix_map.setdefault(prefix, []).append(m.name)
    for prefix, members in prefix_map.items():
        if len(members) >= 2:
            recs.append({"name": f"{prefix}_family", "members": sorted(set(members)), "reason": "prefix-family"})

    # 3) Size-based split (e.g., large vs small)
    large = [m.name for m in models if (m.nodes or 0) >= 500 or (m.strings or 0) >= 24]
    small = [m.name for m in models if (m.nodes or 0) and (m.nodes or 0) < 200]
    if len(large) >= 2: recs.append({"name":"large_props", "members":sorted(set(large)), "reason":"size-large"})
    if len(small) >= 2: recs.append({"name":"small_props", "members":sorted(set(small)), "reason":"size-small"})

    # Dedup by name
    uniq = {}
    for r in recs:
        uniq[r["name"]] = r
    return list(uniq.values())
