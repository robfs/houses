"""Main app file."""

import json
import sqlite3

import regex
import requests
from bs4 import BeautifulSoup
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, DataTable, Footer, Header, Input, Label

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


class JSONStore:
    def __init__(self, db_path) -> None:
        self.conn = sqlite3.connect(db_path)
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

    def get_by_status(self, status):
        query = "select data from houses where status = ?"
        cursor = self.conn.execute(query, (status,))
        rows = cursor.fetchall()
        return [json.loads(row[0]) for row in rows]

    def delete(self, property_number):
        query = "delete from houses where property_number = ?"
        self.conn.execute(query, property_number)
        self.conn.commit()

    def update_status(self, property_number, status):
        query = "update houses set status = ? where property_number = ?"
        self.conn.execute(query, (status, property_number))
        self.conn.commit()


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


class AddHouseScreen(ModalScreen[tuple[bool, str, dict]]):
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
        yield Input(
            id="property-number",
            placeholder="Rightmove proerty number",
            value="163721768",
        )
        yield Horizontal(Button("Save", id="save"), Button("Cancel", id="cancel"))

    @staticmethod
    def fetch_property_data(property_number: str) -> requests.Response:
        url = f"https://www.rightmove.co.uk/properties/{property_number}"
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response

    @staticmethod
    def extract_model_script(response: requests.Response) -> str:
        soup = BeautifulSoup(response.text)
        pattern = regex.compile(r"window\.(\w+)\s*=\s*\{")
        script = soup.find("script", string=pattern)
        if not script:
            return ""
        return script.get_text(strip=True)

    @staticmethod
    def get_models(script_text: str) -> dict[str, dict]:
        models = {}
        pattern = r"window\.(\w+)\s*=\s*(\{(?:[^{}]|(?2))*\})"
        for match in regex.finditer(pattern, script_text, regex.DOTALL):
            model_name = match.group(1)
            js_content = match.group(2)
            try:
                # The content is already valid JSON, no need for js_to_json conversion
                models[model_name] = json.loads(js_content)
            except json.JSONDecodeError as e:
                print(f"Failed to parse {model_name}: {e}")
        return models

    def add_house(self) -> tuple[bool, str, dict]:
        property_number = self.query_one("#property-number", Input).value
        self.app.notify(f"Fetching property {property_number}")
        response = self.fetch_property_data(property_number)
        script = self.extract_model_script(response)
        property_models = self.get_models(script)
        page_data = property_models["PAGE_MODEL"]
        self.app.notify(f"{page_data.keys()} retrieved.")
        return (True, property_number, page_data)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            dismiss = self.add_house()
            self.dismiss(dismiss)
        else:
            self.dismiss((False, "", {}))


class MainContainer(Container):
    DEFAULT_CSS = """
    MainContainer {
                padding: 1;
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
        table = self.query_one(DataTable)
        table.add_columns("ID", "Description")
        self.load_data()

    def set_border_title_from_id(self) -> None:
        id = self.id or ""
        parts = id.split("-")
        self.border_title = " ".join(map(str.capitalize, parts))
        return None

    def action_add_house(self) -> None:
        def process_house(house: tuple[bool, str, dict]):
            to_save, key, data = house
            if not to_save:
                self.app.notify("Aborting add")
                return
            self.app.notify(f"Saving {key}")
            store = JSONStore(JSON_STORE)
            store.set(key, self.id, data)
            self.app.notify(f"Data saved for {key}")

        # [{"to-review": [], "to-view": [], "viewed-yes": [], "viewed-no": []}]
        self.app.push_screen(AddHouseScreen(), process_house)

    # def action_move_house(self) -> None:
    #     def move_house(to: str) -> None:
    #         list_parent = self.parent
    #         if not list_parent:
    #             return
    #         new_list = list_parent.query_one(f"#{to}", HouseList)
    #         table_from = self.query_one(DataTable)
    #         table_to = new_list.query_one(DataTable)
    #         row_key, _ = table_from.coordinate_to_cell_key(table_from.cursor_coordinate)
    #         row = table_from.get_row(row_key)
    #         data_from = self.data.copy()
    #         data_to = new_list.data.copy()
    #         cols = list(data_from[0].keys())
    #         new_data = {col: cell for col, cell in zip(cols, row, strict=True)}
    #         data_to.append(new_data)
    #         index_to_remove = data_from.index(new_data)
    #         data_from.pop(index_to_remove)
    #         self.data = data_from
    #         new_list.data = data_to
    #
    #     self.app.push_screen(MoveScreen(), move_house)

    def load_data(self) -> None:
        store = JSONStore(JSON_STORE)
        self.data = store.get_by_status(self.id)

    # def save_data(self) -> None:
    #     with open("data.json") as f:
    #         all_data = json.load(f)[0]
    #     all_data[self.id] = self.data
    #     with open("data.json", "w") as f:
    #         json.dump([all_data], f)

    def watch_data(self, data: list[dict]) -> None:
        if not data:
            return
        table = self.query_one(DataTable)
        table.clear()
        for row in data:
            property_data = row.get("propertyData", {})
            text = property_data.get("text", {})
            table.add_row(
                property_data.get("id"),
                text.get("description"),
                key=property_data["id"],
            )
        # self.save_data()


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


if __name__ == "__main__":
    app = Houses()
    app.run()
