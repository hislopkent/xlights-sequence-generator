import os, shutil, zipfile


def write_xsq(xsq_path: str, rgbeffects_path: str):
    # XSQ = single-file sequence doc. Minimal valid content: xlights_rgbeffects.xml content.
    shutil.copyfile(rgbeffects_path, xsq_path)
    return xsq_path


def write_xsqz(xsqz_path: str, rgbeffects_path: str,
               networks_path: str | None = None,
               media_files: list[str] | None = None):
    # XSQZ = zip package. xLights importer expects exact names:
    #   /xlights_rgbeffects.xml   (required)
    #   /xlights_networks.xml     (optional)
    #   /media/<files>            (optional)
    with zipfile.ZipFile(xsqz_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(rgbeffects_path, arcname="xlights_rgbeffects.xml")
        if networks_path and os.path.exists(networks_path):
            z.write(networks_path, arcname="xlights_networks.xml")
        if media_files:
            for f in media_files:
                if f and os.path.exists(f):
                    z.write(f, arcname=os.path.join("media", os.path.basename(f)))
    return xsqz_path
