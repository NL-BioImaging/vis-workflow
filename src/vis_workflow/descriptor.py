"""Load a workflow descriptor into biomero-schema, keeping the raw descriptor for diagram details."""
import json
from dataclasses import dataclass, field

import yaml
from biomero_schema.adapters import detect_schema_format, parse_descriptor
from biomero_schema.models import OutputParameter, Parameter, WorkflowSchema

# biomero-schema input types that carry data (files/folders); all others are parameters
DATA_TYPES = {"image", "file", "array", "measurement", "executable"}


@dataclass(frozen=True)
class Descriptor:
    raw: dict
    workflow: WorkflowSchema
    format: str
    sections: dict[str, str] = field(default_factory=dict)

    @property
    def name(self) -> str:
        return self.workflow.name

    @property
    def data_inputs(self) -> list[Parameter]:
        return [param for param in self.workflow.inputs if param.type in DATA_TYPES]

    @property
    def parameters(self) -> list[Parameter]:
        return [param for param in self.workflow.inputs if param.type not in DATA_TYPES]

    @property
    def outputs(self) -> list[OutputParameter]:
        return self.workflow.outputs

    @property
    def image(self) -> str:
        image = self.workflow.container_image.image
        # biomero-schema leaves out the Bilayers image tag
        tag = (self.raw.get("docker_image") or {}).get("tag")
        if tag and ":" not in image.rsplit("/", 1)[-1]:
            image = f"{image}:{tag}"
        return image


def load_descriptor(text: str, name: str | None = None) -> Descriptor:
    """Parse descriptor text (JSON or YAML; Bilayers, BIAFLOWS or biomero-schema)."""
    try:
        raw = json.loads(text)
    except json.JSONDecodeError:
        raw = yaml.safe_load(text)
    if not isinstance(raw, dict):
        label = f"'{name}' " if name else ""
        raise ValueError(f"Descriptor {label}is not a mapping of descriptor fields")
    return Descriptor(
        raw=raw,
        workflow=parse_descriptor(raw, name=name),
        format=detect_schema_format(raw),
        sections=_bilayers_sections(raw),
    )


def _bilayers_sections(raw: dict) -> dict[str, str]:
    sections = {}
    for key in ("inputs", "parameters", "outputs"):
        for item in raw.get(key) or []:
            if item.get("section_id") and "name" in item:
                sections[item["name"]] = item["section_id"]
    return sections
