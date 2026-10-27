import re

import pytest

from conftest import FIXTURE_NAMES, load_fixture, load_raw, nodes
from vis_workflow import node_descriptions, to_mermaid


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_diagram(name, snapshot):
    descriptor = load_fixture(name)
    text = to_mermaid(descriptor)
    snapshot(name.split(".")[0] + ".mmd", text)
    found = nodes(text)
    described = [param for param in descriptor.workflow.inputs + descriptor.outputs if param.description]
    descriptions = node_descriptions(descriptor)
    assert descriptions.keys() <= found.keys()
    assert len(descriptions) == len(described) + bool(descriptor.workflow.description)
    assert text.count("subgraph") == text.count("  end")
    for param in descriptor.data_inputs:
        assert f"  in_{param.id} --> tool" in text
    for param in descriptor.outputs:
        assert f"  tool --> out_{param.id}" in text


@pytest.mark.parametrize("mode, shown, summary, rows, hint", [
    ("all", 41, None, None, None),
    ("beginner", 19, "+22 advanced parameters", [3] * 6 + [2], ("param_advanced", 22)),
    ("collapsed", 0, "41 parameters", [], ("param_summary", 41)),
    ("none", 0, None, [], None),
])
def test_parameter_modes(mode, shown, summary, rows, hint):
    descriptor = load_fixture("cideconvolve_config.yaml")
    text = to_mermaid(descriptor, params=mode)
    found = nodes(text)
    assert len([node_id for node_id in found if node_id.startswith("param_")]) == shown + bool(summary)
    assert summary is None or summary in found.values()
    assert rows is None or [line.count("~~~") + 1 for line in text.splitlines() if "~~~" in line] == rows
    assert ("parameters -.-> tool" in text) == (mode != "none")
    # Summary nodes list the names of the parameters they stand for
    assert hint is None or len(node_descriptions(descriptor, params=mode)[hint[0]].splitlines()) == hint[1]


@pytest.mark.parametrize("name, mode, declared, chains", [
    # Sections nested in Basic; Advanced has one section, so it merges into the Advanced box
    ("cideconvolve_config.yaml", "all", ["Basic", "essential", "method", "Advanced"],
     [["essential", "method"], ["Basic", "Advanced"]]),
    ("cideconvolve_config.yaml", "grouped", ["essential", "advanced", "method"], [["essential", "advanced", "method"]]),
    # All basic: the Basic level merges away, leaving the sections
    ("wb_measurements_config.yaml", "all", ["masks", "measurements"], [["masks", "measurements"]]),
    ("example_workflow.json", "grouped", [], []),
    ("example_workflow.json", "all", [], []),
])
def test_groups_nested_in_descriptor_order(name, mode, declared, chains):
    text = to_mermaid(load_fixture(name), params=mode)
    assert re.findall(r'subgraph group_\w+\["([^"]+)"\]', text) == declared
    assert [line.strip().replace("group_", "").split(" ~~~ ") for line in text.splitlines()
            if "~~~ group_" in line] == chains


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
