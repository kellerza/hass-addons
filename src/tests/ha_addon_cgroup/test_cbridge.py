"""Test helpers."""

from ha_addon_control_group.cbridge import CGroupBridge, ControlGroupOptions


def test_kick() -> None:
    """Test kick template."""
    cg = CGroupBridge(
        opt=ControlGroupOptions(id="a", entities=["light.dining", "light.kitchen"])
    )
    assert (
        cg.kick_template
        == "{%- set _kick=states('light.dining')+states('light.kitchen') -%}"
    )
