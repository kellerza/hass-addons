"""listen to qsusb."""

import requests

URL = "http://192.168.1.8:2020/&listen"


def main() -> None:
    """Main function to listen for QS64 commands."""
    while True:
        response = requests.get(URL)
        if response.status_code == 200:
            print(response.text)
        else:
            print(f"Failed to connect to {URL}. Status code: {response.status_code}")


if __name__ == "__main__":
    main()
