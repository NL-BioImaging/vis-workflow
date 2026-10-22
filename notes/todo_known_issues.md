# Known issues and TODO

Test descriptors: cideconvolve
[config.yaml](https://github.com/Cellular-Imaging-Amsterdam-UMC/cideconvolve/blob/main/config.yaml) (Bilayers,
~40 parameters), biomero-schema `tests/bilayers_example.yaml` (Cellpose), `tests/W_NucleiSegmentation-ImageJ.descriptor.json`
(BIAFLOWS), `tests/example_workflow.json` (native). Design: [design.md](design.md).

## In progress

(none)

## TODO

### 1. Package core: parse + Mermaid
- Python package `vis_workflow` (pyproject, src layout), dependency on biomero-schema PR #8 branch.
- Loader returning raw descriptor + parsed `WorkflowSchema`, with data inputs and parameters distinguished
  (by type) for the diagram.
- `to_mermaid()` with parameter modes collapsed/beginner/grouped/all; tests on the four fixtures.

### 2. CLI
- `vis-workflow mermaid`, `convert`, `view` (local CORS server + open portal).
- URL rewriting (GitHub blob/tree -> raw, descriptor auto-discovery), tested on fixed strings.

### 3. Web portal
- Static page with `?source=`, Pyodide loading the package wheel, mermaid.js render, option toggles,
  SVG/PNG download, copy Mermaid, details panel, errors.
- GitHub Actions: tests, build wheel, deploy Pages.

### 4. Later
- Gallery of known Bilayers/BIOMERO workflows; embed mode.
- Multi-step pipelines: chain tools by matching output -> input types.
- Switch dependency to the biomero-schema release once PR #8 is released.

## Known issues

### biomero-schema PR #8 not merged yet
[PR #8](https://github.com/NL-BioImaging/biomero-schema/pull/8) is needed to parse Bilayers descriptors. Until
released, install from branch `feature/bilayers-adapter`.
