import re

import orjson as json
import regex
import requests
from bs4 import BeautifulSoup
from textual.app import ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.widgets import DataTable

from utils.json_store import JSONStore

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

JSON_STORE = "houses.db"


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
