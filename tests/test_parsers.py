import xml.etree.ElementTree as ET
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from xlights_seq.parsers import parse_models, ModelInfo, parse_tree_with_index


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
