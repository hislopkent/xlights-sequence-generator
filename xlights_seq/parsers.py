import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ModelInfo:
    name: str
    strings: int|None = None
    nodes: int|None = None


@dataclass
class NodeInfo:
    name: str
    type: str             # "model" | "group"
    strings: Optional[int] = None
    nodes: Optional[int] = None
    children: List["NodeInfo"] = field(default_factory=list)

def parse_models(xml_path: str) -> list[ModelInfo]:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    models: list[ModelInfo] = []

    for m in root.findall(".//model"):
        name = m.get("name") or m.get("Model") or m.get("Name")
        if not name:
            continue
        strings = m.get("StringCount") or m.get("strings")
        nodes = m.get("Nodes") or m.get("nodes")
        try:
            strings_i = int(strings) if strings is not None else None
        except ValueError:
            strings_i = None
        try:
            nodes_i = int(nodes) if nodes is not None else None
        except ValueError:
            nodes_i = None
        models.append(ModelInfo(name=name, strings=strings_i, nodes=nodes_i))

    # Deduplicate by name
    seen=set(); uniq=[]
    for mi in models:
        if mi.name not in seen:
            uniq.append(mi); seen.add(mi.name)
    return uniq


def parse_tree(xml_path: str) -> NodeInfo:
    root = ET.parse(xml_path).getroot()
    # Many xLights layouts have <models> with multiple <model> and <group>.
    # Groups typically include child references by name. Structure varies by version, so we discover both.
    models_index = {}
    top = NodeInfo(name="ROOT", type="group")

    # index models
    for m in root.findall(".//model"):
        name = m.get("name") or m.get("Model") or m.get("Name")
        if not name: continue
        strings = m.get("StringCount") or m.get("strings")
        nodes = m.get("Nodes") or m.get("nodes")
        models_index[name] = NodeInfo(
            name=name, type="model",
            strings=int(strings) if (strings and strings.isdigit()) else None,
            nodes=int(nodes) if (nodes and nodes.isdigit()) else None
        )

    # groups (best-effort: search common structures)
    groups = []
    for g in root.findall(".//group"):
        gname = g.get("name") or g.get("Group") or g.get("Name")
        if not gname: continue
        node = NodeInfo(name=gname, type="group")
        # child refs by <member name="..."> or CSV in attribute
        for mem in g.findall(".//member"):
            ref = mem.get("name")
            if ref and ref in models_index:
                node.children.append(models_index[ref])
        members_csv = (g.get("members") or g.get("Members") or "")
        for ref in [x.strip() for x in members_csv.split(",") if x.strip()]:
            if ref in models_index and models_index[ref] not in node.children:
                node.children.append(models_index[ref])
        groups.append(node)

    # attach loose models (not in groups) under ROOT
    grouped_names = {c.name for gg in groups for c in gg.children}
    for m in list(models_index.values()):
        if m.name not in grouped_names:
            top.children.append(m)
    # append groups
    top.children.extend(groups)
    return top


def flatten_models(tree: NodeInfo) -> list[NodeInfo]:
    out = []
    def walk(n):
        if n.type == "model": out.append(n)
        for c in n.children: walk(c)
    walk(tree)
    return out
