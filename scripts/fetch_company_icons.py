#!/usr/bin/env python3
"""Cache company icons for the static directory, preferring Apple touch icons."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
ICON_DIR = ROOT / "assets" / "company-icons"
MANIFEST = ICON_DIR / "manifest.json"
USER_AGENT = "Mozilla/5.0 (compatible; AwesomeAIEmployees/1.0; icon discovery)"
MAX_ICON_BYTES = 512 * 1024


@dataclass(frozen=True)
class Candidate:
    url: str
    kind: str
    size: int = 0


class IconParser(HTMLParser):
    """Read declared icons, including relative URLs and HTML base elements."""

    def __init__(self, page_url: str):
        super().__init__(convert_charrefs=True)
        self.page_url = page_url
        self.base_url = page_url
        self.base_seen = False
        self.links: list[tuple[str, str, int]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key: value or "" for key, value in attrs}
        if tag == "base" and not self.base_seen and attributes.get("href"):
            self.base_url = urljoin(self.page_url, attributes["href"])
            self.base_seen = True
        if tag != "link" or not attributes.get("href"):
            return
        relations = attributes.get("rel", "").lower().split()
        if any(rel in {"apple-touch-icon", "apple-touch-icon-precomposed"} for rel in relations):
            kind = "apple-touch-icon"
        elif "icon" in relations:
            kind = "favicon"
        else:
            return
        sizes = [int(size) for size in re.findall(r"(\d+)x\d+", attributes.get("sizes", ""))]
        self.links.append((attributes["href"], kind, max(sizes, default=0)))

    def candidates(self) -> list[Candidate]:
        candidates = [Candidate(urljoin(self.base_url, href), kind, size) for href, kind, size in self.links]
        return sorted(candidates, key=lambda icon: (icon.kind == "apple-touch-icon", icon.size), reverse=True)


def icon_candidates(html: str, page_url: str) -> list[Candidate]:
    parser = IconParser(page_url)
    parser.feed(html)
    origin = urlunsplit((*urlsplit(page_url)[:2], "/", "", ""))
    declared = parser.candidates()
    # Some sites publish conventional files without declaring them in their HTML.
    candidates = (
        [icon for icon in declared if icon.kind == "apple-touch-icon"]
        + [Candidate(urljoin(origin, "apple-touch-icon.png"), "apple-touch-icon")]
        + [icon for icon in declared if icon.kind == "favicon"]
        + [Candidate(urljoin(origin, "favicon.ico"), "favicon")]
    )
    unique = {}
    for candidate in candidates:
        if urlsplit(candidate.url).scheme in {"http", "https"}:
            unique.setdefault(candidate.url, candidate)
    return list(unique.values())


def image_extension(data: bytes) -> str | None:
    """Check image bytes rather than trusting an HTML fallback's content type."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"\x00\x00\x01\x00"):
        return "ico"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "webp"
    if b"<svg" in data[:1024]:
        try:
            root = ET.fromstring(data)
        except ET.ParseError:
            return None
        if root.tag.split("}")[-1] != "svg":
            return None
        for element in root.iter():
            if element.tag.split("}")[-1].lower() in {"script", "foreignobject", "image", "a"}:
                return None
            for name, value in element.attrib.items():
                attribute = name.split("}")[-1].lower()
                if attribute.startswith("on") or (attribute == "href" and not value.startswith("#")):
                    return None
                if "url(" in value.lower() and not re.fullmatch(r"url\(#[\w-]+\)", value):
                    return None
            if element.tag.split("}")[-1] == "style" and re.search(r"@import|url\(", element.text or "", re.I):
                return None
        return "svg"
    return None


def download(url: str, limit: int) -> tuple[bytes, str]:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    with urlopen(request, timeout=10) as response:
        data = response.read(limit + 1)
        if len(data) > limit:
            raise ValueError("Response exceeds size limit")
        return data, response.url


def fetch_icon(company: dict, previous: dict) -> tuple[str, dict]:
    name = company["company"]
    parsed = urlsplit(company["link"])
    home = urlunsplit((parsed.scheme, parsed.netloc, "/", "", ""))
    html = ""
    reason = "No usable icon found"
    try:
        raw, home = download(home, 2 * 1024 * 1024)
        html = raw.decode("utf-8", errors="replace")
    except (OSError, ValueError, HTTPError, URLError) as error:
        reason = f"Homepage unavailable ({type(error).__name__})"
    for candidate in icon_candidates(html, home):
        try:
            data, source = download(candidate.url, MAX_ICON_BYTES)
            extension = image_extension(data)
            if not extension:
                continue
            slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
            path = ICON_DIR / f"{slug}.{extension}"
            path.write_bytes(data)
            return name, {"path": path.relative_to(ROOT).as_posix(), "kind": candidate.kind, "source": source}
        except (OSError, ValueError, HTTPError, URLError):
            continue
    cached = previous.get(name, {})
    if cached.get("path") and (ROOT / cached["path"]).is_file():
        return name, {**cached, "note": "Retained cached icon; source unavailable during refresh"}
    return name, {"kind": "initials", "reason": reason}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--company", action="append", help="Refresh only this company (repeatable)")
    parser.add_argument("--workers", type=int, choices=range(1, 17), default=8)
    args = parser.parse_args()
    companies = json.loads((ROOT / "data" / "companies.json").read_text())
    if args.company:
        selected = set(args.company)
        unknown = selected - {company["company"] for company in companies}
        if unknown:
            parser.error(f"Unknown companies: {', '.join(sorted(unknown))}")
        companies = [company for company in companies if company["company"] in selected]
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    previous = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    result = dict(previous) if args.company else {}
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(fetch_icon, company, previous) for company in companies]
        for index, future in enumerate(as_completed(futures), start=1):
            name, icon = future.result()
            result[name] = icon
            print(f"[{index}/{len(companies)}] {name}: {icon['kind']}", flush=True)
    MANIFEST.write_text(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    counts = {kind: sum(icon["kind"] == kind for icon in result.values()) for kind in ("apple-touch-icon", "favicon", "initials")}
    print(json.dumps(counts), flush=True)


if __name__ == "__main__":
    main()
