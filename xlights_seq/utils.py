import os
from werkzeug.utils import secure_filename


def allowed_file(filename, allowed):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


def secure_ext(filename, allowed):
    """Return a secure filename if its extension is allowed.

    The filename is sanitized using :func:`werkzeug.utils.secure_filename` and
    the extension is validated against the provided set of ``allowed``
    extensions. The returned value will be ``None`` if the filename does not
    contain an extension or if the extension is not permitted.
    """

    name = secure_filename(filename)
    if '.' not in name:
        return None
    ext = name.rsplit('.', 1)[1].lower()
    if ext not in allowed:
        return None
    return name


def path_in(folder, name):
    """Generate an absolute path for ``name`` inside ``folder``.

    A ``ValueError`` is raised if the resulting path would escape the target
    ``folder``. This helps protect against directory traversal attacks when
    saving user supplied filenames.
    """

    base = os.path.abspath(folder)
    path = os.path.abspath(os.path.join(base, name))
    if not path.startswith(base + os.sep):
        raise ValueError("invalid path")
    return path
