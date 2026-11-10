"""Shared pieces of the bin/shot and bin/browser-login scripts."""

from __future__ import annotations

import os
from pathlib import Path

from playwright.sync_api import Browser, Playwright

STATE_DIR = Path(
    os.environ.get("WORKSTATION_BROWSER_STATE")
    or Path.home() / ".config/workstation/browser-state"
)
DEFAULT_VIEWPORT = "1440x900"


class BrowserSetupError(Exception):
    pass


def parse_viewport(text: str) -> dict[str, int]:
    try:
        width, height = (int(part) for part in text.lower().split("x"))
    except ValueError:
        raise BrowserSetupError(
            f"viewport must look like 1440x900, got {text!r}"
        ) from None
    return {"width": width, "height": height}


def state_path(env: str) -> Path:
    return STATE_DIR / f"{env}.json"


def load_state(env: str | None) -> str | None:
    """Return the saved storage state path for env, or fail so a missing login is never silent."""
    if env is None:
        return None
    path = state_path(env)
    if not path.exists():
        raise BrowserSetupError(
            f"no saved state for {env!r}; run browser-login {env} <url> once"
        )
    return str(path)


def launch(playwright: Playwright, headed: bool = False) -> Browser:
    """Launch Chromium, using the newest installed headless shell when the pinned revision is absent."""
    if headed:
        return playwright.chromium.launch(headless=False)
    try:
        return playwright.chromium.launch()
    except Exception:
        shells = sorted(
            (Path.home() / "Library/Caches/ms-playwright").glob(
                "chromium_headless_shell-*/*/chrome-headless-shell"
            )
        )
        if not shells:
            raise
        return playwright.chromium.launch(executable_path=str(shells[-1]))
