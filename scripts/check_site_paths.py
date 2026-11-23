#!/usr/bin/env python3
"""Verify generated static URLs for the /windmills/ path migration."""
from html.parser import HTMLParser
from pathlib import Path

dist = Path("dist")
expected = [
    "windmills/index.html",
    "windmills/writing/index.html",
    "windmills/writing/the-first-step/index.html",
    "windmills/series/hctigt/index.html",
    "windmills/projects/index.html",
    "windmills/about/index.html",
    "windmills/rss.xml",
]
for path in expected:
    assert (dist / path).is_file(), f"Missing public page: {path}"
print("All expected /windmills/ pages exist.")

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        url = attrs.get("href") or attrs.get("src")
        if url:
            self.urls.append(url)

for path in ["windmills/index.html", "windmills/writing/the-first-step/index.html"]:
    html = (dist / path).read_text(encoding="utf-8")
    parsed = Links()
    parsed.feed(html)
    for url in parsed.urls:
        assert not url.startswith(("/writing/", "/series/", "/projects/", "/about/", "/rss.xml")), (
            f"Unprefixed URL in {path}: {url}"
        )
    assert "/windmills/writing/" in html, f"No prefixed writing link in {path}"
    print(f"{path}: {len(parsed.urls)} links and assets checked")

article = (dist / "windmills/writing/the-first-step/index.html").read_text(encoding="utf-8")
# The site's header provides series context, while the HCTiGT manuscript
# remains authoritative. Repetition is intentional until the author changes
# the source: the import must never delete or move the source's footnotes.
assert "Alpha preview" not in article, "Unwanted alpha banner"
assert 'class="article-series-preface"' in article, "Missing series pre-title context"
assert '/windmills/series/hctigt/' in article, "Series link is missing"
source_markdown = Path("src/content/writing/the-first-step.md").read_text(encoding="utf-8")
series_intro = "is my series about finding my way into interpretability"
# A second occurrence belongs to the author, not to the site's presenter.
# The site-owned frontmatter includes the header text, so only inspect
# Markdown after frontmatter when determining whether the author repeats it.
source_body = source_markdown.split("\n---\n", 1)[1]
expected_occurrences = 1 + int(series_intro in source_body)
assert article.count(series_intro) == expected_occurrences, (
    f"Series context should appear once in the header plus any canonical article occurrence, got {article.count(series_intro)}"
)
assert article.index('class="article-series-preface"') < article.index("<h1>The First Step</h1>"), "Series preface must precede title"
assert "colab.research.google.com/github/bubskee/hctigt/blob/main/notebooks/03-make-a-choice.ipynb" in article
assert 'rel="canonical" href="https://tylting.at/windmills/writing/the-first-step/"' in article or 'href="https://tylting.at/windmills/writing/the-first-step/" rel="canonical"' in article, "Incorrect article canonical URL"
assert "/windmills/writing/the-first-step/" in (dist / "windmills/rss.xml").read_text(encoding="utf-8"), "Incorrect RSS URL"
assert (dist / "_redirects").is_file(), "Missing Cloudflare Worker redirects"
assert (dist / "robots.txt").is_file(), "Missing domain-root robots.txt"
assert (dist / "windmills/favicon.svg").is_file(), "Missing base-aware favicon"
assert "/windmills/favicon.svg" in article, "Favicon does not use /windmills prefix"
# The article is freshly generated from HCTiGT, not maintained as a site copy.
source_markdown = Path("src/content/writing/the-first-step.md").read_text(encoding="utf-8")
assert source_markdown.startswith("---\ntitle: \"The First Step\""), "Missing site metadata"
assert "NASA / Public domain" in source_markdown, "Expected author's NASA image credit"
assert "Cargo Cult Science" in source_markdown, "Article seems older than canonical source"
import re
from urllib.parse import unquote

# Source-driven: articles may gain or lose footnotes, with arbitrary labels.
defined_labels = re.findall(r"(?m)^\[\^([^\]]+)\]:", source_body)
cited_labels = re.findall(r"\[\^([^\]]+)\](?!:)", source_body)
assert len(defined_labels) == len(set(defined_labels)), "Duplicate footnote definitions"
undefined = set(cited_labels) - set(defined_labels)
assert not undefined, f"References without footnote definitions: {sorted(undefined)}"

class FootnoteMarkup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
        self.backrefs = []
        self.ids = set()
        self.has_section = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag == "section" and "data-footnotes" in attrs:
            self.has_section = True
        if tag == "a" and "data-footnote-ref" in attrs:
            self.refs.append(attrs.get("href", ""))
        if tag == "a" and "data-footnote-backref" in attrs:
            self.backrefs.append(attrs.get("href", ""))

markup = FootnoteMarkup()
markup.feed(article)
assert len(markup.refs) == len(cited_labels), (
    f"HCTiGT cites {len(cited_labels)} footnotes {cited_labels}, but Astro "
    f"rendered {len(markup.refs)} links. Check Markdown inside <details>."
)
if cited_labels:
    assert markup.has_section, "Missing rendered footnotes section"
    assert len(markup.backrefs) >= len(set(cited_labels)), "Missing return links"
else:
    assert not markup.has_section, "Unexpected footnotes section with no references"

for url in markup.refs + markup.backrefs:
    assert url.startswith("#") and unquote(url[1:]) in markup.ids, (
        f"Footnote link points to a missing destination: {url}"
    )
for label in cited_labels:
    assert f"[^{label}]" not in article, f"Literal unrendered footnote marker: {label}"

