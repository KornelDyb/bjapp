"""Start: python -m app"""
import webview

from .api import Api
from .paths import UI_DIR, db_path
from .storage.db import Database


def main() -> None:
    api = Api(Database(db_path()))
    webview.create_window(
        "Trener Blackjacka",
        str(UI_DIR / "index.html"),
        js_api=api,
        width=1280,
        height=800,
        min_size=(1100, 720),
        background_color="#0B0E1F",
    )
    webview.start()


if __name__ == "__main__":
    main()
