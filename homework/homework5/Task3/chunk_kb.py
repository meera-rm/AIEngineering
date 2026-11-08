"""Task 3: turn the knowledge-base articles into vector-store records.

Chunking rule: one chunk per "## " section of an article. Sections in this corpus
are 15-149 words, well under bge-small-en-v1.5's 512-token limit, so no further
splitting is needed. A section over MAX_WORDS (none today) would be split at
blank lines so the rule still works if longer articles are added.

The output is deterministic: files are read in sorted name order, no randomness,
no timestamps, and the same input always produces byte-identical records.json.

content keeps the source text exactly, including its CRLF line endings.

Run:  python chunk_kb.py                      (expects ../HW5_materials/knowledge_base)
      python chunk_kb.py --kb-dir <path>      (knowledge base anywhere else)
Writes: records.json (list of {chunk_id, embedding_text, content, metadata})
"""

import argparse
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Default assumes the course layout (homework5/HW5_materials/knowledge_base);
# pass --kb-dir if the knowledge base lives somewhere else.
DEFAULT_KB_DIR = HERE.parent / "HW5_materials" / "knowledge_base"
OUT_FILE = HERE / "records.json"
MAX_WORDS = 300  # safety cap per chunk; well below the model's 512-token limit

FRONT_MATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.S)
SECTION_START = re.compile(r"(?m)^## ")


def parse_article(path: Path) -> tuple[dict, str]:
    """Split a file into its front-matter fields and its body text."""
    # newline="" keeps the file's own line endings (CRLF here), so content is byte-for-byte unmodified.
    with path.open(encoding="utf-8", newline="") as f:
        text = f.read()
    match = FRONT_MATTER.match(text)
    if not match:
        raise ValueError(f"{path.name}: missing front matter")
    fields = dict(line.split(": ", 1) for line in match.group(1).splitlines())
    for key in ("article_id", "title"):
        if key not in fields:
            raise ValueError(f"{path.name}: front matter has no {key}")
    return fields, text[match.end():]


def split_sections(body: str) -> list[str]:
    """Return each '## ' section exactly as written (heading line included)."""
    starts = [m.start() for m in SECTION_START.finditer(body)]
    if not starts:
        raise ValueError("article has no '## ' sections")
    if body[: starts[0]].strip():
        raise ValueError("text found before the first section")
    ends = starts[1:] + [len(body)]
    return [body[s:e].strip() for s, e in zip(starts, ends)]


def split_long(section: str) -> list[str]:
    """Split an oversized section at blank lines into pieces of <= MAX_WORDS."""
    if len(section.split()) <= MAX_WORDS:
        return [section]
    pieces, current = [], []
    for para in re.split(r"\r?\n\r?\n", section):
        if current and len(" ".join(current + [para]).split()) > MAX_WORDS:
            pieces.append("\n\n".join(current))
            current = []
        current.append(para)
    pieces.append("\n\n".join(current))
    return pieces


def section_text(content: str) -> str:
    """Section body without its '## ' heading line, with line endings normalized to \n."""
    # Embedding text is built, not source, so normalizing line endings here is fine.
    parts = content.replace("\r\n", "\n").split("\n", 1)
    return parts[1].strip() if len(parts) > 1 else ""


def article_summary(first_section: str) -> str:
    """One-sentence article summary: the first sentence of the article's first section.

    The articles have no separate summary field, but every one opens with a sentence
    saying what the article covers ("Use this article when ..."), so that sentence is
    used as the document-level summary.
    """
    text = " ".join(section_text(first_section).split())
    match = re.match(r"(.+?[.!?])(?:\s|$)", text)
    return match.group(1) if match else text


def build_embedding_text(fields: dict, summary: str, heading: str, content: str, position: int) -> str:
    """Prefix the chunk with document-level context (title, product, summary) so every
    section, including short ones like 'Limits', says which article and product it is about."""
    lines = [f"Title: {fields['title']}"]
    if fields.get("product"):
        lines.append(f"Product: {fields['product']}")
    # Chunk 1 already contains the summary sentence, so it is not repeated there.
    if position > 1:
        lines.append(f"Article summary: {summary}")
    lines.append(f"Section: {heading}")
    return "\n".join(lines) + "\n\n" + section_text(content)


def build_records(kb_dir: Path) -> list[dict]:
    paths = sorted(kb_dir.glob("*.txt"))
    if not paths:
        raise SystemExit(f"No .txt articles found in {kb_dir}. Pass --kb-dir <path to knowledge_base>.")
    records = []
    for path in paths:
        fields, body = parse_article(path)
        sections = split_sections(body)
        summary = article_summary(sections[0])
        chunks = [piece for section in sections for piece in split_long(section)]
        for position, content in enumerate(chunks, start=1):
            heading = content.splitlines()[0].removeprefix("## ").strip()
            records.append({
                "chunk_id": f"{fields['article_id']}#{position:02d}",
                "embedding_text": build_embedding_text(fields, summary, heading, content, position),
                "content": content,
                "metadata": {
                    "article_id": fields["article_id"],
                    "title": fields["title"],
                    "chunk_position": position,
                    "chunk_count": len(chunks),
                    "section_heading": heading,
                    "product": fields.get("product", ""),
                    "topic": fields.get("topic", ""),
                    "source_file": path.name,
                    "article_version": fields.get("version", ""),
                    "corpus_version": fields.get("corpus_version", ""),
                },
            })
    ids = [r["chunk_id"] for r in records]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate chunk_id found")
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Chunk the HW5 knowledge base into vector-store records.")
    parser.add_argument("--kb-dir", type=Path, default=DEFAULT_KB_DIR, help="folder containing the knowledge-base .txt articles")
    args = parser.parse_args()
    records = build_records(args.kb_dir)
    OUT_FILE.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    articles = len({r["metadata"]["article_id"] for r in records})
    words = [len(r["content"].split()) for r in records]
    print(f"{len(records)} chunks from {articles} articles -> {OUT_FILE.name}")
    print(f"content words per chunk: min {min(words)}, max {max(words)}, mean {sum(words)/len(words):.0f}")


if __name__ == "__main__":
    main()
