"""Where the committed data lives: inside the package, so installing it installs the data."""

from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
BUNDLE_DIR = DATA_DIR / "bundles"
MANIFEST = DATA_DIR / "manifest.json"
MEMBERS = DATA_DIR / "members.json"
PROPERTIES = DATA_DIR / "synthea.properties"
KEEP_MODULE = DATA_DIR / "keep_respiratory.json"
