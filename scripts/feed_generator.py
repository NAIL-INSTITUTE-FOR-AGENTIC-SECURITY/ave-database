"""
AVE Database RSS/Atom Feed Generator

Generates RSS 2.0 and Atom feeds from the AVE card database.
Run as standalone script or import generate_feeds() into the API server.

Usage:
    python feed_generator.py                     # Generate feeds to ./feeds/
    python feed_generator.py --output /path/to   # Custom output directory

Cron:
    0 */6 * * * cd /app && python feed_generator.py  # Every 6 hours
"""

import json
import glob
import os
import sys
from datetime import datetime, timezone
from xml.etree.ElementTree import Element, SubElement, tostring, ElementTree
from xml.dom import minidom
from typing import Optional
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SITE_URL = "https://nailinstitute.org"
API_URL = "https://api.nailinstitute.org"
FEED_TITLE = "NAIL Institute — AVE Database"
FEED_DESCRIPTION = (
    "Agentic Vulnerability Enumeration (AVE) database updates from the "
    "NAIL Institute for Agentic AI Security."
)
FEED_AUTHOR = "NAIL Institute"
FEED_EMAIL = "ave@nailinstitute.org"
FEED_LANGUAGE = "en"
CARDS_DIR = os.path.join(os.path.dirname(__file__), "..", "ave-database", "cards")
MAX_ITEMS = 50

# ---------------------------------------------------------------------------
# Card loading
# ---------------------------------------------------------------------------

def load_cards(cards_dir: str = CARDS_DIR) -> list[dict]:
    """Load all AVE cards and sort by date_published (newest first)."""
    cards = []
    for json_file in glob.glob(os.path.join(cards_dir, "*.json")):
        try:
            with open(json_file, "r") as f:
                card = json.load(f)
            cards.append(card)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: skipping {json_file}: {e}", file=sys.stderr)
    
    # Sort by date_published descending, fall back to ave_id
    cards.sort(
        key=lambda c: c.get("date_published", c.get("ave_id", "")),
        reverse=True,
    )
    return cards[:MAX_ITEMS]


def card_to_html(card: dict) -> str:
    """Convert an AVE card to an HTML summary for feed content."""
    severity = card.get("severity", "unknown").upper()
    category = card.get("category", "unknown")
    summary = card.get("summary", "No summary available.")
    mechanism = card.get("mechanism", "")
    defences = card.get("defences", [])
    mitre = card.get("mitre_mapping", "")
    avss = card.get("avss_score", "")
    
    html_parts = [
        f"<h3>{card.get('name', card.get('ave_id', 'Unknown'))}</h3>",
        f"<p><strong>Severity:</strong> {severity} | "
        f"<strong>Category:</strong> {category}",
    ]
    
    if avss:
        html_parts[-1] += f" | <strong>AVSS:</strong> {avss}"
    html_parts[-1] += "</p>"
    
    html_parts.append(f"<p>{summary}</p>")
    
    if mechanism:
        html_parts.append(f"<p><strong>Mechanism:</strong> {mechanism}</p>")
    
    if mitre:
        html_parts.append(f"<p><strong>MITRE Mapping:</strong> {mitre}</p>")
    
    if defences:
        html_parts.append("<p><strong>Defences:</strong></p><ul>")
        for d in defences[:5]:
            html_parts.append(f"<li>{d}</li>")
        html_parts.append("</ul>")
    
    return "\n".join(html_parts)


# ---------------------------------------------------------------------------
# RSS 2.0 Generator
# ---------------------------------------------------------------------------

def generate_rss(cards: list[dict]) -> str:
    """Generate RSS 2.0 XML feed."""
    rss = Element("rss", version="2.0")
    rss.set("xmlns:atom", "http://www.w3.org/2005/Atom")
    rss.set("xmlns:dc", "http://purl.org/dc/elements/1.1/")
    
    channel = SubElement(rss, "channel")
    SubElement(channel, "title").text = FEED_TITLE
    SubElement(channel, "link").text = SITE_URL
    SubElement(channel, "description").text = FEED_DESCRIPTION
    SubElement(channel, "language").text = FEED_LANGUAGE
    SubElement(channel, "lastBuildDate").text = (
        datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    )
    SubElement(channel, "generator").text = "NAIL AVE Feed Generator v1.0"
    
    # Self-referencing atom:link
    atom_link = SubElement(channel, "atom:link")
    atom_link.set("href", f"{API_URL}/feeds/rss.xml")
    atom_link.set("rel", "self")
    atom_link.set("type", "application/rss+xml")
    
    # Image
    image = SubElement(channel, "image")
    SubElement(image, "url").text = f"{SITE_URL}/og-image.png"
    SubElement(image, "title").text = FEED_TITLE
    SubElement(image, "link").text = SITE_URL
    
    for card in cards:
        item = SubElement(channel, "item")
        ave_id = card.get("ave_id", "UNKNOWN")
        name = card.get("name", ave_id)
        
        SubElement(item, "title").text = f"[{ave_id}] {name}"
        SubElement(item, "link").text = f"{API_URL}/api/v2/ave/{ave_id}"
        SubElement(item, "guid", isPermaLink="true").text = (
            f"{API_URL}/api/v2/ave/{ave_id}"
        )
        SubElement(item, "description").text = card_to_html(card)
        SubElement(item, "dc:creator").text = FEED_AUTHOR
        
        # Category
        cat = card.get("category", "")
        if cat:
            SubElement(item, "category").text = cat
        
        # Severity as category
        severity = card.get("severity", "")
        if severity:
            SubElement(item, "category").text = f"severity:{severity}"
        
        # Date
        pub_date = card.get("date_published", "")
        if pub_date:
            try:
                dt = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                SubElement(item, "pubDate").text = (
                    dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
                )
            except ValueError:
                pass
    
    # Pretty print
    rough = tostring(rss, encoding="unicode", xml_declaration=False)
    parsed = minidom.parseString(rough)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + parsed.toprettyxml(
        indent="  "
    ).split("\n", 1)[1]


