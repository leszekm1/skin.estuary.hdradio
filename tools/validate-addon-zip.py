#!/usr/bin/env python3

import argparse
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path, PurePosixPath


REJECTED_PARTS = {".git", ".github", "__pycache__", ".pytest_cache", "tools"}
REJECTED_SUFFIXES = {".bak", ".orig", ".rej", ".tmp"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a Kodi install ZIP")
    parser.add_argument("zip_path", type=Path)
    parser.add_argument("--addon-id", required=True)
    args = parser.parse_args()

    with zipfile.ZipFile(args.zip_path) as archive:
        files = [entry for entry in archive.infolist() if not entry.is_dir()]
        if not files:
            raise SystemExit("archive contains no files")

        paths = [PurePosixPath(entry.filename) for entry in files]
        for path in paths:
            if path.is_absolute() or ".." in path.parts:
                raise SystemExit(f"unsafe archive path: {path}")
            if REJECTED_PARTS.intersection(path.parts):
                raise SystemExit(f"unwanted archive path: {path}")
            if path.suffix in REJECTED_SUFFIXES:
                raise SystemExit(f"unwanted archive file: {path}")

        roots = {path.parts[0] for path in paths}
        if roots != {args.addon_id}:
            raise SystemExit(
                f"expected one top-level {args.addon_id} directory, found {sorted(roots)}"
            )

        manifest_path = f"{args.addon_id}/addon.xml"
        if manifest_path not in {entry.filename for entry in files}:
            raise SystemExit(f"missing {manifest_path}")

        manifest = ET.fromstring(archive.read(manifest_path))
        if manifest.attrib.get("id") != args.addon_id or not manifest.attrib.get("version"):
            raise SystemExit("manifest id or version is invalid")

        with tempfile.TemporaryDirectory(prefix="kodi-addon-zip-") as directory:
            archive.extractall(directory)
            if not Path(directory, args.addon_id, "addon.xml").is_file():
                raise SystemExit("clean extraction did not produce addon.xml")

    print(
        f"validated {args.zip_path}: "
        f"{manifest.attrib['id']} {manifest.attrib['version']}"
    )


if __name__ == "__main__":
    main()
