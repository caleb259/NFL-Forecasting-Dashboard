import json
from html.parser import HTMLParser
from urllib.request import Request, urlopen


SOURCES = {
    "Week 8": (
        "https://www.49ers.com/news/"
        "lenoir-questionable-purdy-out-vs-texans-injury-report-ahead-of-sfvshou"
    ),
    "Week 9": (
        "https://www.49ers.com/news/"
        "purdy-winters-questionable-vs-giants-injury-report-ahead-of-sfvsnyg"
    ),
    "Week 10": (
        "https://www.49ers.com/news/"
        "bethune-white-questionable-vs-rams-injury-report-ahead-of-larvssf"
    ),
    "Week 11": (
        "https://www.49ers.com/video/"
        "shanahan-provides-final-injury-updates-ahead-of-sfvsaz-purdy-pearsall"
    ),
}


class MetadataParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_json = False
        self.parts = []
        self.json_blocks = []
        self.fields = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)

        if tag == "meta":
            name = attrs.get("property") or attrs.get("name") or ""
            if any(word in name.lower() for word in [
                "publish", "modif", "date", "time"
            ]):
                self.fields.append((name, attrs.get("content", "")))

        if tag == "time" and "datetime" in attrs:
            self.fields.append(("time.datetime", attrs["datetime"]))

        if tag == "script" and attrs.get("type") == "application/ld+json":
            self.in_json = True
            self.parts = []

    def handle_data(self, data):
        if self.in_json:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.in_json:
            self.json_blocks.append("".join(self.parts))
            self.in_json = False


def find_dates(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"datePublished", "dateModified", "uploadDate"}:
                print(f"  JSON-LD {key}: {item}")
            find_dates(item)
    elif isinstance(value, list):
        for item in value:
            find_dates(item)


def main():
    for label, url in SOURCES.items():
        print(f"\n{label}\n{url}")

        try:
            request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(request, timeout=30) as response:
                html = response.read().decode("utf-8", errors="replace")

            parser = MetadataParser()
            parser.feed(html)

            for name, value in parser.fields:
                print(f"  {name}: {value}")

            for block in parser.json_blocks:
                try:
                    find_dates(json.loads(block))
                except json.JSONDecodeError:
                    print("  Could not parse a JSON-LD block.")

            if not parser.fields and not parser.json_blocks:
                print("  No supported metadata found.")

        except Exception as error:
            print(f"  Download/check failed: {type(error).__name__}: {error}")

    print("\nMetadata inspection only. No files changed.")


if __name__ == "__main__":
    main()