# ---------------------------------------------------------------------------
# Atom Generator
# ---------------------------------------------------------------------------

def generate_atom(cards: list[dict]) -> str:
    """Generate Atom 1.0 XML feed."""
    ATOM_NS = "http://www.w3.org/2005/Atom"
    feed = Element("feed", xmlns=ATOM_NS)
    
    SubElement(feed, "title").text = FEED_TITLE
    SubElement(feed, "subtitle").text = FEED_DESCRIPTION
    SubElement(feed, "id").text = f"{SITE_URL}/feeds/atom.xml"
    SubElement(feed, "updated").text = (
        datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    SubElement(feed, "generator", version="1.0").text = "NAIL AVE Feed Generator"
    
    # Links
    link_self = SubElement(feed, "link")
    link_self.set("href", f"{API_URL}/feeds/atom.xml")
    link_self.set("rel", "self")
    link_self.set("type", "application/atom+xml")
    
    link_alt = SubElement(feed, "link")
    link_alt.set("href", SITE_URL)
    link_alt.set("rel", "alternate")
    link_alt.set("type", "text/html")
    
    # Author
    author = SubElement(feed, "author")
    SubElement(author, "name").text = FEED_AUTHOR
    SubElement(author, "email").text = FEED_EMAIL
    SubElement(author, "uri").text = SITE_URL
    
    # Icon
    SubElement(feed, "icon").text = f"{SITE_URL}/favicon.ico"
    SubElement(feed, "logo").text = f"{SITE_URL}/og-image.png"
    
    for card in cards:
        entry = SubElement(feed, "entry")
        ave_id = card.get("ave_id", "UNKNOWN")
        name = card.get("name", ave_id)
        
        SubElement(entry, "title").text = f"[{ave_id}] {name}"
        SubElement(entry, "id").text = f"{API_URL}/api/v2/ave/{ave_id}"
        
        link = SubElement(entry, "link")
        link.set("href", f"{API_URL}/api/v2/ave/{ave_id}")
        link.set("rel", "alternate")
        link.set("type", "application/json")
        
        # Content
        content = SubElement(entry, "content")
        content.set("type", "html")
        content.text = card_to_html(card)
        
        # Summary
        SubElement(entry, "summary").text = card.get("summary", "")
        
        # Categories
        cat = card.get("category", "")
        if cat:
            cat_el = SubElement(entry, "category")
            cat_el.set("term", cat)
            cat_el.set("label", cat.replace("_", " ").title())
        
        severity = card.get("severity", "")
        if severity:
            sev_el = SubElement(entry, "category")
            sev_el.set("term", f"severity:{severity}")
            sev_el.set("label", f"Severity: {severity.upper()}")
        
        # Author
        entry_author = SubElement(entry, "author")
        contributor = card.get("contributor", FEED_AUTHOR)
        SubElement(entry_author, "name").text = contributor
        
        # Dates
        pub_date = card.get("date_published", "")
        if pub_date:
            try:
                dt = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                SubElement(entry, "published").text = dt.strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                )
                SubElement(entry, "updated").text = dt.strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                )
            except ValueError:
                pass
    
    rough = tostring(feed, encoding="unicode", xml_declaration=False)
    parsed = minidom.parseString(rough)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + parsed.toprettyxml(
        indent="  "
    ).split("\n", 1)[1]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate_feeds(
    cards_dir: str = CARDS_DIR,
    output_dir: Optional[str] = None,
) -> dict[str, str]:
    """Generate both RSS and Atom feeds. Returns dict of format->content."""
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), "..", "feeds")
    
    os.makedirs(output_dir, exist_ok=True)
    
    cards = load_cards(cards_dir)
    print(f"Loaded {len(cards)} AVE cards")
    
    rss_content = generate_rss(cards)
    atom_content = generate_atom(cards)
    
    rss_path = os.path.join(output_dir, "rss.xml")
    atom_path = os.path.join(output_dir, "atom.xml")
    
    with open(rss_path, "w") as f:
        f.write(rss_content)
    print(f"RSS feed written to {rss_path}")
    
    with open(atom_path, "w") as f:
        f.write(atom_content)
    print(f"Atom feed written to {atom_path}")
    
    return {"rss": rss_content, "atom": atom_content}


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate AVE database feeds")
    parser.add_argument("--output", "-o", help="Output directory", default=None)
    parser.add_argument("--cards", "-c", help="Cards directory", default=CARDS_DIR)
    args = parser.parse_args()
    
    generate_feeds(cards_dir=args.cards, output_dir=args.output)
