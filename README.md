# indrajala-datasets-euclid-heath

Euclid's *Elements* in Thomas Heath's translation (Cambridge, 1908), all thirteen books, Euclid's
text alone, cleaned to ASCII plain text for character-level language modelling, for use by
[`indrajala-ml`](https://github.com/davidbarkhuizen/indrajala-ml) and other consumers that want a
pinned, checksum-verified source rather than a manually-supplied local copy.

This repo holds a *reproducible cleaned text*: the source is the Perseus Digital Library's TEI
text, pinned to one commit, and `clean.py` rebuilds `data/euclid-heath.txt` from it byte for byte
(`python3 clean.py --check`).

## contents

```
clean.py                            - fetches the pinned source, verifies, cleans
metadata.json                       - repo-level metadata (provenance, commit, file list)
LICENSE-TEXT.md                     - the text's licence (CC BY-SA 4.0) and attribution
data/
  euclid-heath.txt                  - 823,448 characters, 605 items, 6,102 paragraphs
  euclid-heath.txt.metadata.json    - checksum, counts, vocabulary
```

## the cleaning

- **Kept:** Euclid's text alone, in order: the definitions, postulates, common notions and
  propositions (with their lemmas and porisms) of the 13 books. 605 items: the source's 607,
  less Book VI's definitions 2 and 5, which Heath moves to his notes as spurious.
- **Dropped:** Heath's introductions (the historical notes before Books XII and XIII) and notes;
  the headings; the figures; the labels Perseus added to some propositions (Enunciation, Proof.,
  QED.); Heath's daggers, marking passages his notes discuss; his citations in brackets, marked up
  (`[I. 46]`, `[I. 13 and I. 14]`, `[X. 15, addition]`) or plain (`[C. N. 2]`, `[id.]`, `[Lemma]`,
  `[Part 1.]`); and his alternative numbering of the common notions. With the introductions go
  all the Greek he quotes.
- **Kept in Heath's brackets:** the words he supplies for sense (`[the straight line]`) and the
  passages he judges interpolated, two of them whole propositions (I. 40, X. 10).
- **Corrected:** two typos in the source (a citation's bracket left open in VI. 20; the scan's
  `4` for `A` opening X. 26).
- **Layout:** a paragraph per line; an item's paragraphs one after another, a blank line between
  items, two between books. Points are named with capital letters, as Heath prints them.
- **ASCII:** dashes as `-` and `--`, quotes straight. 67 distinct characters remain: letters
  (no `J`), the digits `1245`, space, newline and `'(),-.:;[]`.

## quick start

```python
text = open("data/euclid-heath.txt", encoding="ascii").read()
vocabulary = sorted(set(text))
```

There is no train/test split: consumers make their own (`indrajala-ml` holds out the last 10%).

## provenance

Euclid wrote the *Elements* about 300 BC; Thomas Heath's translation, from Heiberg's Greek text,
was published by Cambridge University Press in 1908 (Heath died in 1940): both public domain. The
TEI text is the Perseus Digital Library's
([catalog](https://catalog.perseus.org/catalog/urn:cts:greekLit:tlg1799.tlg001.perseus-eng1),
[repository](https://github.com/PerseusDL/canonical-greekLit)), released under CC BY-SA 4.0.
`metadata.json` gives the commit and the checksum of the raw XML, which `clean.py` verifies.

## versioning

Consumers should pin to a specific tag or commit, not `main` - see `metadata.json`'s `version`
field for this repo's own packaging version.

## license

- **The text** (`data/euclid-heath.txt`) is adapted from Perseus's and released, as Perseus's is,
  under **CC BY-SA 4.0**: attribution, and adaptations under the same licence. See
  `LICENSE-TEXT.md`.
- **This repo's packaging** (this README, `clean.py`, `metadata.json`, directory layout) is
  MIT-licensed - see `LICENSE`.
