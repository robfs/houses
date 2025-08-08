"""Main app file."""

from textual.app import App
from textual.reactive import reactive

from screens.main_screen import MainScreen


class Houses(App):
    BINDINGS = [("q", "quit", "Quit")]
    SCREENS = {
        "main": MainScreen,
    }
    houses: reactive[dict[str, list[dict]]] = reactive({})

    def on_mount(self) -> None:
        self.theme = "nord"
        self.push_screen("main")


if __name__ == "__main__":
    app = Houses()
    app.run()
