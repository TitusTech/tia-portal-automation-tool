from pathlib import Path
import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Internal tooling for Siemens PLC Engineers by Titus Global Tech.")
    parser.add_argument("-j", "--json",
                        type=Path,
                        help="JSON config file path"
                        )
    args = parser.parse_args()

    json_config = args.json

    if not json_config:
        import sys

        from ui.graphical import MainWindow, app

        window = MainWindow()
        window.show()
        sys.exit(app.exec())

    else:
        import ui.terminal
