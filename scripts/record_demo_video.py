"""Automated video recording of LinguaPay Assistant demo using Playwright."""

from __future__ import annotations

import os
import shutil
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
VIDEO_DIR = ROOT / "docs" / "video"

venv_py = ROOT / "backend" / ".venv" / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python")
PY_BIN = str(venv_py) if venv_py.exists() else sys.executable


def record_demo() -> Path:
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    temp_video_dir = VIDEO_DIR / "raw"
    temp_video_dir.mkdir(parents=True, exist_ok=True)

    print(f"[Video] Starting SimuBank on 5174 and Core API on 8000 using {PY_BIN}...")
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
                browser_args = [
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                    f"--disable-extensions-except={EXT_DIST}",
                    f"--load-extension={EXT_DIST}",
                ]

                launch_kwargs = {
                    "user_data_dir": user_data,
                    "headless": False,
                    "args": browser_args,
                    "record_video_dir": str(temp_video_dir),
                    "record_video_size": {"width": 1280, "height": 720},
                    "viewport": {"width": 1280, "height": 720},
                }
                if channel:
                    launch_kwargs["channel"] = channel

                ctx = p.chromium.launch_persistent_context(**launch_kwargs)
                page = ctx.new_page()

                print("[Video] Step 1: Loading SimuBank CM in original French...")
                page.goto("http://127.0.0.1:5174/index.html", wait_until="networkidle")
                time.sleep(3.0)

                # Wait for overlay host
                page.wait_for_selector("#linguapay-shadow-host", timeout=8000)
                time.sleep(1.5)

                print("[Video] Step 2: Activating LinguaPay & Selecting Ewondo...")
                # Activate translation and switch to Ewondo via shadow root
                page.evaluate("""() => {
                    const host = document.getElementById('linguapay-shadow-host');
                    if (host && host.shadowRoot) {
                        const toggle = host.shadowRoot.getElementById('lp-toggle');
                        if (toggle && !toggle.classList.contains('active')) toggle.click();
                        const langSelect = host.shadowRoot.getElementById('lp-lang');
                        if (langSelect) {
                            langSelect.value = 'ewondo';
                            langSelect.dispatchEvent(new Event('change'));
                        }
                    }
                }""")
                time.sleep(3.0)

                print("[Video] Step 3: Demonstrating Transfer Simulation (50 000 FCFA)...")
                # Scroll to transfer card
                page.locator("#transfer-amount").scroll_into_view_if_needed()
                time.sleep(1.0)
                page.fill("#transfer-amount", "50000")
                time.sleep(1.5)

                # Open confirmation modal
                page.click("#btn-prepare-transfer")
                time.sleep(2.5)

                # Click audio button in modal if present
                page.evaluate("""() => {
                    const host = document.getElementById('linguapay-shadow-host');
                    if (host && host.shadowRoot) {
                        const speakBtn = host.shadowRoot.getElementById('lp-speak');
                        if (speakBtn) speakBtn.click();
                    }
                }""")
                time.sleep(3.0)

                # Fill PIN and confirm
                page.fill("#mock-pin", "1234")
                time.sleep(1.0)
                page.click("#btn-modal-confirm")
                time.sleep(2.5)

                print("[Video] Step 4: Live Injection of Unseen Content...")
                page.locator(".jury-panel").scroll_into_view_if_needed()
                time.sleep(1.5)
                page.click("#btn-preset-maint")
                time.sleep(1.5)
                page.click("#btn-inject-custom")
                time.sleep(3.0)

                print("[Video] Step 5: Opening Integrity & Zero-PII Inspector...")
                page.evaluate("""() => {
                    const host = document.getElementById('linguapay-shadow-host');
                    if (host && host.shadowRoot) {
                        const inspBtn = host.shadowRoot.getElementById('lp-insp-btn');
                        if (inspBtn) inspBtn.click();
                    }
                }""")
                time.sleep(3.0)

                print("[Video] Step 6: Demonstrating Tri-Lingual Parity (Duala & Fulfulde)...")
                page.evaluate("""() => {
                    const host = document.getElementById('linguapay-shadow-host');
                    if (host && host.shadowRoot) {
                        const langSelect = host.shadowRoot.getElementById('lp-lang');
                        if (langSelect) {
                            langSelect.value = 'duala';
                            langSelect.dispatchEvent(new Event('change'));
                        }
                    }
                }""")
                time.sleep(3.0)

                page.evaluate("""() => {
                    const host = document.getElementById('linguapay-shadow-host');
                    if (host && host.shadowRoot) {
                        const langSelect = host.shadowRoot.getElementById('lp-lang');
                        if (langSelect) {
                            langSelect.value = 'fulfulde';
                            langSelect.dispatchEvent(new Event('change'));
                        }
                    }
                }""")
                time.sleep(3.0)

                print("[Video] Step 7: Restoring original French state...")
                page.evaluate("""() => {
                    const host = document.getElementById('linguapay-shadow-host');
                    if (host && host.shadowRoot) {
                        const restoreBtn = host.shadowRoot.getElementById('lp-restore-btn');
                        if (restoreBtn) restoreBtn.click();
                    }
                }""")
                time.sleep(2.5)

                video_path = page.video.path()
                print(f"[Video] Temporary video recorded to: {video_path}")
                ctx.close()

                # Destination file
                final_video = VIDEO_DIR / "demo_linguapay_presentation.webm"
                shutil.copy(video_path, final_video)
                print(f"[Video] Official demo video saved successfully to: {final_video} ({final_video.stat().st_size} bytes)")
                shutil.rmtree(temp_video_dir, ignore_errors=True)
                return final_video

    finally:
        sim_proc.terminate()
        api_proc.terminate()


if __name__ == "__main__":
    record_demo()

