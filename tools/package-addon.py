#!/usr/bin/env python3

import argparse
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build an installable Kodi add-on ZIP")
    parser.add_argument("--addon-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    manifest = ET.parse("addon.xml").getroot()
    actual_id = manifest.attrib.get("id")
    if actual_id != args.addon_id:
        raise SystemExit(f"manifest id {actual_id!r} does not match {args.addon_id!r}")

    status = subprocess.run(
        ["git", "status", "--porcelain"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout
    if status:
        raise SystemExit("working tree must be clean before packaging")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "git",
            "archive",
            "--format=zip",
            f"--prefix={args.addon_id}/",
            f"--output={args.output}",
            "HEAD",
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
