import io
import shutil
import threading
import urllib.error
import urllib.request

import pytest
from biomero_schema.models import WorkflowSchema
from click.testing import CliRunner

from conftest import FIXTURES, load_fixture
from vis_workflow import cli as cli_module
from vis_workflow import to_mermaid
from vis_workflow.cli import cli, make_server, read_source


def test_mermaid_and_convert_from_directory(tmp_path):
    shutil.copy(FIXTURES / "bilayers_example.yaml", tmp_path / "config.yaml")
    descriptor = load_fixture("bilayers_example.yaml")
    runner = CliRunner()

    result = runner.invoke(cli, ["mermaid", str(tmp_path), "--params", "all"])
    assert result.exit_code == 0, result.output
    assert result.output == to_mermaid(descriptor, params="all")

    markdown = tmp_path / "diagram.md"
    assert runner.invoke(cli, ["mermaid", str(tmp_path), "-o", str(markdown)]).exit_code == 0
    assert markdown.read_text(encoding="utf-8") == f"```mermaid\n{to_mermaid(descriptor)}```\n"

    result = runner.invoke(cli, ["convert", str(tmp_path)])
    assert WorkflowSchema.model_validate_json(result.output) == descriptor.workflow


@pytest.mark.parametrize("content, message", [
    (None, "No such file or directory"),
    ("- not\n- a mapping\n", "not a mapping"),
    ("key: [unclosed", "while parsing"),
])
def test_errors_reported(tmp_path, content, message):
    path = tmp_path / "config.yaml"
    if content is not None:
        path.write_text(content, encoding="utf-8")
    result = CliRunner().invoke(cli, ["mermaid", str(path)])
    assert result.exit_code == 1
    assert message in result.output


def test_url_tries_candidates_in_order(monkeypatch):
    tried = []

    def fake_urlopen(url, timeout):
        tried.append(url.rsplit("/", 1)[-1])
        if not url.endswith("config.yaml"):
            raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
        return io.BytesIO(b"text")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    text, location = read_source("https://github.com/org/repo/tree/main")
    assert (text, location) == ("text", "https://raw.githubusercontent.com/org/repo/main/config.yaml")
    assert tried == ["descriptor.json", "descriptor.yaml", "config.yaml"]


def test_view_url_opens_portal_without_server(monkeypatch):
    opened = []
    monkeypatch.setattr(cli_module.webbrowser, "open", opened.append)
    assert CliRunner().invoke(cli, ["view", "https://example.org/c.yaml", "--portal", "https://p/"]).exit_code == 0
    assert opened == ["https://p/?source=https%3A%2F%2Fexample.org%2Fc.yaml"]


def test_server_serves_only_descriptor_with_cors():
    server = make_server(FIXTURES / "bilayers_example.yaml", 0)
    # Short poll so shutdown() returns at once
    threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        with urllib.request.urlopen(f"{base}/bilayers_example.yaml") as response:
            assert response.headers["Access-Control-Allow-Origin"] == "*"
            assert response.read() == (FIXTURES / "bilayers_example.yaml").read_bytes()
        for path in ("/", "/example_workflow.json"):
            with pytest.raises(urllib.error.HTTPError, match="404"):
                urllib.request.urlopen(base + path)
    finally:
        server.shutdown()
        server.server_close()
