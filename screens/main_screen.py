"""Main app file."""

import json
import re
import sqlite3
from collections.abc import Collection
from urllib.request import urlopen

import regex
import requests
from bs4 import BeautifulSoup
from PIL import Image as PilImage
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, DataTable, Footer, Header, Input, Label
from textual_image.widget import Image

__all__ = ["MainScreen"]


JSON_STORE = "houses.db"
TO_REVIEW = "to-review"
TO_VIEW = "to-view"
VIEWED_YES = "viewed-yes"
VIEWED_NO = "viewed-no"


IDS = [TO_REVIEW, TO_VIEW, VIEWED_YES, VIEWED_NO]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    # 'Accept-Encoding': 'gzip, deflate, br',
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0",
}


class HouseQuery:
    def _column_string(
        self, paths: Collection[tuple[str, str]], root: str = "data"
    ) -> str:
        columns = []
        for path, name in paths:
            if "." in path:
                clean_path = path.strip(".")
                column = f"json_extract({root}, '$.{clean_path}') as {name}"
            else:
                column = f"{path} as {name}"
            columns.append(column)

        return ", ".join(columns)

    def _add_filters(self, query: str, **kwargs) -> str:
        if not kwargs:
            return query
        filters = [f"{key} = '{value}'" for key, value in kwargs.items()]
        filter_str = " and ".join(filters)
        return query + f" where {filter_str}"

    def atomic_query(self, paths: Collection[tuple[str, str]], **kwargs) -> str:
        column_str = self._column_string(paths)
        query = f"select {column_str} from houses"
        return self._add_filters(query, **kwargs)

    def array_query(
        self, array_path: str, paths: Collection[tuple[str, str]], **kwargs
    ) -> str:
        column_str = self._column_string(paths, "value")
        query = (
            f"select {column_str} from houses, json_each(houses.data, '$.{array_path}')"
        )
        return self._add_filters(query, **kwargs)


class JSONStore:
    def __init__(self, db_path) -> None:
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(
            """
            create table if not exists houses (
                property_number text primary key,
                status text,
                data JSON
            )
            """
        )

    def set(self, property_number, status, data):
        self.conn.execute(
            "insert or replace into houses (property_number, status, data) values (?, ?, ?)",
            (property_number, status, json.dumps(data)),
        )
        self.conn.commit()

    def get(self, key):
        cursor = self.conn.execute(
            "select data from houses where property_number = ?", (key,)
        )
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None

    def delete(self, property_number):
        query = "delete from houses where property_number = ?"
        self.conn.execute(query, property_number)
        self.conn.commit()

    def update_status(self, property_number, status):
        query = "update houses set status = ? where property_number = ?"
        self.conn.execute(query, (status, property_number))
        self.conn.commit()

    def get_main_table_data(self, status: str):
        query = HouseQuery().atomic_query(
            [
                ("property_number", "property_number"),
                ("propertyData.address.displayAddress", "description"),
            ],
            status=status,
        )
        cursor = self.conn.execute(query)
        return cursor.fetchall()

    def get_image_urls(self, property_number: str) -> list[str]:
        query = HouseQuery().array_query(
            "propertyData.images", [(".url", "url")], property_number=property_number
        )
        cursor = self.conn.execute(query)
        data = cursor.fetchall()
        return [row["url"] for row in data]


class MoveScreen(ModalScreen[str]):
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


class AddHouseScreen(ModalScreen[tuple[bool, list[str]]]):
    DEFAULT_CSS = """
    AddHouseScreen {
            align: center middle;

            Container {
                height: 10;
                width: 50;
                border: $accent double;
                border-title-color: $accent;
                align: center middle;
                }
            }
    """

    def compose(self) -> ComposeResult:
        input = Input(
            id="property-number",
            placeholder="Rightmove proerty number",
            value="163721768",
        )
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
            self.dismiss((False, []))


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
        table = self.query_one(DataTable)
        table.add_columns("ID", "Description")
        self.load_data()

    def set_border_title_from_id(self) -> None:
        id = self.id or ""
        parts = id.split("-")
        self.border_title = " ".join(map(str.capitalize, parts))
        return None

    @staticmethod
    def get_property_response(property_number: str) -> requests.Response:
        url = f"https://www.rightmove.co.uk/properties/{property_number}"
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response

    @staticmethod
    def extract_model_script(response: requests.Response) -> str:
        soup = BeautifulSoup(response.text)
        pattern = re.compile(r"window\.(\w+)\s*=\s*\{")
        script = soup.find("script", string=pattern)
        if not script:
            return ""
        return script.get_text(strip=True)

    @classmethod
    def get_models(cls, response: requests.Response) -> dict[str, dict]:
        script_text = cls.extract_model_script(response)
        models = {}
        pattern = r"window\.(\w+)\s*=\s*(\{(?:[^{}]|(?2))*\})"
        for match in regex.finditer(pattern, script_text, regex.DOTALL):
            model_name = match.group(1)
            js_content = match.group(2)
            try:
                models[model_name] = json.loads(js_content)
            except json.JSONDecodeError as e:
                print(f"Failed to parse {model_name}: {e}")
        return models

    def action_add_house(self) -> None:
        def process_houses(houses: tuple[bool, list[str]] | None):
            if not houses:
                return
            to_save, property_numbers = houses
            if not to_save:
                return

            store = JSONStore(JSON_STORE)
            for property_number in property_numbers:
                try:
                    response = self.get_property_response(property_number)
                    property_models = self.get_models(response)
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

    def update_image_displayed(self, property_number: str) -> None:
        store = JSONStore(JSON_STORE)
        url = store.get_image_urls(property_number)[0]
        parent = self.parent
        parent = parent.parent if parent else None
        if not parent:
            return
        image = parent.query_one(Image)
        image.image = PilImage.open(urlopen(url))

    def on_data_table_row_highlighted(self, message: DataTable.RowHighlighted) -> None:
        property_number = message.row_key.value or ""
        self.update_image_displayed(property_number)

    def on_descendant_focus(self) -> None:
        table = self.query_one(DataTable)
        cell_key = table.coordinate_to_cell_key(table.cursor_coordinate)
        property_number = cell_key.row_key.value or ""
        self.update_image_displayed(property_number)


class DetailContainer(Container):
    DEFAULT_CSS = """
    DetailContainer {
        border: $accent round;
        border-title-color: $accent;
        border-title-background: $background;
        background: $surface;
    }
    """
    BORDER_TITLE = "Details"

    def compose(self) -> ComposeResult:
        yield Image()


class MainScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Horizontal(
            Vertical(
                HouseList(id=TO_REVIEW),
                HouseList(id=TO_VIEW),
                HouseList(id=VIEWED_YES),
                HouseList(id=VIEWED_NO),
            ),
            DetailContainer(),
        )
        yield Footer()
        yield Header()
