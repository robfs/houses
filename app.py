"""Main app file."""

import json

import requests
from bs4 import BeautifulSoup
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Button, Footer, Header, Input
from textual.screen import Screen
from textual.screen import ModalScreen
from textual.widgets import DataTable
from textual.widgets import Label
from textual.reactive import reactive


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
        # yield Input(id="Name", placeholder="Name")
        # yield Input(id="URL", placeholder="URL")
        # yield Input(id="Price", placeholder="Price", type="integer")
        # yield Input(id="Notes", placeholder="Notes")
        yield Input(
            id="property-number",
            placeholder="Rightmove proerty number",
            value="163721768",
        )
        yield Horizontal(Button("Save", id="save"), Button("Cancel", id="cancel"))

    def parse_property_page(self, response: requests.Response):
        """
        Parse a specific Rightmove property page to extract detailed property information
        """
        if not response:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        to_find = "window.PAGE_MODEL"
        scripts = soup.find_all("script")
        for script in scripts:
            self.app.notify(str(script)[:100])
        property_data = {}
        
        
        
        #
        # # Property price - multiple possible selectors
        # price_selectors = [
        #     'span[data-testid="price"]',
        #     ".property-header-price",
        #     "._1gfnqJ3Vtd1z40MlC0MzXu",
        #     "h1",  # Sometimes price is in main heading
        # ]
        #
        # for selector in price_selectors:
        #     price_elem = soup.select_one(selector)
        #     if price_elem and (
        #         "£" in price_elem.get_text() or "POA" in price_elem.get_text()
        #     ):
        #         property_data["price"] = price_elem.get_text(strip=True)
        #         break
        #
        # # Property address
        # address_selectors = [
        #     'address[data-testid="address-label"]',
        #     'h1[data-testid="property-title"]',
        #     ".property-header-address",
        #     "h1",
        #     "address",
        # ]
        #
        # for selector in address_selectors:
        #     address_elem = soup.select_one(selector)
        #     if address_elem and address_elem != soup.select_one(
        #         'span[data-testid="price"]'
        #     ):
        #         address_text = address_elem.get_text(strip=True)
        #         if address_text and not address_text.startswith("£"):
        #             property_data["address"] = address_text
        #             break
        #
        # # Property type and bedrooms (from title or breadcrumbs)
        # title_elem = soup.find("h1")
        # if title_elem:
        #     property_data["title"] = title_elem.get_text(strip=True)
        #
        # # Key features/property details
        # features = []
        #
        # # Method 1: Look for feature lists
        # feature_selectors = [
        #     '[data-testid="property-features"] li',
        #     ".key-features li",
        #     "._2RnXSVJcWbWv4IpBC1Sng6 li",
        #     ".property-features li",
        # ]
        #
        # for selector in feature_selectors:
        #     feature_elements = soup.select(selector)
        #     if feature_elements:
        #         features = [elem.get_text(strip=True) for elem in feature_elements]
        #         break
        #
        # # Method 2: Look for key information section
        # if not features:
        #     info_sections = soup.find_all(
        #         "div", string=re.compile(r"(bedroom|bathroom|reception|garden)", re.I)
        #     )
        #     for section in info_sections:
        #         parent = section.find_parent()
        #         if parent:
        #             features.append(parent.get_text(strip=True))
        #
        # property_data["features"] = features
        #
        # # Property description
        # description_selectors = [
        #     '[data-testid="property-description"]',
        #     ".property-description",
        #     "._1u12RxIYGx3c6RrR5gSCKH",
        #     '[data-testid="description-text"]',
        # ]
        #
        # for selector in description_selectors:
        #     desc_elem = soup.select_one(selector)
        #     if desc_elem:
        #         property_data["description"] = desc_elem.get_text(strip=True)
        #         break
        #
        # # Extract property images
        # image_urls = []
        #
        # # Multiple possible image selectors
        # image_selectors = [
        #     'img[data-testid="gallery-image"]',
        #     ".gallery-image img",
        #     "._3jEoSxJ4dPQMhzWNYAdG0b img",
        #     '[data-testid="property-image"] img',
        #     ".property-photos img",
        # ]
        #
        # for selector in image_selectors:
        #     images = soup.select(selector)
        #     if images:
        #         for img in images:
        #             src = img.get("src") or img.get("data-src") or img.get("data-lazy")
        #             if src and src.startswith("http"):
        #                 image_urls.append(src)
        #         break
        #
        # property_data["images"] = list(set(image_urls))  # Remove duplicates
        # property_data["image_count"] = len(image_urls)
        #
        # # Agent/Branch information
        # agent_selectors = [
        #     '[data-testid="contactBranch"] h2',
        #     ".agent-details h2",
        #     ".branch-name",
        #     "._3SesHHkUj7PNl73sSocFRY",
        # ]
        #
        # for selector in agent_selectors:
        #     agent_elem = soup.select_one(selector)
        #     if agent_elem:
        #         property_data["agent"] = agent_elem.get_text(strip=True)
        #         break
        #
        # # Property ID from URL or page
        # property_id = None
        # canonical_link = soup.find("link", rel="canonical")
        # if canonical_link and canonical_link.get("href"):
        #     # Extract ID from URL like /properties/123456789
        #     id_match = re.search(r"/properties/(\d+)", canonical_link["href"])
        #     if id_match:
        #         property_id = id_match.group(1)
        #
        # if not property_id:
        #     # Try to find it in the current URL or page data
        #     scripts = soup.find_all("script")
        #     for script in scripts:
        #         if script.string:
        #             id_match = re.search(r'"propertyId"\s*:\s*"?(\d+)"?', script.string)
        #             if id_match:
        #                 property_id = id_match.group(1)
        #                 break
        #
        # if property_id:
        #     property_data["property_id"] = property_id
        #
        # # EPC rating
        # epc_selectors = ['[data-testid="epc-rating"]', ".epc-rating", 'img[alt*="EPC"]']
        #
        # for selector in epc_selectors:
        #     epc_elem = soup.select_one(selector)
        #     if epc_elem:
        #         epc_text = epc_elem.get("alt") or epc_elem.get_text(strip=True)
        #         if epc_text:
        #             property_data["epc_rating"] = epc_text
        #             break

        return property_data

    def add_house(self):
        property_number = self.query_one("#property-number", Input).value
        url = f"https://www.rightmove.co.uk/properties/{property_number}"
        self.app.notify(f"Fetching {url}")
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        with open("content.txt", "w") as f:
            f.write(response.text)
        data = self.parse_property_page(response)
        self.app.notify(str(data))
        # keys = ["Name", "URL", "Price", "Notes"]
        # data = {key: self.query_one(f"#{key}", Input).value for key in keys}
        return self.dismiss((False, {}))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self.add_house()
        else:
            self.dismiss((False, {}))


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

    def action_move_house(self) -> None:
        def move_house(to: str) -> None:
            list_parent = self.parent
            if not list_parent:
                return
            new_list = list_parent.query_one(f"#{to}", HouseList)
            table_from = self.query_one(DataTable)
            table_to = new_list.query_one(DataTable)
            row_key, _ = table_from.coordinate_to_cell_key(table_from.cursor_coordinate)
            row = table_from.get_row(row_key)
            data_from = self.data.copy()
            data_to = new_list.data.copy()
            cols = list(data_from[0].keys())
            new_data = {col: cell for col, cell in zip(cols, row, strict=True)}
            data_to.append(new_data)
            index_to_remove = data_from.index(new_data)
            data_from.pop(index_to_remove)
            self.data = data_from
            new_list.data = data_to

        self.app.push_screen(MoveScreen(), move_house)

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


if __name__ == "__main__":
    app = Houses()
    app.run()
