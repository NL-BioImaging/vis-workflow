import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11.17.2/dist/mermaid.esm.min.mjs";

const PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v314.0.7/full/";
const EXAMPLES = {
  "cideconvolve (Bilayers)": "https://github.com/Cellular-Imaging-Amsterdam-UMC/cideconvolve",
  "WB Measurements (Bilayers)": "https://github.com/Cellular-Imaging-Amsterdam-UMC/WB_Measurements-CellProfiler",
  "InstanSeg (Bilayers)":
    "https://github.com/bilayer-containers/bilayers/blob/main/tests/fixtures/instanseg_inference/config.yaml",
  "NucleiSegmentation (BIAFLOWS)": "https://github.com/Neubias-WG5/W_NucleiSegmentation-ImageJ",
  "NucleiTracking (biomero-schema)":
    "https://github.com/NL-BioImaging/biomero-schema/blob/main/tests/example_workflow.json",
};

// Same functions as the CLI; errors come back as text rather than Python tracebacks
const GLUE = `
import json
from vis_workflow import load_descriptor, node_descriptions, to_mermaid
from vis_workflow.sources import candidate_urls

descriptor = None

def load(text, name):
    global descriptor
    try:
        descriptor = load_descriptor(text, name=name)
    except Exception as error:
        return json.dumps({"error": str(error)})
    return json.dumps({"format": descriptor.format, "image": descriptor.image,
                       "workflow": descriptor.workflow.model_dump(mode="json", by_alias=True)})

def diagram(params):
    return json.dumps({"mermaid": to_mermaid(descriptor, params=params),
                       "descriptions": node_descriptions(descriptor, params=params)})

def candidates(source):
    return json.dumps(candidate_urls(source))
`;

const element = (id) => document.getElementById(id);
const dark = window.matchMedia("(prefers-color-scheme: dark)").matches;
// Rendered at natural size; the "Fit to width" toggle scales it with CSS, no re-render
mermaid.initialize({
  startOnLoad: false,
  securityLevel: "strict",
  theme: dark ? "dark" : "default",
  flowchart: { useMaxWidth: false },
});

const python = startPython();
let mermaidText = "";
let workflowName = "workflow";

async function startPython() {
  const { loadPyodide } = await import(PYODIDE_URL + "pyodide.mjs");
  const pyodide = await loadPyodide({ indexURL: PYODIDE_URL });
  await pyodide.loadPackage(["micropip", "pydantic", "pyyaml"]);
  const wheels = await (await fetch("wheels/wheels.json")).json();
  pyodide.globals.set("wheel_urls", wheels.map((name) => new URL(`wheels/${name}`, location.href).href));
  await pyodide.runPythonAsync("import micropip\nawait micropip.install(wheel_urls.to_py(), deps=False)");
  pyodide.runPython(GLUE);
  return pyodide;
}

function setStatus(text, isError = false) {
  element("status").textContent = text;
  element("status").classList.toggle("error", isError);
}

async function fetchDescriptor(urls) {
  for (const url of urls) {
    let response;
    try {
      response = await fetch(url);
    } catch {
      throw new Error(`Could not fetch ${url}: the server may not allow cross-origin requests (CORS), ` +
        "or it is unreachable. A local file can be shown with: vis-workflow view <file>");
    }
    if (response.ok) {
      return { text: await response.text(), url };
    }
    // Missing candidates are expected while discovering a directory's descriptor
    if (response.status !== 404) {
      throw new Error(`${url}: HTTP ${response.status}`);
    }
  }
  throw new Error(`No descriptor found, tried:\n${urls.join("\n")}`);
}

async function show(source) {
  element("result").hidden = true;
  try {
    setStatus("Loading Python (first time takes a few seconds)…");
    const pyodide = await python;
    setStatus("Fetching descriptor…");
    const urls = JSON.parse(pyodide.globals.get("candidates")(source));
    const { text, url } = await fetchDescriptor(urls);
    const loaded = JSON.parse(pyodide.globals.get("load")(text, url));
    if (loaded.error) {
      throw new Error(`${url}:\n${loaded.error}`);
    }
    workflowName = loaded.workflow.name || "workflow";
    showDetails(loaded, url);
    await renderDiagram();
    setStatus("");
    element("result").hidden = false;
  } catch (error) {
    setStatus(error.message, true);
  }
}

async function renderDiagram() {
  const pyodide = await python;
  const { mermaid: text, descriptions } = JSON.parse(pyodide.globals.get("diagram")(element("params").value));
  mermaidText = text;
  const { svg } = await mermaid.render("diagram-svg", mermaidText);
  element("diagram").innerHTML = svg;
  addHoverHints(descriptions);
}

