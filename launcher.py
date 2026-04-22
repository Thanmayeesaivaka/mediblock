import sys
import webbrowser


PROJECT_URL = "https://mediblock-kvgs.onrender.com/"


def main() -> int:
    try:
        webbrowser.open(PROJECT_URL, new=2)
        return 0
    except Exception:
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
