from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.events import Focus
from textual.message import Message
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Footer, Input, Label, Select

from protocols import PropertyService

__all__ = ["HouseList", "IDS"]


TO_REVIEW = "to-review"
TO_VIEW = "to-view"
VIEWED_YES = "viewed-yes"
VIEWED_NO = "viewed-no"
IDS = [TO_REVIEW, TO_VIEW, VIEWED_YES, VIEWED_NO]


class AddHouseScreen(ModalScreen[tuple[bool, str, list[str]]]):
    def compose(self) -> ComposeResult:
        input = Input(
            id="property-number",
            placeholder="Rightmove proerty number",
            value="163179074",
        )
        dropdown = Select(
            id="property-site", options=[("Rightmove", "rightmove")], allow_blank=False
        )
        buttons = Horizontal(Button("Save", id="save"), Button("Cancel", id="cancel"))
        yield Container(input, dropdown, buttons)

    def add_houses(self) -> tuple[bool, str, list[str]]:
        input_value = self.query_one("#property-number", Input).value
        site = self.query_one("#property-site", Select).value
        if not site:
            raise ValueError("No site set")
        property_numbers = input_value.split()
        return (True, str(site), property_numbers)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            dismiss = self.add_houses()
            self.dismiss(dismiss)
        else:
            self.dismiss()


class MoveScreen(ModalScreen[str]):
    BINDINGS = [
        ("q", "dismiss", "Close"),
        ("v", "move_to_view", "To View"),
        ("r", "move_to_review", "To Review"),
        ("y", "move_to_yes", "Viewed Yes"),
        ("n", "move_to_no", "Viewed No"),
    ]

    def compose(self) -> ComposeResult:
        container = Container(
            Label("To Reivew (r)"),
            Label("To View (v)"),
            Label("Viewed - yes (y)"),
            Label("Viewed - No (n)"),
        )
        container.border_title = "Move to"
        yield container
        yield Footer()

    def action_move_to_view(self) -> None:
        self.dismiss(TO_VIEW)

    def action_move_to_review(self) -> None:
        self.dismiss(TO_REVIEW)

    def action_move_to_yes(self) -> None:
        self.dismiss(VIEWED_YES)

    def action_move_to_no(self) -> None:
        self.dismiss(VIEWED_NO)


class HouseList(DataTable):
    BINDINGS = [("m", "move_house", "Move"), ("a", "add_house", "Add House")]
    data: reactive[list[dict]] = reactive([])
    property_number: reactive[str] = reactive("")

    def on_mount(self) -> None:
        self.set_border_title_from_id()
        self.service: PropertyService = self.app.service
        self.cursor_type = "row"
        self.add_columns("ID", "Description")
        self.load_data()

    def set_border_title_from_id(self) -> None:
        id = self.id or ""
        parts = id.split("-")
        self.border_title = " ".join(map(str.capitalize, parts))
        return None

    def action_add_house(self) -> None:
        def process_houses(houses: tuple[bool, str, list[str]] | None):
            if not houses:
                return None
            to_save, site_name, ids = houses
            if not to_save:
                return
            property_id = ids[0]
            self.service.add_property(site_name, property_id, TO_REVIEW)
            self.load_data()

        self.app.push_screen(AddHouseScreen(), process_houses)

    def action_move_house(self) -> None:
        def move_house(to: str | None) -> None: ...

        self.app.push_screen(MoveScreen(), move_house)

    def load_data(self) -> None:
        self.clear()

    class HouseSelectionChanged(Message):
        def __init__(self, property_number: str) -> None:
            super().__init__()
            self.property_number = property_number

    def notify_container(self) -> None:
        if not self.has_focus_within:
            return
        containers = self.screen.query("#detail-container")
        if not containers:
            return
        detail_container = containers.first()
        detail_container.post_message(self.HouseSelectionChanged(self.property_number))

    def on_data_table_row_highlighted(self, message: DataTable.RowHighlighted) -> None:
        self.property_number = message.row_key.value or ""

    def on_focus(self, message: Focus) -> None:
        if message.from_app_focus:
            return
        self.notify_container()
