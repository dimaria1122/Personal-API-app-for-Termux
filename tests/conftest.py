from __future__ import annotations

import sys
import tempfile
from pathlib import Path
import os
import uuid

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TEMP_ROOT = Path(r"C:\Users\violet\.codex\memories\teleg_tmp")
TEMP_ROOT.mkdir(exist_ok=True)
tempfile.tempdir = str(TEMP_ROOT)
os.environ.setdefault("TMPDIR", str(TEMP_ROOT))
os.environ.setdefault("TEMP", str(TEMP_ROOT))
os.environ.setdefault("TMP", str(TEMP_ROOT))


@pytest.fixture
def workspace_tmp():
    path = ROOT / ".test-tmp" / uuid.uuid4().hex
    path.mkdir(parents=True, exist_ok=False)
    return path
