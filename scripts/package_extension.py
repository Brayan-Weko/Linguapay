"""Packages extension/dist into a clean distribution ZIP file for jury evaluation."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT / "extension" / "dist"
OUTPUT_ZIP = ROOT / "linguapay-extension-v1.0.zip"


def main() -> int:
    if not DIST_DIR.exists():
        print(f"Error: {DIST_DIR} does not exist. Run 'cd extension && npm run build' first.")
        return 1

    print(f"Creating distribution ZIP: {OUTPUT_ZIP}...")
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(DIST_DIR.rglob("*")):
            if p.is_file():
                arcname = p.relative_to(DIST_DIR)
                zf.write(p, arcname)
                print(f"  + {arcname}")

    print(f"\nDistribution archive ready ({OUTPUT_ZIP.stat().st_size:,} bytes).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

