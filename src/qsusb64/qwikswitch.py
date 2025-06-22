"""QwikSwitch USB HID protocol."""

from typing import Any
from collections import defaultdict


type QSID = tuple[int, int, int]


def l2s(data: list[int] | QSID, sep: str = " ") -> str:
    """Return a string representation of the current state."""
    return sep.join([f"{d:02X}" for d in data])


def s2l(data: str, sep=" ") -> list[int]:
    """Convert a string representation to a list of integers."""
    if sep == "":
        # group in 2s, add spaces
        data = " ".join(data[i : i + 2] for i in range(0, len(data), 2))
    return [int(d, 16) for d in data.split() if d.strip()]


def parse_id(data: str) -> QSID:
    """Parse a QwikSwitch ID string into a tuple of integers."""
    data = data.strip()
    if not data.startswith("@") or len(data) != 7:
        raise ValueError(f"Invalid ID format: {data}")
    try:
        return tuple(s2l(data[1:], sep=""))  # type:ignore
    except ValueError:
        raise ValueError(f"Invalid ID format: {data}") from None


def string_id(data: list[int] | QSID) -> str:
    """Convert a list of integers to a QwikSwitch ID string."""
    if len(data) != 3:
        raise ValueError(f"Invalid ID data length: {len(data)}")
    return "@" + l2s(data, sep="").lower()


COUNT: dict[QSID, int] = defaultdict(int)


def qs_encode(cmd: str, id: str, val: int) -> list[int]:
    """Encode a command for QwikSwitch USB HID protocol."""
    idint = parse_id(id)
    count = COUNT[idint] + 1
    # Increment the count for this device. max 7
    COUNT[idint] = 0 if count > 6 else count
    cmdint = 0
    data: list[int] = []
    match cmd:
        case "TOGGLE":
            cmdint = 8
            data = [count, val]  # val is 5/7
        case "SET":
            cmdint = 9
            data = [count, 0x7, val]  # , 0xFF, 0xFF, 0xFF, 0xFF]  # 0x7 - LEVEL cmd
        case "SETTINGS":
            cmdint = 10
            data = [0, 0, 0, val]  # val is report interval in minutes

    data = [0x01, cmdint, *idint, 0x00, *data]

    return data


def qs_decode(data: list[int]) -> dict[str, Any]:
    data = data[:12]
    if data[0] != 0x01 or data[5] != 0x00:
        print("Error: ", l2s(data))
    res = {
        "id": string_id(data[2:5]),
        "cmd": data[1],
    }
    match res["cmd"]:
        case 8:
            res["cmd"] = "TOGGLE"
            res["cnt"] = data[6]
            if data[7] == 0x2:
                res["cmd"] = "TOGGLE.PING"
            elif data[7] != 5:
                res["cmd"] = f"TOGGLE.{data[7]}"
            res["rssi"] = f"{data[8]}%"
            data = data[:10]  # ignore last 2
        case 9:
            res["cmd"] = "SET"
            res["cnt"] = data[6]
            res["val"] = data[8]
        case 10:  # update settings
            res["cmd"] = "SETTINGS"
            res["report"] = f"/{data[9]}min"

        case 11:
            res["cmd"] = "STATUS.ACK"
            type_map = {0x81: "RX1DIM", 0x91: "RX1REL"}
            typ = type_map.get(data[8], f"UNKNOWN({data[8]:02X})")
            ver = f"v{data[9]}"

            match typ:
                case "RX1REL":
                    # bit 10=0x80 on, 0x00 off
                    res["val"] = (
                        "ON"
                        if data[10] == 0x80
                        else "OFF"
                        if data[10] == 0x00
                        else f"?{data[10]:02X}"
                    )
                case "RX1DIM":
                    # bit 10=0x80 on, 0x00 off
                    vvv = data[10]
                    if vvv == 0x7D:
                        res["val"] = "OFF"
                    elif vvv in (0x5A, 0x00):
                        res["val"] = "ON"
                    elif vvv > 0 and vvv < 0x7D:
                        # 0 is 100% and 0x7d is 0%
                        vvv = 100 - (vvv * 100 // 0x7D)
                        res["val"] = f"{vvv}%"
                    else:
                        res["val"] = f"?{data[10]:02X}"

            res["type"] = f"{typ}{ver}"
            res["rssi"] = f"{data[6]}%"

        case _:
            pass
    data = data[6:]

    res["x"] = ".".join([f"{d:02X}" for d in data])
    return res
