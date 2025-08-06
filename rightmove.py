import re
import requests
from bs4 import BeautifulSoup, Tag


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

def get_page(url: str) -> requests.Response:
    return requests.get(url, headers=HEADERS)

def get_models_string(response: requests.Response) -> str:
    soup = BeautifulSoup(response.text, "html.parser")
    script: Tag = soup.find("script", string=re.compile("window.PAGE_MODEL"))
    return script.string or ""

def parse_property_page(response: requests.Response):
    models_string = get_models_string(response)
    
    return models_string

if __name__ == "__main__":
    url = "https://www.rightmove.co.uk/properties/163721768"
    response = get_page(url)
    model = parse_property_page(response)
    print(model)
