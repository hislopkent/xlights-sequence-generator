import zipfile, os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from xlights_seq.xsq_package import write_xsq, write_xsqz


def test_xsq_and_xsqz(tmp_path):
    rgbeffects = tmp_path/"xlights_rgbeffects.xml"
    rgbeffects.write_text("<xrgb></xrgb>", encoding="utf-8")
    xsq = tmp_path/"out.xsq"; xsqz = tmp_path/"out.xsqz"
    write_xsq(str(xsq), str(rgbeffects))
    assert xsq.exists() and xsq.read_text(encoding="utf-8").startswith("<xrgb")
    write_xsqz(str(xsqz), str(rgbeffects), None, [])
    with zipfile.ZipFile(xsqz) as z:
        assert "xlights_rgbeffects.xml" in z.namelist()
