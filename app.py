"""Main app file."""

from textual.app import App
from textual.reactive import reactive

from screens import MainScreen


class Houses(App):
    CSS_PATH = "assets/styles.tcss"
    BINDINGS = [("q", "quit", "Quit")]
    SCREENS = {
        "main": MainScreen,
    }

    def on_mount(self) -> None:
        self.theme = "nord"
        self.push_screen("main")


if __name__ == "__main__":
    app = Houses()
    app.run()
