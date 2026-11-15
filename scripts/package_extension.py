"""Packages extension/dist into clean distribution ZIP and CRX files."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT / "extension" / "dist"
OUTPUT_ZIP = ROOT / "linguapay-extension-v1.0.zip"
OUTPUT_CRX = ROOT / "linguapay-extension-v1.0.crx"


def main() -> int:
    if not DIST_DIR.exists():
        print(f"Error: {DIST_DIR} does not exist. Run 'cd extension && npm run build' first.")
        return 1

    # 1. Create standard distribution ZIP
    print(f"Creating distribution ZIP: {OUTPUT_ZIP}...")
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(DIST_DIR.rglob("*")):
            if p.is_file():
                arcname = p.relative_to(DIST_DIR)
                zf.write(p, arcname)
                print(f"  + {arcname}")
    print(f"ZIP archive ready: {OUTPUT_ZIP.name} ({OUTPUT_ZIP.stat().st_size:,} bytes).")

    # 2. Create signed CRX extension file if Chromium/Edge is available
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    ]
    browser_bin = next((p for p in edge_paths if os.path.exists(p)), None)
    if browser_bin:
        print(f"\nPacking official CRX extension using {browser_bin}...")
        pem_key = ROOT / "extension" / "dist.pem"
        cmd = [browser_bin, f"--pack-extension={DIST_DIR}"]
        if pem_key.exists():
            cmd.append(f"--pack-extension-key={pem_key}")
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        generated_crx = ROOT / "extension" / "dist.crx"
        if generated_crx.exists():
            shutil.copy(generated_crx, OUTPUT_CRX)
            print(f"CRX file ready: {OUTPUT_CRX.name} ({OUTPUT_CRX.stat().st_size:,} bytes).")

    return 0


if __name__ == "__main__":
    sys.exit(main())

