"""Main app file."""

from textual.app import App
from textual.reactive import var

from protocols import PropertyService
from screens import MainScreen
from utils import HouseService, RightMove, RightMoveFetcher, RightMoveParser
from utils.json_store import HouseStore


class Houses(App):
    CSS_PATH = "assets/styles.tcss"
    BINDINGS = [("q", "quit", "Quit")]
    SCREENS = {
        "main": MainScreen,
    }
    service: var[PropertyService]

    def on_mount(self) -> None:
        self.theme = "nord"
        self.push_screen("main")


if __name__ == "__main__":
    db_name = "houses.db"
    site = RightMove()
    fetchers = [RightMoveFetcher()]
    parsers = [RightMoveParser()]
    stores = [HouseStore(db_name)]
    service = HouseService(site, fetchers, parsers, stores)
    app = Houses()
    app.service = service

    app.run()
