from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.events import DescendantFocus
from textual.message import Message
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Footer, Input, Label

from utils import JSON_STORE, JSONStore, get_property_models_async

__all__ = ["HouseList", "IDS"]


TO_REVIEW = "to-review"
TO_VIEW = "to-view"
VIEWED_YES = "viewed-yes"
VIEWED_NO = "viewed-no"
IDS = [TO_REVIEW, TO_VIEW, VIEWED_YES, VIEWED_NO]


class AddHouseScreen(ModalScreen[tuple[bool, list[str]]]):
    def compose(self) -> ComposeResult:
        input = Input(id="property-number", placeholder="Rightmove proerty number")
        buttons = Horizontal(Button("Save", id="save"), Button("Cancel", id="cancel"))
        yield Container(input, buttons)

    def add_houses(self) -> tuple[bool, list[str]]:
        input_value = self.query_one("#property-number", Input).value
        property_numbers = input_value.split()
        return (True, property_numbers)

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


class HouseList(Container):
    BINDINGS = [("m", "move_house", "Move"), ("a", "add_house", "Add House")]
    data: reactive[list[dict]] = reactive([])
    property_number: reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        yield DataTable(zebra_stripes=True, cursor_type="row")

    def on_mount(self) -> None:
        self.set_border_title_from_id()
        table = self.query_one(DataTable)
        table.add_columns("ID", "Description")
        self.load_data()

    def set_border_title_from_id(self) -> None:
        id = self.id or ""
        parts = id.split("-")
        self.border_title = " ".join(map(str.capitalize, parts))
        return None

    async def action_add_house(self) -> None:
        async def process_houses(houses: tuple[bool, list[str]] | None):
            if not houses:
                return
            to_save, property_numbers = houses
            if not to_save:
                return

            store = JSONStore(JSON_STORE)
            for property_number in property_numbers:
                try:
                    property_models = await get_property_models_async(property_number)
                    page_data = property_models["PAGE_MODEL"]
                    store.set(property_number, self.id, page_data)
                    self.app.notify(f"Data saved for {property_number}")
                except Exception as e:
                    self.app.notify(
                        f"Failed: {property_number}.\n\n{e}", severity="error"
                    )
            self.load_data()

        self.app.push_screen(AddHouseScreen(), process_houses)

    def action_move_house(self) -> None:
        def move_house(to: str | None) -> None:
            if not to:
                return
            list_container = self.parent
            if not list_container:
                raise ValueError(f"No parent container for {self}")
            old_table = self.query_one(DataTable)
            key, _ = old_table.coordinate_to_cell_key(old_table.cursor_coordinate)
            store = JSONStore(JSON_STORE)
            self.app.notify(f"Moving {key.value} to {to}")
            store.update_status(key.value, to)
            self.load_data()
            new_list = list_container.query_one(f"#{to}", HouseList)
            new_list.load_data()

        self.app.push_screen(MoveScreen(), move_house)

    def load_data(self) -> None:
        if not self.id:
            raise ValueError(f"{self} missind id.")
        store = JSONStore(JSON_STORE)
        data = store.get_main_table_data(self.id)
        table = self.query_one(DataTable)
        table.clear()
        for row in data:
            table.add_row(
                row["property_number"], row["description"], key=row["property_number"]
            )

    class HouseSelectionChanged(Message):
        def __init__(self, property_number: str) -> None:
            super().__init__()
            self.property_number = property_number

    def notify_container(self) -> None:
        detail_container = self.screen.query_one("#detail-container")
        detail_container.post_message(self.HouseSelectionChanged(self.property_number))

    def watch_property_number(self) -> None:
        self.notify_container()

    def on_data_table_row_highlighted(self, message: DataTable.RowHighlighted) -> None:
        self.property_number = message.row_key.value or ""

    def on_descendant_focus(self, message: DescendantFocus) -> None:
        self.notify_container()
