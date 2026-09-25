"""Suite-wide guard: no test may file a document in the real register."""
import os
import shutil

import pytest


@pytest.fixture(autouse=True)
def _never_file_documents(monkeypatch):
    for k in [k for k in os.environ if k.startswith("DOC_")]:
        monkeypatch.delenv(k)
    dirs = [d for d in os.environ.get("PATH", "").split(os.pathsep)
            if d and not os.access(os.path.join(d, "cc-docs"), os.X_OK)]
    monkeypatch.setenv("PATH", os.pathsep.join(dirs))
    assert shutil.which("cc-docs") is None
