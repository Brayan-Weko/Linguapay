"""End-to-End integration smoke test running SimuBank CM, LinguaPay Core API, and Playwright."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
EXT_DIST = str((ROOT / "extension" / "dist").resolve())
SIM_DIR = str((ROOT / "simulator").resolve())
BACKEND_DIR = str((ROOT / "backend").resolve())

# Use active python or virtualenv python if present
venv_py = ROOT / "backend" / ".venv" / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python")
PY_BIN = str(venv_py) if venv_py.exists() else sys.executable


def main() -> int:
    print(f"[E2E] Starting SimuBank on port 5174 and Core API on port 8000 using {PY_BIN}...")
    sim_proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", "5174", "--directory", SIM_DIR],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    api_proc = subprocess.Popen(
        [PY_BIN, "-m", "uvicorn", "app.main:app", "--port", "8000"],
        cwd=BACKEND_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        time.sleep(2.5)
        with sync_playwright() as p:
            with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as user_data:
                channel = "msedge" if os.name == "nt" else None
                launch_kwargs = {
                    "user_data_dir": user_data,
                    "headless": True,
                    "args": [
                        f"--disable-extensions-except={EXT_DIST}",
                        f"--load-extension={EXT_DIST}",
                    ],
                }
                if channel:
                    launch_kwargs["channel"] = channel

                ctx = p.chromium.launch_persistent_context(**launch_kwargs)
                page = ctx.new_page()
                errs: list[str] = []
                page.on("pageerror", lambda e: errs.append(str(e)))

                # 1. SimuBank load & overlay check
                page.goto("http://127.0.0.1:5174/index.html", wait_until="networkidle")
                time.sleep(1.2)
                has_host = page.evaluate("() => Boolean(document.getElementById('linguapay-shadow-host'))")
                assert has_host, "LinguaPay shadow host overlay not mounted in DOM!"
                assert "145 750 FCFA" in page.inner_text("#account-balance")

                # 2. Test Unseen Content Injection
                page.click("#btn-preset-maint")
                assert "02h00" in page.inner_text("#dynamic-feed")

                # 3. Test Transfer Flow
                page.click("#btn-prepare-transfer")
                assert "51 500 FCFA" in page.inner_text("#modal-summary-sentence")
                page.fill("#mock-pin", "1234")
                page.click("#btn-modal-confirm")
                assert "94 250 FCFA" in page.inner_text("#account-balance")

                # 4. Check microfinance alternate interface
                page.goto("http://127.0.0.1:5174/microfinance-skin.html", wait_until="networkidle")
                assert "82 400 FCFA" in page.inner_text(".kpi h2")

                assert not errs, f"Unexpected page errors: {errs}"
                ctx.close()

        print("[E2E] Full End-to-End smoke test PASSED successfully!")
        return 0
    finally:
        sim_proc.terminate()
        api_proc.terminate()


if __name__ == "__main__":
    sys.exit(main())

