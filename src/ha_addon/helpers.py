"""Home Assistant Addon Helpers."""

import os
from pathlib import Path


def ha_share_path(addon_slug: str, create: bool = False) -> Path:
    """Get the root folder for data and mysensors."""
    root = (
        Path(f"/share/{addon_slug}/")
        if os.name != "nt"
        else Path(__name__).parent.parent / ".data"
    )
    if create and not root.exists():
        root.mkdir(parents=True)
    return root


def slug(name: str) -> str:
    """Create a slug."""
    return name.lower().replace(" ", "_").replace("-", "_")
