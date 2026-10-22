import re

import pytest

from conftest import FIXTURE_NAMES, load_fixture, load_raw
from vis_workflow import to_mermaid

NODE = re.compile(r"^\s+(\w+)(?:\[\[|\[/|\[)\"([^\"]*)\"(?:\]\]|/\]|\])$")


def nodes(text):
    """Node id -> label; fails on any node line whose label is not a single quoted string."""
    found = {}
    for line in text.splitlines():
        if "[" in line and not line.strip().startswith("subgraph"):
            match = NODE.match(line)
            assert match, f"Malformed node line: {line!r}"
            found[match.group(1)] = match.group(2)
    return found


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_diagram(name, snapshot):
    descriptor = load_fixture(name)
    text = to_mermaid(descriptor)
    snapshot(name.split(".")[0] + ".mmd", text)
    nodes(text)
    assert text.count("subgraph") == text.count("  end")
    for param in descriptor.data_inputs:
        assert f"  in_{param.id} --> tool" in text
    for param in descriptor.outputs:
        assert f"  tool --> out_{param.id}" in text


@pytest.mark.parametrize("mode, shown, summary, rows", [
    # all: Basic (19, 3 columns) and Advanced (22, 4 columns) boxes, then the chain fixing their order
    ("all", 41, None, [3] * 6 + [4] * 5 + [2] + [2]),
    ("beginner", 19, "+22 advanced parameters", [3] * 6 + [2]),
    ("collapsed", 0, "41 parameters", []),
    ("none", 0, None, []),
])
def test_parameter_modes(mode, shown, summary, rows):
    text = to_mermaid(load_fixture("cideconvolve_config.yaml"), params=mode)
    found = nodes(text)
    assert len([node_id for node_id in found if node_id.startswith("param_")]) == shown + bool(summary)
    assert summary is None or summary in found.values()
    assert [line.count("~~~") + 1 for line in text.splitlines() if "~~~" in line] == rows
    assert ("parameters -.-> tool" in text) == (mode != "none")


@pytest.mark.parametrize("name, mode, groups", [
    ("cideconvolve_config.yaml", "all", ["Basic", "Advanced"]),
    ("cideconvolve_config.yaml", "grouped", ["essential", "advanced", "method"]),
    ("example_workflow.json", "grouped", ["other"]),
    ("example_workflow.json", "all", []),
])
def test_groups_in_descriptor_order(name, mode, groups):
    text = to_mermaid(load_fixture(name), params=mode)
    for group in groups:
        assert f'subgraph group_{group}["{group}"]' in text
    assert text.count("subgraph group_") == len(groups)
    assert ("~~~ group_" in text) == (len(groups) > 1)
    assert len(groups) < 2 or " ~~~ ".join(f"group_{group}" for group in groups) in text


def test_unknown_mode_rejected():
    with pytest.raises(ValueError, match="Unknown parameter mode"):
        to_mermaid(load_fixture("example_workflow.json"), params="some")


def test_labels_escaped_and_ids_unique(bilayers_raw):
    bilayers_raw["inputs"][0]["label"] = 'Say "hi" <b>#1</b> `code`'
    first, second = bilayers_raw["parameters"][:2]
    first["name"], second["name"] = "a-b", "a.b"
    found = nodes(to_mermaid(load_raw(bilayers_raw), params="all"))
    assert found["in_dir"].split("<br/>")[0] == "<b>Say #quot;hi#quot; #lt;b#gt;#35;1#lt;/b#gt; #96;code#96;</b>"
    assert {"param_a_b", "param_a_b_2"} <= found.keys()