// An SVG <title> shows as a native tooltip, and stays in the downloaded SVG
function addHoverHints(descriptions) {
  for (const node of element("diagram").querySelectorAll("svg .node")) {
    const nodeId = node.id.match(/-flowchart-(.+)-\d+$/)?.[1];
    if (descriptions[nodeId]) {
      const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
      title.textContent = descriptions[nodeId];
      node.prepend(title);
    }
  }
}

function showDetails({ format, image, workflow }, url) {
  const details = element("details");
  details.replaceChildren();
  const add = (term, value) => {
    if (!value) {
      return;
    }
    const dt = document.createElement("dt");
    dt.textContent = term;
    const dd = document.createElement("dd");
    dd.append(value);
    details.append(dt, dd);
  };
  add("Name", workflow.name);
  add("Description", workflow.description);
  add("Format", format);
  add("Container", image);
  add("Command", workflow["command-line"]);
  for (const citation of workflow.citations) {
    const value = document.createElement("span");
    value.textContent = [citation.name, citation.license].filter(Boolean).join(" · ") + " ";
    const doi = citation.doi || "";
    const href = doi.startsWith("10.") ? `https://doi.org/${doi}` : doi;
    if (/^https?:\/\//.test(href)) {
      const link = document.createElement("a");
      link.href = href;
      link.textContent = doi;
      value.append(link);
    }
    add("Citation", value);
  }
  add("Descriptor", Object.assign(document.createElement("a"), { href: url, textContent: url }));
}

function updateAddress(source) {
  const query = new URLSearchParams({ source });
  if (element("params").value !== "all") {
    query.set("params", element("params").value);
  }
  history.replaceState(null, "", `?${query}`);
}

function save(blob, extension) {
  const link = Object.assign(document.createElement("a"), {
    href: URL.createObjectURL(blob),
    download: `${workflowName}.${extension}`,
  });
  link.click();
  URL.revokeObjectURL(link.href);
}

async function downloadPng() {
  // HTML labels (foreignObject) block canvas export, so re-render with plain SVG text labels, which
  // show <b> literally: strip it (user text has '<' escaped) and bold each node's first line instead
  const plainText = mermaidText.replaceAll("<b>", "").replaceAll("</b>", "");
  const { svg } = await mermaid.render("png-svg", `%%{init: {"htmlLabels": false}}%%\n${plainText}`);
  const svgElement = new DOMParser().parseFromString(svg, "image/svg+xml").documentElement;
  const style = document.createElementNS("http://www.w3.org/2000/svg", "style");
  style.textContent = ".node text > tspan:first-child tspan { font-weight: bold; }";
  svgElement.append(style);
  const { width, height } = svgElement.viewBox.baseVal;
  svgElement.setAttribute("width", width);
  svgElement.setAttribute("height", height);

  const image = new Image();
  image.src = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(new XMLSerializer().serializeToString(svgElement))}`;
  await image.decode();
  const scale = 2;
  const canvas = Object.assign(document.createElement("canvas"), { width: width * scale, height: height * scale });
  const context = canvas.getContext("2d");
  context.fillStyle = getComputedStyle(element("diagram")).backgroundColor;
  context.fillRect(0, 0, canvas.width, canvas.height);
  context.drawImage(image, 0, 0, canvas.width, canvas.height);
  save(await new Promise((resolve) => canvas.toBlob(resolve, "image/png")), "png");
}

for (const [label, url] of Object.entries(EXAMPLES)) {
  const link = Object.assign(document.createElement("a"), {
    href: `?${new URLSearchParams({ source: url })}`,
    textContent: label,
  });
  element("examples").append(link);
}

element("source-form").addEventListener("submit", (event) => {
  event.preventDefault();
  updateAddress(element("source").value);
  show(element("source").value);
});
element("params").addEventListener("change", () => {
  updateAddress(element("source").value);
  renderDiagram();
});
element("fit").addEventListener("change", () => {
  element("diagram").classList.toggle("fit", element("fit").checked);
});
element("copy").addEventListener("click", async () => {
  await navigator.clipboard.writeText(mermaidText);
  setStatus("Mermaid copied - paste it into a ```mermaid block on GitHub.");
});
element("download").addEventListener("click", () => {
  // XML, not innerHTML: label HTML such as <br> must be well-formed for a standalone SVG file
  const svg = new XMLSerializer().serializeToString(element("diagram").querySelector("svg"));
  save(new Blob([svg], { type: "image/svg+xml" }), "svg");
});
element("download-png").addEventListener("click", () => {
  downloadPng().catch((error) => setStatus(`PNG export failed: ${error.message}`, true));
});

const query = new URLSearchParams(location.search);
if (query.has("params")) {
  element("params").value = query.get("params");
}
if (query.get("source")) {
  element("source").value = query.get("source");
  show(query.get("source"));
}
