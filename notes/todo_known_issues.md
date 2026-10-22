# Known issues and TODO

Test descriptors: cideconvolve
[config.yaml](https://github.com/Cellular-Imaging-Amsterdam-UMC/cideconvolve/blob/main/config.yaml) (Bilayers,
41 parameters), WB_Measurements-CellProfiler
[config.yaml](https://github.com/Cellular-Imaging-Amsterdam-UMC/WB_Measurements-CellProfiler/blob/master/config.yaml)
(Bilayers, 4 parameters, measurement output), biomero-schema `tests/bilayers_example.yaml` (Cellpose), `tests/W_NucleiSegmentation-ImageJ.descriptor.json`
(BIAFLOWS), `tests/example_workflow.json` (native). Design: [design.md](design.md).

## In progress

(none)

## TODO

### 1. Package core: parse + Mermaid - done
`load_descriptor()` -> `Descriptor`, `to_mermaid()` with modes beginner/all/grouped/collapsed/none; 21 tests,
snapshots in `tests/snapshots/` (update with `VIS_WORKFLOW_UPDATE_SNAPSHOTS=1`).

To check rendering (no Node install needed; uses installed Edge instead of downloading Chrome):
`PUPPETEER_SKIP_DOWNLOAD=true pixi exec --spec nodejs -- npx.cmd -y @mermaid-js/mermaid-cli@11 -p puppeteer.json -i x.mmd -o x.png`
with `puppeteer.json`: `{"executablePath": "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"}`.

### 2. CLI - done
`vis-workflow mermaid|convert|view`, GitHub URL resolution with descriptor discovery; 35 tests in 0.25s.
`view` on a local file is untested end to end until the portal exists (phase 3); its server is tested.

### 3. Web portal - done locally, not deployed
`web/` + `.github/workflows/pages.yml`. Checked in Edge via Playwright (scratch script, not in the repo): the four
examples, a local file through the `view` server (grouped mode), the missing-repo error, mode switch, fit toggle,
dark theme, phone width.
- To deploy: push to main with Pages source set to "GitHub Actions" (repository settings).
- No automated browser test in CI yet; could add a Playwright smoke test of one example.
- PNG download left out: Mermaid's HTML labels make a canvas export tainted; SVG download covers it.

### 4. Later
- Gallery of known Bilayers/BIOMERO workflows; embed mode.
- Multi-step pipelines: chain tools by matching output -> input types.
- Switch dependency to the biomero-schema release once PR #8 is released.

## Known issues

### biomero-schema PR #8 not merged yet
[PR #8](https://github.com/NL-BioImaging/biomero-schema/pull/8) is needed to parse Bilayers descriptors. Until
released, install from branch `feature/bilayers-adapter`.

### Grouped mode: section order not kept
Mermaid stacks the section subgraphs in its own order (cideconvolve: method, advanced, essential rather than the
descriptor's essential, method, advanced). Cosmetic; declaring them in reverse would depend on layout internals.

### BIAFLOWS diagrams have no data nodes
BIAFLOWS descriptors have no outputs, and their data inputs are the Cytomine ones the parser filters out, so only
the tool and parameters show.
