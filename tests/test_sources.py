import pytest

from vis_workflow.sources import candidate_urls, portal_url

RAW = "https://raw.githubusercontent.com/org/repo"
DISCOVERED = ["descriptor.json", "descriptor.yaml", "config.yaml"]


@pytest.mark.parametrize("source, expected", [
    ("https://github.com/org/repo/blob/main/config.yaml", [f"{RAW}/main/config.yaml"]),
    ("https://github.com/org/repo/tree/v1.0/sub/descriptor.json", [f"{RAW}/v1.0/sub/descriptor.json"]),
    ("https://github.com/org/repo/tree/v1.0/sub/", [f"{RAW}/v1.0/sub/{name}" for name in DISCOVERED]),
    ("https://github.com/org/repo.git", [f"{RAW}/HEAD/{name}" for name in DISCOVERED]),
    ("https://github.com/org/repo/blob/main/config.yaml?plain=1#L5", [f"{RAW}/main/config.yaml"]),
    ("https://example.org/any/descriptor", ["https://example.org/any/descriptor"]),
])
def test_candidate_urls(source, expected):
    assert candidate_urls(source) == expected


def test_portal_url_encodes_source():
    assert portal_url("http://localhost:8000/a b.yaml", "https://portal/") == \
        "https://portal/?source=http%3A%2F%2Flocalhost%3A8000%2Fa%20b.yaml"
