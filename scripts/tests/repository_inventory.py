from __future__ import annotations

import importlib.util
from pathlib import Path

_IMPLEMENTATION = Path(__file__).resolve().parents[1] / "repository_inventory.py"
_SPEC = importlib.util.spec_from_file_location("_cabinet_repository_inventory", _IMPLEMENTATION)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("unable to load repository inventory implementation")
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

for _name, _value in vars(_MODULE).items():
    if not _name.startswith("__"):
        globals()[_name] = _value
