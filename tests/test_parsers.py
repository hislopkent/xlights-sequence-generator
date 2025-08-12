import xml.etree.ElementTree as ET
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from xlights_seq.parsers import (
    parse_models,
    ModelInfo,
    parse_tree_with_index,
    map_style_groups_to_layout,
    parse_layout_groups_and_models,
    extract_model_nodes,
)


def test_parse_models_deduplicate(tmp_path):
    xml = ET.Element("root")
    ET.SubElement(xml, "model", name="Tree", StringCount="10")
    ET.SubElement(xml, "model", Model="Tree", Strings="8")
    ET.SubElement(xml, "model", name="Star", Nodes="50")
    ET.ElementTree(xml).write(tmp_path / "models.xml")

    models = parse_models(str(tmp_path / "models.xml"))
    assert [m.name for m in models] == ["Tree", "Star"]
    tree = models[0]
    star = models[1]
    assert tree.strings == 10 and tree.nodes is None
    assert star.strings is None and star.nodes == 50


def test_parse_tree_with_index(tmp_path):
    xml = ET.Element("root")
    ET.SubElement(xml, "model", name="MegaTree", StringCount="10")
    ET.SubElement(xml, "model", name="MegaTree-Left", StringCount="5")
    ET.SubElement(xml, "model", name="MiniTree", Nodes="20")
    g = ET.SubElement(xml, "group", name="Trees")
    ET.SubElement(g, "member", name="MegaTree")
    ET.SubElement(g, "member", name="MiniTree")
    ET.ElementTree(xml).write(tmp_path / "layout.xml")

    tree, name_index = parse_tree_with_index(str(tmp_path / "layout.xml"))
    assert {c.name for c in tree.children} == {"Trees", "MegaTree_GROUP"}
    assert name_index["MegaTree-Left"].parent.name == "MegaTree_GROUP"
    assert name_index["MegaTree"].parent.name == "MegaTree_GROUP"
    assert name_index["MiniTree"].parent.name == "Trees"
    assert name_index["MegaTree_GROUP"].type == "group"


def test_layout_groups_and_fuzzy_match(tmp_path):
    xml = ET.Element("root")
    ET.SubElement(xml, "model", name="Tree", StringCount="5")
    ET.SubElement(xml, "model", name="Star", Nodes="50")
    ET.SubElement(xml, "group", name="Focal Tree")
    ET.SubElement(xml, "group", name="Garage")
    ET.ElementTree(xml).write(tmp_path / "layout.xml")

    layout_groups, models_index = parse_layout_groups_and_models(str(tmp_path / "layout.xml"))
    assert set(layout_groups) == {"Focal Tree", "Garage"}
    assert models_index["Tree"].strings == 5
    assert models_index["Star"].nodes == 50

    mapping = map_style_groups_to_layout(["Focal_Tree", "Garage/Porch", "Other"], layout_groups)
    assert mapping == {"Focal_Tree": "Focal Tree", "Garage/Porch": "Garage"}


def test_extract_model_nodes(tmp_path):
    xml = ET.Element("root")
    m1 = ET.SubElement(xml, "model", name="Tree")
    ET.SubElement(m1, "node", x="1", y="2")
    ET.SubElement(m1, "node", X="3", Y="4")
    m2 = ET.SubElement(xml, "model", name="Star")
    ET.SubElement(m2, "pixel", x="5", y="6")
    ET.SubElement(m2, "pixel", x="7", y="8")
    ET.ElementTree(xml).write(tmp_path / "coords.xml")

    coords = extract_model_nodes(str(tmp_path / "coords.xml"))
    assert coords["Tree"] == [(1.0, 2.0), (3.0, 4.0)]
    assert coords["Star"] == [(5.0, 6.0), (7.0, 8.0)]
