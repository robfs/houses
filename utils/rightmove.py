import sqlite3
from urllib.parse import urlparse

import httpx
import orjson
import orjson as json
import regex
import requests

from protocols import Property

__all__ = [
    "RightMove",
    "RightMoveFetcher",
    "RightMoveParser",
    "RightMoveProperty",
    "RightMoveStore",
]


def check_url_host_in(url: str, valid: set[str]) -> bool:
    host = urlparse(url).hostname
    if not host:
        raise ValueError(f"Could not detect host in url: {url}")
    return host in valid


class RightMoveProperty:
    data: dict
    status: str | None
    valid_hosts: set[str] = {"rightmove.co.uk", "www.rightmove.co.uk"}

    def __init__(self, data: dict, status: str | None = None) -> None:
        self.data = data
        self.status = status

    def supports_url(self, url: str) -> bool:
        return check_url_host_in(url, self.valid_hosts)


class RightMove:
    def name(self) -> str:
        return "rightmove"

    @staticmethod
    def get_property_url(property_id: str) -> str:
        return f"https://www.rightmove.co.uk/properties/{property_id}"

    def get_property_constructor(self) -> type[RightMoveProperty]:
        return RightMoveProperty


class RightMoveFetcher:
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
    valid_hosts: set[str] = {"rightmove.co.uk", "www.rightmove.co.uk"}

    def supports_url(self, url: str) -> bool:
        return check_url_host_in(url.lower(), self.valid_hosts)

    def fetch(self, url: str) -> str:
        response = requests.get(url, headers=self.HEADERS)
        response.raise_for_status()
        return response.text

    async def fetch_async(self, url: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.HEADERS)
            return response.text


class RightMoveParser:
    _valid_hosts: set[str] = {"rightmove.co.uk", "www.rightmove.co.uk"}

    def supports_url(self, url: str) -> bool:
        return check_url_host_in(url, self._valid_hosts)

    def _get_page_model(self, content: str) -> str:
        pattern = r"window\.PAGE_MODEL\s*=\s*(\{(?:[^{}]|(?1))*\})"
        match_ = regex.search(pattern, content, regex.DOTALL)
        if not match_:
            raise ValueError("Couldn't locate page model.")
        return match_.group(1).strip()

    def parse(self, content: str) -> RightMoveProperty:
        script = self._get_page_model(content)
        property_data = orjson.loads(script)
        return RightMoveProperty(property_data)


class RightMoveStore:
    _constructor: type[RightMoveProperty] = RightMoveProperty
    valid_hosts: set[str] = {"rightmove.co.uk", "www.rightmove.co.uk"}

    def __init__(self, db_path) -> None:
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(
            """
            create table if not exists houses (
                url text primary key,
                status text,
                data JSON
            )
            """
        )

    def get_property_constructor(self) -> type[RightMoveProperty]:
        return self._constructor

    def supports_url(self, url: str) -> bool:
        return check_url_host_in(url, self.valid_hosts)

    def set(self, url: str, property: Property, status: str | None = None) -> str:
        self.conn.execute(
            "insert or replace into houses (url, status, data) values (?, ?, ?)",
            (url, status, json.dumps(property.data)),
        )
        self.conn.commit()
        return url

    def get(self, url: str) -> RightMoveProperty | None:
        cursor = self.conn.execute(
            "select data, status from houses where url = ?", (url,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        data, status = row[0]
        constructor = self.get_property_constructor()
        return constructor(data, status)

    def delete(self, url: str) -> str:
        query = "delete from houses where url = ?"
        self.conn.execute(query, url)
        self.conn.commit()
        return url

    def update(self, url: str, *, status: str) -> str:
        raise NotImplementedError()

    # def update_status(self, property_number, status):
    #     query = "update houses set status = ? where property_number = ?"
    #     self.conn.execute(query, (status, property_number))
    #     self.conn.commit()

    # def get_main_table_data(self, status: str):
    #     query = HouseQuery().atomic_query(
    #         [
    #             ("property_number", "property_number"),
    #             ("propertyData.address.displayAddress", "description"),
    #         ],
    #         status=status,
    #     )
    #     cursor = self.conn.execute(query)
    #     return cursor.fetchall()
    #
    # def get_image_urls(self, property_number: str) -> list[str]:
    #     query = HouseQuery().array_query(
    #         "propertyData.images", [(".url", "url")], property_number=property_number
    #     )
    #     cursor = self.conn.execute(query)
    #     data = cursor.fetchall()


async def main():
    property_number = "163179074"
    site = RightMove()
    url = site.get_property_url(property_number)
    fetcher = RightMoveFetcher()
    content = await fetcher.fetch_async(url)
    parser = RightMoveParser()
    return parser.parse(content)


if __name__ == "__main__":
    import asyncio
    import pprint

    property = asyncio.run(main())
    pprint.pprint(property.data)
