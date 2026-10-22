"""Build the wheels the web portal installs into Pyodide: python web/build.py"""
import json
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).parent.parent
WHEELS = Path(__file__).parent / "wheels"


def main():
    dependencies = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["dependencies"]
    # Pyodide provides the other dependencies (pydantic, pyyaml); click is only used by the CLI
    biomero_schema = next(dep for dep in dependencies if dep.startswith("biomero-schema"))
    WHEELS.mkdir(exist_ok=True)
    for old in WHEELS.glob("*.whl"):
        old.unlink()
    subprocess.run([sys.executable, "-m", "pip", "wheel", "--no-deps", "--wheel-dir", str(WHEELS),
                    str(ROOT), biomero_schema], check=True)
    wheels = sorted(path.name for path in WHEELS.glob("*.whl"))
    (WHEELS / "wheels.json").write_text(json.dumps(wheels, indent=2) + "\n", encoding="utf-8")
    print("\n".join(wheels))


if __name__ == "__main__":
    main()
