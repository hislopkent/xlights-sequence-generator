import xml.etree.ElementTree as ET
from dataclasses import dataclass


@dataclass
class ModelInfo:
    name: str
    strings: int | None = None
    nodes: int | None = None


def parse_models(xml_path: str) -> list[ModelInfo]:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    models: list[ModelInfo] = []

    # xLights rgbeffects: models often under <models><model name="...">...</model></models>
    for m in root.findall(".//model"):
        name = m.get("name") or m.get("Model")
        strings = m.get("StringCount") or m.get("strings")
        nodes = m.get("Nodes") or m.get("nodes")
        models.append(
            ModelInfo(
                name=name,
                strings=int(strings) if strings else None,
                nodes=int(nodes) if nodes else None,
            )
        )

    # de-dup names, keep first occurrence
    seen = set()
    uniq: list[ModelInfo] = []
    for mi in models:
        if mi.name and mi.name not in seen:
            uniq.append(mi)
            seen.add(mi.name)

    return uniq
