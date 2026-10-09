"""
Rebuilds data/euclid-heath.txt from the Perseus Digital Library: Euclid's Elements in Thomas
Heath's translation (Cambridge, 1908), its TEI text fetched at a pinned commit of
PerseusDL/canonical-greekLit, checksum-verified, and cleaned to Euclid's text alone:

- kept: the definitions, postulates, common notions and propositions of the 13 books, in order
  (Book VI's definitions 2 and 5 are empty here: Heath moves them to his notes as spurious);
- dropped: Heath's introductions (the historical notes before Books XII and XIII) and notes, the
  headings, the figures, the labels Perseus added to some propositions (Enunciation, Proof., QED.),
  Heath's daggers marking passages his notes discuss, his citations in brackets, marked up
  ([I. 46], [X. 15, addition]) or plain (EDITORIAL: [C. N. 2], [id.], [Lemma], ...), and his
  alternative numbering of the common notions; line and page breaks are markup only;
- kept in Heath's brackets: the words he supplies for sense and the passages he judges
  interpolated, two of them whole propositions (I. 40, X. 10);
- each paragraph on one line; a definition, postulate, common notion or proposition is its
  paragraphs, one after another, separated from the next by a blank line; books by two;
- two typos in the source corrected (ERRATA);
- normalized to ASCII: accents stripped, dashes as - and --, curly quotes straight. Any other
  non-ASCII character is an error, not a silent change: the Greek Heath quotes is all in his
  introductions and notes, so none should remain.

    python3 clean.py            # fetch, verify, clean, write data/euclid-heath.txt
    python3 clean.py --check    # the same, then compare with the committed file, byte for byte

Python 3.10+, standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET

COMMIT = "70427323b61267cdcd0256b9b02009c23392de07"
PATH = "data/tlg1799/tlg001/tlg1799.tlg001.perseus-eng2.xml"
URL = f"https://raw.githubusercontent.com/PerseusDL/canonical-greekLit/{COMMIT}/{PATH}"
SHA256 = "b41068f265202520a6c3dccb512b258a01b298be6004763cb92057ccd50802a8"
OUT = "data/euclid-heath.txt"

TEI = "{http://www.tei-c.org/ns/1.0}"
# dropped with their text: a heading, a note, a figure (and, in flatten, a label Perseus added)
DROPPED = {f"{TEI}head", f"{TEI}note", f"{TEI}figure"}
# markup only: their text, if any, is kept
BREAKS = {f"{TEI}lb", f"{TEI}pb"}
# a cross-reference's place while the text is flattened
REF = "\x00"

# the source's typos that cleaning depends on, each fixed where it occurs exactly once: (old, new)
ERRATA = [
    # VI. 20: a citation's bracket left open
    (
        '[<ref target="elem.5.12">V. 12</ref> therefore, as the triangle',
        '[<ref target="elem.5.12">V. 12</ref>] therefore, as the triangle',
    ),
    # X. 26: the scan's 4 for A
    (
        '<p><hi rend="italic">4 medial area does not exceed',
        '<p><hi rend="italic">A medial area does not exceed',
    ),
]

# Heath's brackets that cite or label rather than translate, written as plain text: common notions
# ([C. N. 2]), [id.], lemmas, parts and cases, a definition, his alternative numbering of the
# common notions ([7]) and a pointer to his notes. Each must occur: a source that changed fails
EDITORIAL = [
    r"\[C\. N\. \d\]",
    r"\[id\.\]",
    r"\[(?:cf\. )?Lemma(?: following)?\]",
    r"\[Part \d\.\]",
    r"\[First part of this Prop\.\]",
    r"\[Case (?:\d|I)\.\]",
    r"\[VI\. Def\. I\]",
    r"\[\d\]",
    r"\[Reciprocally related figures\. See note\.\]",
]
# each pattern's removals, which clean checks
REMOVED: dict[str, int] = dict.fromkeys(EDITORIAL, 0)

# characters NFKD doesn't reduce to ASCII
SPELLED = {"—": "--", "–": "-", "‘": "'", "’": "'", "“": '"', "”": '"', "æ": "ae", "œ": "oe"}


def fetch() -> bytes:
    request = urllib.request.Request(URL, headers={"User-Agent": "indrajala-datasets-euclid-heath/clean.py"})
    with urllib.request.urlopen(request) as response:
        raw = response.read()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != SHA256:
        sys.exit(f"{PATH} at {COMMIT[:7]}: sha256 is {actual}, expected {SHA256}")
    return raw


def corrected(raw: bytes) -> str:
    source = raw.decode("utf-8")
    for old, new in ERRATA:
        if source.count(old) != 1:
            raise ValueError(f"an erratum's text occurs {source.count(old)} times, not once: {old!r}")
        source = source.replace(old, new)
    return source


def flatten(element: ET.Element) -> str:
    """element's text, with dropped elements removed and each cross-reference as REF."""
    parts = [element.text or ""]
    for child in element:
        if child.tag in DROPPED or (child.tag == f"{TEI}label" and child.get("resp") == "perseus"):
            pass
        elif child.tag == f"{TEI}ref":
            parts.append(REF)
        elif child.tag in BREAKS:
            parts.append(" ")
        else:
            parts.append(flatten(child))
        parts.append(child.tail or "")
    return "".join(parts)


