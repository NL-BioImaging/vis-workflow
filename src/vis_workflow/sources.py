"""Turn a descriptor source URL into the raw URLs to try, without any I/O (shared with the web portal)."""
import re
from urllib.parse import quote

PORTAL_URL = "https://nl-bioimaging.github.io/vis-workflow/"
# Tried in this order for a directory, as BIOMERO does
DESCRIPTOR_FILES = ("descriptor.json", "descriptor.yaml", "config.yaml")
DESCRIPTOR_SUFFIXES = (".json", ".yaml", ".yml")

GITHUB = re.compile(
    r"^https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?"
    r"(?:/(?P<kind>blob|tree)/(?P<ref>[^/]+)(?P<path>/.*)?)?/?$"
)


def candidate_urls(source: str) -> list[str]:
    """Raw URLs for a GitHub file, directory or repository URL; other URLs as given."""
    match = GITHUB.match(source.split("?")[0].split("#")[0])
    if not match:
        return [source]
    raw = f"https://raw.githubusercontent.com/{match['owner']}/{match['repo']}/{match['ref'] or 'HEAD'}"
    path = (match["path"] or "").rstrip("/")
    if path.lower().endswith(DESCRIPTOR_SUFFIXES):
        return [raw + path]
    return directory_candidates(raw + path)


def directory_candidates(directory: str) -> list[str]:
    return [f"{directory.rstrip('/')}/{name}" for name in DESCRIPTOR_FILES]


def portal_url(source: str, portal: str = PORTAL_URL) -> str:
    return f"{portal}?source={quote(source, safe='')}"
