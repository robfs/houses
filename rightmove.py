from bs4 import BeautifulSoup
import regex as re
import requests
import json

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


def load_html(url: str) -> str:
    response = requests.get(url, headers=HEADERS)
    return response.text


def extract_script(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    pattern = re.compile(r"window\.(\w+)\s*=\s*\{")
    script = soup.find("script", string=pattern)
    if not script:
        return ""
    return script.get_text(strip=True)


def get_models(html) -> dict[str, dict]:
    """Extract JavaScript models from html and return them as dictionaries."""

    models = {}

    # Use regex with recursive pattern to match nested braces
    pattern = r"window\.(\w+)\s*=\s*(\{(?:[^{}]|(?2))*\})"

    for match in re.finditer(pattern, html, re.DOTALL):
        model_name = match.group(1)
        js_content = match.group(2)

        try:
            # The content is already valid JSON, no need for js_to_json conversion
            models[model_name] = json.loads(js_content)
        except json.JSONDecodeError as e:
            print(f"Failed to parse {model_name}: {e}")

    return models


if __name__ == "__main__":
    html = load_html("https://www.rightmove.co.uk/properties/163179074")
    with open("content.html", "w") as f:
        f.write(html)
    script = extract_script(html)
    models = get_models(script)

    # Print basic info about extracted models
    for model_name, model_data in models.items():
        print(f"\nModel: {model_name}")
        if isinstance(model_data, dict):
            print(f"Keys: {list(model_data.keys())[:10]}...")  # Show first 10 keys
            # Print property info if it's the PAGE_MODEL
            if model_name == "PAGE_MODEL" and "propertyData" in model_data:
                prop_data = model_data["propertyData"]
                print(f"Property ID: {prop_data.get('id')}")
                print(f"Bedrooms: {prop_data.get('bedrooms')}")
                if "prices" in prop_data:
                    print(f"Price: {prop_data['prices'].get('primaryPrice')}")
