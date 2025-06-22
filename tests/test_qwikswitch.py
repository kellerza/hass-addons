"""Test qs."""

from qsusb64.qwikswitch import parse_id, qs_encode


def test_id() -> None:
    """Test the ID parsing."""
    assert parse_id("@123456") == (18, 52, 86)
    assert parse_id("@FF0000") == (255, 0, 0)
    assert parse_id("@000000") == (0, 0, 0)
    try:
        parse_id("123456")
    except ValueError as e:
        assert str(e) == "Invalid ID format: 123456"
    try:
        parse_id("@12345G")
    except ValueError as e:
        assert str(e) == "Invalid ID format: @12345G"


def test_encode() -> None:
    """Test the encoding."""
    assert qs_encode("TOGGLE", "@123456", 5) == [1, 8, 18, 52, 86, 0, 0, 5]
    assert qs_encode("TOGGLE", "@123456", 5) == [1, 8, 18, 52, 86, 0, 1, 5]

    assert qs_encode("SET", "@123457", 7) == [1, 9, 18, 52, 87, 0, 0, 7]
    assert qs_encode("SETTINGS", "@123458", 10) == [1, 10, 18, 52, 88, 0, 0, 0, 0, 10]
