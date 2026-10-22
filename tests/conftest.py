import functools
import json
import os
from pathlib import Path

import pytest
import yaml

from vis_workflow import load_descriptor

FIXTURES = Path(__file__).parent / "fixtures"
SNAPSHOTS = Path(__file__).parent / "snapshots"
FIXTURE_NAMES = [
    "cideconvolve_config.yaml",
    "wb_measurements_config.yaml",
    "bilayers_example.yaml",
    "W_NucleiSegmentation-ImageJ.descriptor.json",
    "example_workflow.json",
]


@functools.cache
def load_fixture(name):
    """Loaded once per session; Descriptor is frozen, so tests share it."""
    return load_descriptor((FIXTURES / name).read_text(encoding="utf-8"), name=name)


@pytest.fixture
def bilayers_raw():
    """Raw Bilayers example, to modify per test and load with load_raw()."""
    return yaml.safe_load((FIXTURES / "bilayers_example.yaml").read_text(encoding="utf-8"))


def load_raw(raw):
    return load_descriptor(json.dumps(raw))


@pytest.fixture
def snapshot():
    """Compare text to tests/snapshots/<name>; VIS_WORKFLOW_UPDATE_SNAPSHOTS=1 rewrites them."""
    def check(name, text):
        path = SNAPSHOTS / name
        if os.environ.get("VIS_WORKFLOW_UPDATE_SNAPSHOTS") == "1":
            path.parent.mkdir(exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="\n")
        assert path.exists(), f"No snapshot {path.name}: run with VIS_WORKFLOW_UPDATE_SNAPSHOTS=1"
        assert text == path.read_text(encoding="utf-8")
    return check
