import xml.etree.ElementTree as ET
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from xlights_seq.parsers import parse_models, ModelInfo


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
