import os
from pathlib import Path


def _this_file() -> Path:
    return Path(__file__).resolve()


def get_project_root() -> Path:
    tf = _this_file()
    return tf.parents[1]


def get_process_method_root() -> Path:
    env = os.environ.get("PROCESS_METHOD_ROOT", "").strip()
    if env:
        return Path(env)
    return get_project_root() / "process_mothod"


def ensure_process_method_on_path() -> None:
    import sys

    root = str(get_process_method_root())
    if root not in sys.path:
        sys.path.insert(0, root)
