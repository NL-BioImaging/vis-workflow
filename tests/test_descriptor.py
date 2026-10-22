import pytest

from conftest import FIXTURES, load_fixture, load_raw
from vis_workflow import load_descriptor


@pytest.mark.parametrize("name, schema_format, data_inputs, parameters, outputs, image", [
    ("cideconvolve_config.yaml", "bilayers", 1, 41, 1, "cellularimagingcf/w_cideconvolve:v3.3.0"),
    ("bilayers_example.yaml", "bilayers", 2, 7, 1, "cellprofiler/runcellpose_no_pretrained:2.3.2"),
    ("W_NucleiSegmentation-ImageJ.descriptor.json", "BIAFLOWS", 0, 2, 0, "neubiaswg5/w_nucleisegmentation-imagej"),
    ("example_workflow.json", "biomero-schema", 2, 2, 2, "neubiaswg5/w_nucleitracking-imagej:1.0.0"),
])
def test_load(name, schema_format, data_inputs, parameters, outputs, image):
    descriptor = load_fixture(name)
    assert descriptor.format == schema_format
    assert len(descriptor.data_inputs) == data_inputs
    assert len(descriptor.parameters) == parameters
    assert len(descriptor.outputs) == outputs
    # Bilayers tag added from the raw descriptor, never twice
    assert descriptor.image == image


def test_bilayers_sections_from_raw():
    descriptor = load_fixture("cideconvolve_config.yaml")
    assert descriptor.sections["infolder"] == "inputs"
    assert {descriptor.sections[param.id] for param in descriptor.parameters} == {"essential", "method", "advanced"}
    assert load_fixture("example_workflow.json").sections == {}


def test_json_and_yaml_text_give_same_workflow(bilayers_raw):
    assert load_raw(bilayers_raw).workflow == load_fixture("bilayers_example.yaml").workflow


@pytest.mark.parametrize("text", ["just text", ""])
def test_non_mapping_rejected(text):
    with pytest.raises(ValueError, match="not a mapping"):
        load_descriptor(text, name="bad.yaml")


def test_unknown_format_rejected():
    with pytest.raises(ValueError, match="Unable to detect schema format"):
        load_descriptor('{"unsupported": "format"}')
