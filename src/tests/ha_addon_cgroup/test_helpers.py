"""Test helpers."""

from ha_addon.helpers import onoff


def test_onoff() -> None:
    """Test the onoff function."""
    assert onoff(True) == "on"
    assert onoff(False) == "off"
    assert onoff(None) == "off"
    assert onoff("on") == "on"
    assert onoff("off") == "off"
    assert onoff("0") == "off"
    assert onoff("1") == "on"
