# Known issues and TODO

Test descriptors: cideconvolve
[config.yaml](https://github.com/Cellular-Imaging-Amsterdam-UMC/cideconvolve/blob/main/config.yaml) (Bilayers,
41 parameters), WB_Measurements-CellProfiler
[config.yaml](https://github.com/Cellular-Imaging-Amsterdam-UMC/WB_Measurements-CellProfiler/blob/master/config.yaml)
(Bilayers, 4 parameters, measurement output), biomero-schema `tests/bilayers_example.yaml` (Cellpose), `tests/W_NucleiSegmentation-ImageJ.descriptor.json`
(BIAFLOWS), `tests/example_workflow.json` (native). Design: [design.md](design.md).
Portal: https://nl-bioimaging.github.io/vis-workflow/

## In progress

(none)

## TODO
- Switch dependency to the biomero-schema release once PR #8 is released.
- Gallery of known Bilayers/BIOMERO workflows; embed mode.
- Multi-step pipelines: chain tools by matching output -> input types.

## Known issues

### biomero-schema PR #8 not merged yet
[PR #8](https://github.com/NL-BioImaging/biomero-schema/pull/8) is needed to parse Bilayers descriptors. Until
released, install from branch `feature/bilayers-adapter`.

### BIAFLOWS diagrams have no data nodes
BIAFLOWS descriptors have no outputs, and their data inputs are the Cytomine ones the parser filters out, so only
the tool and parameters show.

### PNG export: wrapped titles only partly bold
The PNG is rendered with plain SVG text labels, where `<b>` is not supported; the first line of each node is made
bold instead, so a title that wraps (e.g. "Excitation Wavelengths / (nm)") is bold on its first line only.