print(
    f"Footnotes: {len(cited_labels)} citations / {len(set(cited_labels))} "
    f"distinct labels; {len(markup.refs)} linked references, "
    f"{len(markup.backrefs)} back-links."
)

# Native <details> should stay collapsible, and Markdown references inside
# the block must become real links rather than remaining literal [^labels].
source_details = re.findall(r"<details\b[^>]*>.*?</details>", source_body, flags=re.DOTALL | re.IGNORECASE)
rendered_details = re.findall(r"<details\b[^>]*>.*?</details>", article, flags=re.DOTALL | re.IGNORECASE)
assert len(rendered_details) == len(source_details), "Missing or unclosed <details> block in article HTML"
for index, (source_block, rendered_block) in enumerate(zip(source_details, rendered_details), start=1):
    expected = len(re.findall(r"\[\^([^\]]+)\](?!:)", source_block))
    present = len(re.findall(r"<a\b[^>]*\bdata-footnote-ref\b", rendered_block))
    assert "<summary" in rendered_block, f"Missing collapsible heading in <details> {index}"
    assert present == expected, (
        f"Inside <details> {index}: expected {expected} linked footnotes, found {present}"
    )
print(f"Collapsible sections: {len(rendered_details)} rendered with their inner footnotes.")

# Footnote presentation enhancement is bundled without replacing the endnotes.
# Astro may inline small scripts into the page rather than emitting .js files.
# Inspect both generated page HTML and every emitted JS bundle.
assets = list(dist.rglob("*.js"))
bundled = article + "\\n" + "\\n".join(
    p.read_text(encoding="utf-8") for p in assets
)
print("Sidenote script audit:", len(assets), "JS assets,",
      "inline or bundled code:", "margin-notes" in bundled)
assert "margin-notes" in bundled, "No sidenote enhancer in article or built JS"
assert "data-footnote-ref" in bundled, "Missing sidenote reference selector"
print("Desktop sidenote enhancer present; mobile endnotes remain intact.")

assert '<blockquote>' in article, "Bilbo quotation is not a semantic blockquote"
assert '*The Fellowship of the Ring*' not in article, "Blockquote attribution not rendered as emphasis"
assert "Bilbo Baggins" in article and "Frodo" in article, "Missing quotation or attribution"

# The source's image lives in the actual Cloudflare-deployed /windmills tree.
assert "/windmills/hctigt-assets/cassidy-spacewalk.jpg" in article, "Missing linked Cassidy image"
image = dist / "windmills/hctigt-assets/cassidy-spacewalk.jpg"
assert image.is_file() and image.stat().st_size > 100_000, "Missing or incomplete copied NASA image"
# The construction note should be visible on all pages, with no duplicate
# banners or dependency on a dynamic widget.
for page in [dist / "windmills/index.html", dist / "windmills/projects/index.html",
             dist / "windmills/writing/the-first-step/index.html"]:
    html = page.read_text(encoding="utf-8")
    assert html.count("Pardon our dust!") == 1, f"Missing or duplicate site notice: {page}"

# The Projects index is hand-curated, with exactly the intended active projects
# and the existing public research artifact. Keep the links verifiable in HTML.
projects = (dist / "windmills/projects/index.html").read_text(encoding="utf-8")
assert 'id="current-projects"' in projects, "Missing current projects section"
assert 'id="published-tools"' in projects, "Missing published tools section"
for url in (
    "/interp/",
    "/interp/#zoo",
    "https://github.com/bubskee/stars-elegy",
    "https://github.com/bubskee/euphoria-axis",
    "https://huggingface.co/bubskee/qwen3-14b-jr-lenses",
    "https://github.com/bubskee/euphoria-axis/blob/main/releases/qwen3-14b-jr-lenses/README.md",
):
    assert f'href="{url}"' in projects, f"Missing project link: {url}"
interp = (dist / "interp/index.html").read_text(encoding="utf-8")
assert 'id="zoo"' in interp and 'href="leg-day.html"' in interp, "Missing illustrated zoo entrance"
assert (dist / "interp/leg-day.html").is_file(), "Missing opening exhibit"
assert "Projects coming soon." not in projects, "Stale projects placeholder"
print("Construction note and current/public projects verified.")

# About page is a short, linked introduction with the original graph mark.
about = (dist / "windmills/about/index.html").read_text(encoding="utf-8")
assert 'class="about-profile"' in about and 'class="about-copy"' in about
assert 'alt="Personal logo: three connected nodes on a dark background"' in about
assert 'src="/windmills/img/github_logo.png"' in about, "Logo must use the site URL prefix"
from re import search
bio = search(r'<div class="about-copy">(.*?)<nav class="about-links"', about, flags=__import__("re").DOTALL)
assert bio is not None, "Missing about introduction"
assert bio.group(1).count("<p>") == 3, "The about blurb should be exactly three sentences in three paragraphs"
for url in ("https://github.com/bubskee", "https://x.com/tylting", "/windmills/projects/"):
    assert f'href="{url}"' in about, f"Missing about link: {url}"
assert 'href="https://x.com/tylting"' in (dist / "windmills/index.html").read_text(encoding="utf-8"), "Missing site-wide Twitter link"
logo = dist / "windmills/img/github_logo.png"
assert logo.is_file() and logo.stat().st_size == 10026, "Original consensus-knot logo missing or modified"
assert logo.read_bytes().startswith(bytes.fromhex("89504e470d0a1a0a")), "Logo is not a PNG"
print("About portrait, three-sentence blurb, social links, and site footer verified.")

print("Fresh HCTiGT article and image, Colab, canonical URL, RSS, and redirects verified.")
