"""Render a Descriptor as a Mermaid flowchart: data inputs -> tool -> outputs, with parameters."""
import math
import re

from vis_workflow.descriptor import Descriptor

# all: advanced parameters in their own box; beginner: advanced ones summarised in one node;
# grouped: one box per Bilayers section_id
PARAM_MODES = ("all", "beginner", "grouped", "collapsed", "none")
MAX_FORMATS = 4
MAX_TEXT = 40
MAX_COMMAND = 60
# Parameter grid: one column up to GRID_ROWS parameters, then more columns up to GRID_MAX_COLUMNS
GRID_ROWS = 7
GRID_MAX_COLUMNS = 4


def to_mermaid(descriptor: Descriptor, params: str = "all") -> str:
    if params not in PARAM_MODES:
        raise ValueError(f"Unknown parameter mode '{params}', expected one of {PARAM_MODES}")
    node_ids = _NodeIds()
    inputs = [(node_ids.make("in", param.id), param) for param in descriptor.data_inputs]
    outputs = [(node_ids.make("out", param.id), param) for param in descriptor.outputs]
    param_lines = _parameter_lines(descriptor, params, node_ids)

    lines = ["flowchart LR"]
    lines.extend(_subgraph("inputs", "Inputs", _data_nodes(inputs)))
    lines.append(f'  tool[["{_tool_label(descriptor)}"]]')
    lines.extend(_subgraph("parameters", "Parameters", param_lines))
    lines.extend(_subgraph("outputs", "Outputs", _data_nodes(outputs)))
    lines.extend(f"  {node_id} --> tool" for node_id, _ in inputs)
    if param_lines:
        lines.append("  parameters -.-> tool")
    lines.extend(f"  tool --> {node_id}" for node_id, _ in outputs)
    return "\n".join(lines) + "\n"


def _subgraph(subgraph_id: str, title: str, body: list[str], indent: str = "  ") -> list[str]:
    if not body:
        return []
    return [f'{indent}subgraph {subgraph_id}["{_escape(title)}"]', *body, f"{indent}end"]


def _data_nodes(nodes) -> list[str]:
    return [f'    {node_id}[/"{_data_label(param)}"/]' for node_id, param in nodes]


def _parameter_lines(descriptor: Descriptor, mode: str, node_ids: "_NodeIds") -> list[str]:
    params = descriptor.parameters
    if mode == "none" or not params:
        return []
    if mode == "collapsed":
        return [f'    {node_ids.make("param", "summary")}["{_plural(len(params), "parameter")}"]']
    if mode == "grouped":
        sections = {}
        for param in params:
            sections.setdefault(descriptor.sections.get(param.id, "other"), []).append(param)
        return _group_lines(sections, node_ids)
    basic = [param for param in params if param.mode != "advanced"]
    advanced = [param for param in params if param.mode == "advanced"]
    if mode == "beginner":
        nodes = _param_nodes(basic, node_ids)
        if advanced:
            nodes.append((node_ids.make("param", "advanced"), f"+{_plural(len(advanced), 'advanced parameter')}"))
        return ["    direction LR", *_param_grid(nodes)]
    if basic and advanced:
        return _group_lines({"Basic": basic, "Advanced": advanced}, node_ids)
    return ["    direction LR", *_param_grid(_param_nodes(params, node_ids))]


def _group_lines(groups: dict[str, list], node_ids: "_NodeIds") -> list[str]:
    # Unlinked boxes are placed in no fixed order: chain them top-down with invisible links
    lines = ["    direction TB"]
    group_ids = []
    for name, group_params in groups.items():
        group_id = node_ids.make("group", name)
        group_ids.append(group_id)
        grid = [f"  {line}" for line in _param_grid(_param_nodes(group_params, node_ids))]
        lines.extend(_subgraph(group_id, name, ["      direction LR", *grid], "    "))
    if len(group_ids) > 1:
        lines.append("    " + " ~~~ ".join(group_ids))
    return lines


def _param_nodes(params, node_ids: "_NodeIds") -> list[tuple[str, str]]:
    return [(node_ids.make("param", param.id), _param_label(param)) for param in params]


def _param_grid(nodes: list[tuple[str, str]]) -> list[str]:
    """Node lines plus invisible links chaining each row, so many parameters form a grid."""
    columns = min(GRID_MAX_COLUMNS, math.ceil(len(nodes) / GRID_ROWS))
    lines = [f'    {node_id}["{label}"]' for node_id, label in nodes]
    for start in range(0, len(nodes), columns):
        row = [node_id for node_id, _ in nodes[start:start + columns]]
        if len(row) > 1:
            lines.append("    " + " ~~~ ".join(row))
    return lines


def _label(title: str, details=()) -> str:
    """Bold title, then one line per detail."""
    return "<br/>".join([f"<b>{_escape(title)}</b>", *(_escape(detail) for detail in details)])


def _param_label(param) -> str:
    default = param.default_value
    if isinstance(default, bool):
        default = str(default).lower()
    details = [] if default is None or default == "" else [_shorten(str(default))]
    return _label(_shorten(param.name or param.id), details)


def _data_label(param) -> str:
    name = param.name or param.id
    if param.optional:
        name += " (optional)"
    formats = param.format if isinstance(param.format, list) else [param.format] if param.format else []
    formats_text = ", ".join(formats[:MAX_FORMATS]) + (" …" if len(formats) > MAX_FORMATS else "")
    # Bilayers marks data not passed on the command line with cli_tag "None"
    flag = param.command_line_flag if param.command_line_flag != "None" else None
    details = [("type", param.type), ("formats", formats_text), ("files", param.file_count), ("flag", flag)]
    return _label(name, [f"{key}: {value}" for key, value in details if value])


def _tool_label(descriptor: Descriptor) -> str:
    details = [f"container: {descriptor.image}"]
    if descriptor.workflow.command_line:
        details.append(f"command: {_shorten(descriptor.workflow.command_line, MAX_COMMAND)}")
    return _label(descriptor.name, details)


def _escape(text: str) -> str:
    # '#' first: Mermaid entity codes themselves start with '#'
    text = str(text).replace("#", "#35;")
    for char, code in (('"', "#quot;"), ("<", "#lt;"), (">", "#gt;"), ("`", "#96;")):
        text = text.replace(char, code)
    return " ".join(text.split())


def _shorten(text: str, max_length: int = MAX_TEXT) -> str:
    return text if len(text) <= max_length else text[:max_length - 1] + "…"


def _plural(count: int, noun: str) -> str:
    return f"{count} {noun}" + ("" if count == 1 else "s")


class _NodeIds:
    """Unique Mermaid node ids from descriptor ids (labels may contain anything)."""

    def __init__(self):
        self.used = set()

    def make(self, prefix: str, name: str) -> str:
        base = prefix + "_" + re.sub(r"\W", "_", str(name), flags=re.ASCII)
        node_id = base
        count = 1
        while node_id in self.used:
            count += 1
            node_id = f"{base}_{count}"
        self.used.add(node_id)
        return node_id
