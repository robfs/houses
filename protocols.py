from typing import Protocol
from urllib.parse import urlparse

import requests


class PropertySite(Protocol):
    def get_property_url(self, *args, **kwargs) -> str: ...


class PropertyFetcher(Protocol):
    def supports_url(self, url: str) -> bool: ...
    def fetch(self, url: str) -> str: ...


class PropertyParser(Protocol):
    def supports_url(self, url: str) -> bool: ...
    def parse(self, content: str) -> dict: ...


class PropertyStore(Protocol):
    def set(self, id: str, data: dict, *args, **kwargs) -> str: ...
    def get(self, id: str) -> dict: ...
    def delete(self, id: str) -> bool: ...
    def update(self, id: str, *args, **kwargs) -> str: ...


class PropertyService(Protocol):
    site: PropertySite
    fetchers: list[PropertyFetcher]
    parsers: list[PropertyParser]
    store: PropertyStore


def check_url_host_in(url: str, valid: set[str]) -> bool:
    host = urlparse(url).hostname
    if not host:
        raise ValueError(f"Could not detect host in url: {url}")
    return host in valid


class RightMove:
    @staticmethod
    def get_property_url(property_number: str) -> str:
        return f"https://www.rightmove.co.uk/properties/{property_number}"


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


class RightMoveParser:
    valid_hosts: set[str] = {"rightmove.co.uk", "www.rightmove.co.uk"}

    def supports_url(self, url: str) -> bool:
        return check_url_host_in(url, self.valid_hosts)


def main(): ...


if __name__ == "__main__":
    main()
