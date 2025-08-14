"""Main app file."""

from textual.app import App
from textual.reactive import var

from protocols import PropertyService
from screens import MainScreen
from utils import (
    HouseService,
    RightMove,
    RightMoveFetcher,
    RightMoveParser,
    RightMoveStore,
)


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
    db_name = "houses_2.db"
    sites = [RightMove()]
    fetchers = [RightMoveFetcher()]
    parsers = [RightMoveParser()]
    stores = [RightMoveStore(db_name)]
    service = HouseService(sites, fetchers, parsers, stores)
    app = Houses()
    app.service = service

    app.run()
