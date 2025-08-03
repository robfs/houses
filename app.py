"""Main app file."""

import json

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Button, Footer, Header, Input
from textual.screen import Screen
from textual.screen import ModalScreen
from textual.message import Message
from textual.widgets import DataTable
from textual.widgets import Label
from textual.reactive import reactive


class MoveScreen(ModalScreen):
    DEFAULT_CSS = """
    MoveScreen {
            align: center middle;

            Container {
                border: $accent double;
                border-title-color: $accent;
                height: 5;
                width: 70;
                layout: grid;
                grid-size: 4 1;
                grid-gutter: 1;
                align: center middle;

                Label {
                    grid-columns: 1fr;
                    }
                }
            }
    """
    BINDINGS = [("q", "dismiss", "Close")]

    def compose(self) -> ComposeResult:
        container = Container(
            Label("To View (v)"),
            Label("To Review (r)"),
            Label("Viewed Yes (y)"),
            Label("Viewed No (n)"),
        )
        container.border_title = "Move to"
        yield container
        yield Footer()


class AddHouseScreen(ModalScreen[tuple[bool, dict]]):
    DEFAULT_CSS = """
    AddHouseScreen {
            align: center middle;

            Container {
                border: $accent double;
                border-title-color: $accent;
                height: 30;
                width: 70;
                align: center middle;
                }
            }
    """

    def compose(self) -> ComposeResult:
        yield Input(id="Name", placeholder="Name")
        yield Input(id="URL", placeholder="URL")
        yield Input(id="Price", placeholder="Price", type="integer")
        yield Input(id="Notes", placeholder="Notes")
        yield Horizontal(Button("Save", id="save"), Button("Cancel", id="cancel"))

    def add_house(self):
        keys = ["Name", "URL", "Price", "Notes"]
        data = {key: self.query_one(f"#{key}", Input).value for key in keys}
        return self.dismiss((True, data))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self.add_house()
        else:
            self.dismiss((False, {}))


class MainContainer(Container):
    DEFAULT_CSS = """
    MainContainer {
                border: $primary double;
                layout: grid;
                grid-size: 2 2;
                grid-gutter: 1;
                }
    """


class HouseList(Container):
    DEFAULT_CSS = """
    HouseList {
            border: $accent round;
            border-title-color: $accent;
            border-title-background: $background;
            background: $surface;
            }
    """
    BINDINGS = [("m", "move_house", "Move"), ("a", "add_house", "Add House")]
    data: reactive[list[dict]] = reactive([])

    def compose(self) -> ComposeResult:
        yield DataTable(zebra_stripes=True, cursor_type="row")

    def on_mount(self) -> None:
        self.set_border_title_from_id()
        self.load_data()

    def set_border_title_from_id(self) -> None:
        id = self.id or ""
        parts = id.split("-")
        self.border_title = " ".join(map(str.capitalize, parts))
        return None

    def action_add_house(self) -> None:
        def process_house(house: tuple[bool, dict]):
            if not house[0]:
                return
            data = self.data.copy()
            data.append(house[1])
            self.data = data

        # [{"to-review": [], "to-view": [], "viewed-yes": [], "viewed-no": []}]
        self.app.push_screen(AddHouseScreen(), process_house)

    class RequestMoveScreen(Message):
        pass

    def action_move_house(self) -> None:
        self.post_message(self.RequestMoveScreen())

    def load_data(self) -> None:
        with open("data.json") as f:
            data = json.load(f)
        self.data = data[0][self.id]

    def save_data(self) -> None:
        with open("data.json") as f:
            all_data = json.load(f)[0]
        all_data[self.id] = self.data
        with open("data.json", "w") as f:
            json.dump([all_data], f)

    def watch_data(self, data: list[dict]) -> None:
        if not data:
            return
        cols = list(data[0].keys())
        table = self.query_one(DataTable)
        table.clear(columns=True)
        table.add_columns(*cols)
        table.add_rows([list(item.values()) for item in data])
        self.save_data()


class MainScreen(Screen):
    def compose(self) -> ComposeResult:
        yield MainContainer(
            HouseList(id="to-review"),
            HouseList(id="to-view"),
            HouseList(id="viewed-yes"),
            HouseList(id="viewed-no"),
        )
        yield Footer()
        yield Header()


class Houses(App):
    BINDINGS = [("q", "quit", "Quit")]
    SCREENS = {
        "main": MainScreen,
    }
    houses: reactive[dict[str, list[dict]]] = reactive({})

    def on_mount(self) -> None:
        self.theme = "nord"
        self.push_screen("main")

    def on_house_list_request_move_screen(self) -> None:
        self.push_screen(MoveScreen())


if __name__ == "__main__":
    app = Houses()
    app.run()
