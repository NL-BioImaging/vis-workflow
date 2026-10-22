# Working conventions for this repo

Follow these when making changes here. Design: [notes/design.md](notes/design.md).

## Descriptor parsing
- Read descriptors only through `biomero_schema.adapters.parse_descriptor()` - never write a parallel Bilayers/BIAFLOWS parser here.
- An adapter bug or missing mapping is fixed upstream in biomero-schema (local clone `C:/Users/defoltj/github/biomero-schema`, origin NL-BioImaging/biomero-schema), on a branch with a PR to its `main`.
- Fields not in `WorkflowSchema` may be read from the raw descriptor next to it, only where the diagram needs them.
- Python and browser (Pyodide) run the same code: keep the core (`parse`, `to_mermaid`) pure Python with no file/network access; I/O lives in the CLI and the web loader.

## Diagram
- The Mermaid diagram is the main output; everything else (details panel, CLI) supports it.
- Generated Mermaid must render on GitHub as well as in mermaid.js: escape labels, quote node text, no features newer than GitHub's Mermaid version.
- Node ids come from sanitised descriptor ids, never from labels.

## Comments
- Code comments: 1-2 lines max, even for non-obvious WHY reasoning. No multi-line rationale blocks.
- Never narrate what changed, reference the current fix/task, or mention specific callers/sessions in a comment - that belongs in the commit message or chat response, not the code.
- Comments explain WHY (a hidden constraint, a subtle invariant), never WHAT (identifiers already say that).

## Testing
- Keep tests as small and fast as possible: the fewest cases that cover each path, no overlapping tests, no repeated loading of large fixtures where a small one does.
- Fixtures in `tests/fixtures/`: cideconvolve `config.yaml` (Bilayers, large), WB_Measurements-CellProfiler `config.yaml` (Bilayers, small, measurement output), biomero-schema's `bilayers_example.yaml`, `W_NucleiSegmentation-ImageJ.descriptor.json` (BIAFLOWS) and `example_workflow.json` (native).
- Test Mermaid output structurally (nodes, edges, labels present), plus one snapshot per fixture - not by eye. Update snapshots with `VIS_WORKFLOW_UPDATE_SNAPSHOTS=1`.
- After a diagram change, check it actually renders (no Node install needed; uses the installed Edge): `PUPPETEER_SKIP_DOWNLOAD=true pixi exec --spec nodejs -- npx.cmd -y @mermaid-js/mermaid-cli@11 -p puppeteer.json -i x.mmd -o x.png`, with `puppeteer.json`: `{"executablePath": "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"}`.
- Tests never hit the network; URL handling is tested on the rewrite logic with fixed strings. The one exception is the opt-in portal smoke test (`tests/test_portal.py`, loads Pyodide and Mermaid from the CDN): run it after a portal change with `python web/build.py` then `VIS_WORKFLOW_BROWSER=msedge pytest tests/test_portal.py` (needs the `browser` extra). CI runs it before every Pages deploy.
- Before adding a test, check for an existing one covering the same path - extend or parametrize it rather than adding a near-duplicate.
- Add tests to the existing file matching the module under test; only a substantial, self-contained feature gets its own test file.

## Code style
- Avoid `continue` statements - restructure the loop body (e.g. invert the condition) instead.
- No single-letter variable names, comprehension variables included: `param for param in params`, not `p for p in params`.
- Reuse as much as possible: existing libraries (biomero-schema, mermaid) and existing code here; extend a helper rather than duplicate a block, and never write a new module that parallels an existing one.
- No atomic one-line wrapper functions; keep code intuitive over clever.
- For a restructure, write a detailed plan first and agree it before editing.

## Carrying work across sessions
- Record the current task, its plan and how far it got under "In progress" in `notes/todo_known_issues.md` before editing code, and keep it updated. Clear it once the task is done.
- On "continue" with no other context, read that section first and resume from it.
- Design decisions go in `notes/design.md`, with the reason; update it when a decision changes rather than appending a contradiction.

## Git
- Small, focused commits with a "why" in the message, not a changelog of "what".
- Work on `main` by default; create a branch only for major restructures or features.
- Never create git worktrees (no `EnterWorktree`, no `isolation: "worktree"` agents, no `git worktree add`).
