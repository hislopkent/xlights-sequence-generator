import xml.etree.ElementTree as ET
from dataclasses import dataclass

@dataclass
class ModelInfo:
    name: str
    strings: int|None = None
    nodes: int|None = None

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
