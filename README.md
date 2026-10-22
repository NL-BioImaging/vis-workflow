# vis-workflow
Workflow visualiser: shows a bioimage workflow descriptor - [Bilayers](https://bilayers.org/understanding-config/)
`config.yaml`, BIAFLOWS `descriptor.json` or [biomero-schema](https://github.com/NL-BioImaging/biomero-schema)
JSON - as a Mermaid diagram of its inputs, parameters and outputs.

```mermaid
flowchart LR
  subgraph inputs["Inputs"]
    in_infolder[/"Input Images<br/>image · tif, tiff, ometif, ometiff … · multiple<br/>--infolder"/]
  end
  tool[["cideconvolve<br/>cellularimagingcf/w_cideconvolve:v3.3.0<br/>python wrapper.py"]]
  subgraph parameters["Parameters"]
    param_summary["41 parameters"]
  end
  subgraph outputs["Outputs"]
    out_output_dir[/"Deconvolved Outputs<br/>image · ometiff, tif, tiff, zarr … · multiple<br/>--outfolder"/]
  end
  in_infolder --> tool
  parameters -.-> tool
  tool --> out_output_dir
```

## Install
```bash
pip install -e .[test]
```

## Usage
```bash
# SOURCE: a descriptor file, a directory/repository with descriptor.json, descriptor.yaml or config.yaml, or a URL
vis-workflow mermaid https://github.com/Cellular-Imaging-Amsterdam-UMC/cideconvolve
vis-workflow mermaid config.yaml --params all -o diagram.md   # .md gets a mermaid code block
vis-workflow convert config.yaml -o descriptor.json           # biomero-schema JSON
vis-workflow view config.yaml                                 # open in the web portal
```

From Python:
```python
from vis_workflow import load_descriptor, to_mermaid

descriptor = load_descriptor(open("config.yaml", encoding="utf-8").read())
print(to_mermaid(descriptor, params="beginner"))
```

Parameter modes: `beginner` (default; advanced parameters summarised), `all`, `grouped` (by Bilayers section),
`collapsed` (one summary node), `none`.

Design and plans: [notes/design.md](notes/design.md), [notes/todo_known_issues.md](notes/todo_known_issues.md).
