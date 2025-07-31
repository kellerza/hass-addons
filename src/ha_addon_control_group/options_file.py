"""Options stored in the configuration folder.

Persistent UUID etc.
"""

import json
import logging
from pathlib import Path
from uuid import uuid4

import attrs
from cattrs.preconf.json import make_converter

CONVERTER = make_converter()
_LOG = logging.getLogger(__name__)


@attrs.define()
class FileGroupOption:
    """File group option."""

    mode: str = ""


@attrs.define()
class FileOptions:
    """HASS Addon Options."""

    uuid: str = ""
    groups: dict[str, FileGroupOption] = attrs.field(factory=dict)

    def file_path(self) -> Path:
        """Get the configuration folder."""
        cfg = Path("/config")
        if not cfg.is_dir():
            cfg = Path(".data/config")
            assert cfg.is_dir(), "Create pytest folder"
        return cfg / "state.json"

    def save_file(self) -> None:
        """Save options."""
        data = CONVERTER.unstructure(self)
        opt = self.file_path()
        with opt.open("w") as f:
            json.dump(data, f, indent=2)

    def load_file(self) -> None:
        """Load options from the configuration files."""
        pth = self.file_path()

        if pth.exists():
            _LOG.info("Loading persistent state from: %s", pth)
            with pth.open("r") as f:
                data = json.load(f)
            if isinstance(data.get("groups"), list):  # migrate from old format
                data.pop("groups", None)
            res = CONVERTER.structure(data, FileOptions)
            self.uuid = res.uuid
            self.groups = res.groups

        if not self.uuid:
            _LOG.info("Creating a new UUID in options file: %s", pth)
            self.uuid = str(uuid4())
            self.save_file()


OPT_FILE = FileOptions()
