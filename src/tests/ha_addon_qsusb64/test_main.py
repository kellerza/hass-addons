"""Main."""

from ha_addon_qsusb64 import __main__ as main_module
from ha_addon_qsusb64 import main


def test_a() -> None:
    """Test that the main module can be imported and has attributes."""
    assert len(dir(main_module)) > 2
    assert len(dir(main)) > 2
    assert hasattr(main, "QsUsb")