def paragraph(p: ET.Element) -> str:
    text = flatten(p)
    # a citation: a bracketed group holding a cross-reference, [I. 46], [I. 13 and I. 14],
    # [cf. VII. 13] or [X. 15, addition], with the space before it. A bracket without one is
    # Heath's and stays
    text = re.sub(rf"\s*\[[^\[\]]*{REF}[^\[\]]*\]", "", text)
    for pattern in EDITORIAL:
        text, count = re.subn(r"\s*" + pattern, "", text)
        REMOVED[pattern] += count
    # Heath's daggers, marking passages his notes discuss: his, not Euclid's
    text = text.replace("\u2020", " ")
    if REF in text:
        raise ValueError(f"a cross-reference outside brackets: {' '.join(text.split())[:120]!r}")
    return " ".join(text.split())


def item(div: ET.Element) -> str:
    """A definition, postulate, common notion or proposition: its paragraphs, a line each."""
    loose = [child.tag for child in div if child.tag not in DROPPED | BREAKS | {f"{TEI}p"}]
    if loose:
        raise ValueError(f"unexpected elements in {div.get('n')}: {loose}")
    lines = [line for line in (paragraph(p) for p in div.findall(f"{TEI}p")) if line]
    # a proposition Heath brackets whole as interpolated (I. 40, X. 10) opens its bracket in its
    # heading; the bracket stays, as with his other interpolations
    head = div.find(f"{TEI}head")
    if head is not None and (head.text or "").startswith("["):
        lines[0] = "[" + lines[0]
    return "\n".join(lines)


def book(div: ET.Element) -> str:
    # each section (definitions, postulates, common notions, propositions; Book X's three parts)
    # is a div of items; the loose paragraphs are Heath's introductions, dropped
    items = [item(entry) for section in div.findall(f"{TEI}div") for entry in section.findall(f"{TEI}div")]
    return "\n\n".join(text for text in items if text)


def to_ascii(text: str) -> str:
    text = "".join(SPELLED.get(c, c) for c in text)
    text = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))
    bad = sorted({c for c in text if ord(c) > 127})
    if bad:
        raise ValueError(f"characters with no ASCII form here: {bad}")
    return text


def clean() -> str:
    body = ET.fromstring(corrected(fetch())).find(f"{TEI}text/{TEI}body")
    assert body is not None, "no TEI body"
    books = body.findall(f"{TEI}div/{TEI}div")
    if [b.get("n") for b in books] != [str(n) for n in range(1, 14)]:
        raise ValueError(f"expected Books 1-13; got {[b.get('n') for b in books]}")
    text = "\n\n\n".join(book(b) for b in books)
    unused = [pattern for pattern, count in REMOVED.items() if count == 0]
    if unused:
        raise ValueError(f"editorial brackets that no longer occur: {unused}")
    return to_ascii(text) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="compare with the committed file instead of writing it")
    args = parser.parse_args()
    text = clean().encode("ascii")
    if args.check:
        with open(OUT, "rb") as f:
            same = f.read() == text
        print("reproduced exactly" if same else "differs from the committed file")
        sys.exit(0 if same else 1)
    with open(OUT, "wb") as f:
        f.write(text)
    print(f"wrote {OUT}: {len(text)} bytes, sha256 {hashlib.sha256(text).hexdigest()}")


if __name__ == "__main__":
    main()
