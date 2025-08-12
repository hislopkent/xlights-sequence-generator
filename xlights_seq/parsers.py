import xml.etree.ElementTree as ET
import re
import unicodedata
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).lower()
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s


def _attr(elem, *names) -> Optional[str]:
    for n in names:
        if n in elem.attrib:
            return elem.attrib[n]
        if n.capitalize() in elem.attrib:
            return elem.attrib[n.capitalize()]
    return None


def map_style_groups_to_layout(style_group_names: list[str], layout_groups: list[str]) -> Dict[str, str]:
    """Map suggested style groups (e.g., 'Focal_Tree') to best matching layout group names."""
    norm_layout = { _norm(g): g for g in layout_groups }
    out = {}
    for sg in style_group_names:
        candidates = [p.strip() for p in re.split(r"[,/•–-]", sg) if p.strip()]
        best = None
        for c in candidates:
            n = _norm(c)
            for k, orig in norm_layout.items():
                if n and n in k:
                    best = orig
                    break
            if best:
                break
        if best:
            out[sg] = best
    return out

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
    parent: Optional["NodeInfo"] = None

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


def parse_layout_groups_and_models(xml_path: str) -> tuple[list[str], Dict[str, ModelInfo]]:
    """Return all layout group names and an index of models with strings/nodes."""
    root = ET.parse(xml_path).getroot()
    layout_groups: list[str] = []
    models_index: Dict[str, ModelInfo] = {}

    for g in root.findall(".//group"):
        gname = (g.get("name") or g.get("Group") or g.get("Name") or "").strip()
        if gname:
            layout_groups.append(gname)

    for m in root.findall(".//model"):
        name = (m.get("name") or m.get("Model") or m.get("Name") or "").strip()
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
        models_index[name] = ModelInfo(name=name, strings=strings_i, nodes=nodes_i)

    return layout_groups, models_index


def extract_model_nodes(xml_path: str) -> Dict[str, List[Tuple[float, float]]]:
    """
    Returns { model_name: [(x,y), ...] }.
    Tries common xLights layouts: <model><node x="" y=""/>, or nested variants.
    """
    root = ET.parse(xml_path).getroot()
    out: Dict[str, List[Tuple[float, float]]] = {}
    for m in root.findall(".//model"):
        name = m.get("name") or m.get("Model") or m.get("Name")
        if not name:
            continue
        pts: List[Tuple[float, float]] = []
        # 1) Direct nodes
        for n in m.findall(".//node"):
            xs, ys = _attr(n, "x"), _attr(n, "y")
            if xs is not None and ys is not None:
                try:
                    pts.append((float(xs), float(ys)))
                except ValueError:
                    pass
        # 2) Some layouts store coordinates on <pixel> or <point> elements
        if not pts:
            for tag in ("pixel", "point", "Point"):
                for n in m.findall(f".//{tag}"):
                    xs, ys = _attr(n, "x"), _attr(n, "y")
                    if xs is not None and ys is not None:
                        try:
                            pts.append((float(xs), float(ys)))
                        except ValueError:
                            pass
        out[name] = pts
    return out


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


def parse_tree_with_index(xml_path: str):
    root = ET.parse(xml_path).getroot()
    name_index: Dict[str, NodeInfo] = {}
    top = NodeInfo(name="ROOT", type="group")

    # Index all models
    for m in root.findall(".//model"):
        n = (m.get("name") or m.get("Model") or m.get("Name") or "").strip()
        if not n:
            continue
        strings = m.get("StringCount") or m.get("strings")
        nodes = m.get("Nodes") or m.get("nodes")
        ni = NodeInfo(
            name=n,
            type="model",
            strings=int(strings) if strings and str(strings).isdigit() else None,
            nodes=int(nodes) if nodes and str(nodes).isdigit() else None,
        )
        name_index[n] = ni

    # Groups from explicit <group> definitions (member refs)
    groups: List[NodeInfo] = []
    for g in root.findall(".//group"):
        gname = (g.get("name") or g.get("Group") or g.get("Name") or "").strip()
        if not gname:
            continue
        gi = NodeInfo(name=gname, type="group")
        # members via <member name="..."/> or CSV attribute
        for mem in g.findall(".//member"):
            ref = (mem.get("name") or "").strip()
            if ref in name_index:
                child = name_index[ref]
                gi.children.append(child)
                child.parent = gi
        members_csv = (g.get("members") or g.get("Members") or "")
        for ref in [x.strip() for x in members_csv.split(",") if x.strip()]:
            if ref in name_index and name_index[ref] not in gi.children:
                child = name_index[ref]
                gi.children.append(child)
                child.parent = gi
        groups.append(gi)

    # Heuristic sub-model inference: name nesting like "Tree-Left", "MegaTree:1"
    for name, node in list(name_index.items()):
        m = re.match(r"(.+?)[\-\:\_ ]\s*(\d+|left|right|top|bottom|inner|outer)$", name, re.I)
        if m:
            parent_name = m.group(1).strip()
            if parent_name in name_index:
                parent = name_index[parent_name]
                # create a synthetic group for the parent if not already a group
                if parent.type == "model":
                    gi = NodeInfo(name=f"{parent.name}_GROUP", type="group")
                    gi.children.append(parent)
                    parent.parent = gi
                    groups.append(gi)
                    name_index[gi.name] = gi
                    parent = gi
                node.parent = parent
                if node not in parent.children:
                    parent.children.append(node)

    # Attach anything unattached to ROOT
    attached = {c.name for g in groups for c in g.children}
    for n in name_index.values():
        if n.parent is None and n.name not in [g.name for g in groups]:
            top.children.append(n)
    for g in groups:
        if g.parent is None:
            top.children.append(g)

    return top, name_index


def flatten_models(tree: NodeInfo) -> list[NodeInfo]:
    out = []
    def walk(n):
        if n.type == "model": out.append(n)
        for c in n.children: walk(c)
    walk(tree)
    return out
