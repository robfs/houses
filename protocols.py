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

    def supports_url(self, url: str) -> bool:
        host = urlparse(url).hostname
        if not host:
            raise ValueError(f"Could not detect host in url: {url}")
        return host.lower() in {"www.rightmove.com", "rightmove.com"}

    def fetch(self, url: str) -> str:
        response = requests.get(url, headers=self.HEADERS)
        return response.text


class RightMoveParser:
    pass


def main(): ...


if __name__ == "__main__":
    main()
