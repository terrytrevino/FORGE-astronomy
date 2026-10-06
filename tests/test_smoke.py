from pathlib import Path
import ast

import forge_astronomy


ROOT = Path(__file__).resolve().parents[1]


def test_package_version():
    assert forge_astronomy.__version__ == "0.11.0"


def test_webapp_python_sources_parse():
    sources = sorted((ROOT / "webapp").glob("*.py"))
    assert sources, "Expected Python sources under webapp/"

    for path in sources:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_required_webapp_files_exist():
    required = [
        ROOT / "webapp" / "app.py",
        ROOT / "webapp" / "archive_discovery.py",
        ROOT / "webapp" / "spectroscopy.py",
        ROOT / "webapp" / "storage.py",
        ROOT / "webapp" / "suggested_targets.py",
        ROOT / "webapp" / "radio_historical.py",
        ROOT / "webapp" / "requirements.txt",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    assert not missing, f"Missing required webapp files: {missing}"
