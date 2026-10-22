"""Command line: render, convert or view a workflow descriptor from a file, directory or URL."""
import functools
import http.server
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from urllib.parse import quote

import click
import yaml

from vis_workflow.descriptor import Descriptor, load_descriptor
from vis_workflow.mermaid import PARAM_MODES, to_mermaid
from vis_workflow.sources import DESCRIPTOR_FILES, PORTAL_URL, candidate_urls, portal_url

OUTPUT_OPTION = click.option(
    "-o", "--output", type=click.Path(dir_okay=False, path_type=Path), help="Write to this file instead of stdout."
)


@click.group()
@click.version_option(package_name="vis-workflow")
def cli():
    """Visualise workflow descriptors (Bilayers, BIAFLOWS, biomero-schema).

    SOURCE is a descriptor file, a directory or repository containing descriptor.json, descriptor.yaml or
    config.yaml, or a URL (GitHub file, tree and repository URLs are resolved to raw files).
    """


@cli.command()
@click.argument("source")
@click.option("--params", type=click.Choice(PARAM_MODES), default=PARAM_MODES[0], show_default=True,
              help="How to show parameters.")
@OUTPUT_OPTION
def mermaid(source, params, output):
    """Write the Mermaid diagram; a .md output file gets a mermaid code block."""
    text = to_mermaid(_load(source), params=params)
    if output and output.suffix.lower() == ".md":
        text = f"```mermaid\n{text}```\n"
    _write(text, output)


@cli.command()
@click.argument("source")
@OUTPUT_OPTION
def convert(source, output):
    """Write the descriptor as biomero-schema JSON."""
    _write(_load(source).workflow.model_dump_json(indent=2, by_alias=True) + "\n", output)


@cli.command()
@click.argument("source")
@click.option("--port", default=8000, show_default=True, help="Local port for serving a local file.")
@click.option("--portal", default=PORTAL_URL, show_default=True, help="Web portal to open.")
def view(source, port, portal):
    """Open SOURCE in the web portal; a local file is served on 127.0.0.1 for it."""
    if "://" in source:
        webbrowser.open(portal_url(source, portal))
        return
    _, location = read_source(source)
    file_path = Path(location).resolve()
    server = make_server(file_path, port)
    url = f"http://127.0.0.1:{server.server_port}/{quote(file_path.name)}"
    click.echo(f"Serving {file_path} at {url} - press Ctrl+C to stop")
    webbrowser.open(portal_url(url, portal))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def read_source(source: str) -> tuple[str, str]:
    """Descriptor text and where it was found, from a local file or directory or a URL."""
    path = Path(source)
    if path.is_file():
        return path.read_text(encoding="utf-8"), source
    if path.is_dir():
        found = [path / name for name in DESCRIPTOR_FILES if (path / name).is_file()]
        if not found:
            raise click.ClickException(f"No {', '.join(DESCRIPTOR_FILES)} in {source}")
        return found[0].read_text(encoding="utf-8"), str(found[0])
    if "://" not in source:
        raise click.ClickException(f"No such file or directory: {source}")
    urls = candidate_urls(source)
    for url in urls:
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                return response.read().decode("utf-8"), url
        except urllib.error.HTTPError as error:
            # Missing candidates are expected while discovering a directory's descriptor
            if error.code != 404:
                raise click.ClickException(f"{url}: HTTP {error.code} {error.reason}")
        except urllib.error.URLError as error:
            raise click.ClickException(f"{url}: {error.reason}")
    raise click.ClickException(f"No descriptor found, tried: {', '.join(urls)}")


def make_server(file_path: Path, port: int) -> http.server.ThreadingHTTPServer:
    handler = functools.partial(_DescriptorHandler, directory=str(file_path.parent), filename=file_path.name)
    return http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)


class _DescriptorHandler(http.server.SimpleHTTPRequestHandler):
    """Serves only the descriptor file, readable cross-origin by the web portal."""

    def __init__(self, *args, filename, **kwargs):
        # Set before super().__init__, which handles the request
        self.filename = filename
        super().__init__(*args, **kwargs)

    def send_head(self):
        if self.path.split("?")[0] != "/" + quote(self.filename):
            self.send_error(404)
            return None
        return super().send_head()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        # Chrome's Private Network Access: a public page may only read localhost when allowed
        self.send_header("Access-Control-Allow-Private-Network", "true")
        super().end_headers()


def _load(source: str) -> Descriptor:
    text, location = read_source(source)
    try:
        return load_descriptor(text, name=location)
    except (ValueError, yaml.YAMLError) as error:
        raise click.ClickException(f"{location}: {error}")


def _write(text: str, output: Path | None):
    if output:
        output.write_text(text, encoding="utf-8")
    else:
        click.echo(text, nl=False)
