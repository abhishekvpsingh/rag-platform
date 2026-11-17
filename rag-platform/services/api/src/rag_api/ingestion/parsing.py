"""Pure parsers; production callers must use the isolated runner."""

import csv
import io
import re
import zipfile
from html.parser import HTMLParser
from pathlib import PurePosixPath
from xml.etree.ElementTree import Element

from defusedxml.ElementTree import fromstring  # type: ignore[import-untyped]
from pydantic import BaseModel, ConfigDict, Field
from pypdf import PdfReader

MAX_FILE = 8 * 1024 * 1024
MAX_TEXT = 2 * 1024 * 1024
MAX_BLOCKS = 10000
PARSER_VERSION = "structured-v1"


class ParseFailure(Exception):
    """Safe machine-readable reason, never source content."""


class Block(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    text: str = Field(max_length=MAX_TEXT)
    locator: str = Field(max_length=512)
    section: str = Field(default="", max_length=512)
    kind: str = "text"


class Parsed(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    blocks: list[Block] = Field(max_length=MAX_BLOCKS)
    parser_version: str = PARSER_VERSION


def archive(data: bytes) -> zipfile.ZipFile:
    z = zipfile.ZipFile(io.BytesIO(data))
    entries = z.infolist()
    if len(entries) > 2000 or sum(x.file_size for x in entries) > 32 * 1024 * 1024:
        raise ParseFailure("expanded_size_limit")
    names = [x.filename for x in entries]
    if len(set(names)) != len(names):
        raise ParseFailure("duplicate_archive_member")
    for item in entries:
        path = PurePosixPath(item.filename)
        if path.is_absolute() or ".." in path.parts or item.flag_bits & 1:
            raise ParseFailure("unsafe_archive")
        if item.file_size > 8 * 1024 * 1024 or item.file_size > max(1, item.compress_size) * 200:
            raise ParseFailure("expanded_size_limit")
        if any(word in item.filename.lower() for word in ("vbaproject", "embeddings/", "activex/")):
            raise ParseFailure("active_content")
    return z


def xml(z: zipfile.ZipFile, name: str) -> Element:
    return fromstring(z.read(name))  # type: ignore[no-any-return]


def plain(data: bytes, markdown: bool) -> list[Block]:
    text = data.decode("utf-8-sig")
    if "\x00" in text:
        raise ParseFailure("binary_text")
    blocks = []
    section = ""
    for number, line in enumerate(text.splitlines(), 1):
        if markdown and re.match(r"^#{1,6}\s", line):
            section = line.lstrip("# ").strip()[:512]
        if line.strip():
            blocks.append(Block(text=line, locator=f"line:{number}", section=section))
    return blocks


class SafeHTML(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hidden = 0
        self.blocks: list[Block] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "iframe", "object", "svg", "template"}:
            self.hidden += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "iframe", "object", "svg", "template"}:
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data: str) -> None:
        if not self.hidden and data.strip():
            self.blocks.append(
                Block(text=data.strip(), locator=f"html-text:{len(self.blocks) + 1}")
            )


def docx(data: bytes) -> list[Block]:
    with archive(data) as z:
        root = xml(z, "word/document.xml")
        ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        body = root.find(f"{ns}body")
        if body is None:
            raise ParseFailure("malformed_document")
        blocks: list[Block] = []
        section = ""
        for index, node in enumerate(body, 1):
            if node.tag == ns + "p":
                text = "".join(x.text or "" for x in node.iter(ns + "t"))
                style = node.find(f"{ns}pPr/{ns}pStyle")
                if style is not None and "heading" in style.get(ns + "val", "").lower():
                    section = text[:512]
                if text.strip():
                    blocks.append(
                        Block(text=text, locator=f"body:{index}/paragraph", section=section)
                    )
            elif node.tag == ns + "tbl":
                rows = node.findall(ns + "tr")
                header = ""
                for number, row in enumerate(rows, 1):
                    values = [
                        " ".join(x.text or "" for x in cell.iter(ns + "t"))
                        for cell in row.findall(ns + "tc")
                    ]
                    text = " | ".join(values)
                    if number == 1:
                        header = text
                    blocks.append(
                        Block(
                            text=text if number == 1 else header + "\n" + text,
                            locator=f"body:{index}/table-row:{number}",
                            section=section,
                            kind="table",
                        )
                    )
        return blocks


def xlsx(data: bytes) -> list[Block]:
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    relns = "{http://schemas.openxmlformats.org/package/2006/relationships}"
    docrel = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    with archive(data) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            shared = [
                "".join(t.text or "" for t in node.iter(ns + "t"))
                for node in xml(z, "xl/sharedStrings.xml").findall(ns + "si")
            ]
        relationships = {
            r.get("Id"): r
            for r in xml(z, "xl/_rels/workbook.xml.rels").findall(relns + "Relationship")
        }
        blocks = []
        for sheet in xml(z, "xl/workbook.xml").iter(ns + "sheet"):
            name = sheet.get("name", "")[:128]
            relation = relationships.get(sheet.get(docrel))
            if relation is None or relation.get("TargetMode") == "External":
                raise ParseFailure("unsafe_workbook")
            target = relation.get("Target", "")
            path = PurePosixPath(target)
            if ".." in path.parts:
                raise ParseFailure("unsafe_workbook")
            member = target.lstrip("/") if target.startswith("/xl/") else "xl/" + target
            root = xml(z, member)
            header = ""
            for row in root.iter(ns + "row"):
                values = []
                for cell in row.findall(ns + "c"):
                    if cell.find(ns + "f") is not None:
                        raise ParseFailure("formula_not_supported")
                    value = cell.find(ns + "v")
                    text = value.text or "" if value is not None else ""
                    if cell.get("t") == "s":
                        text = shared[int(text)]
                    elif cell.get("t") == "inlineStr":
                        text = "".join(t.text or "" for t in cell.iter(ns + "t"))
                    values.append(f"{cell.get('r', '')}={text}")
                text = " | ".join(values)
                if not header:
                    header = text
                blocks.append(
                    Block(
                        text=header if header == text else header + "\n" + text,
                        locator=f"sheet:{name}/row:{row.get('r', '')}",
                        section=name,
                        kind="table",
                    )
                )
        return blocks


def parse(data: bytes, format: str) -> Parsed:
    if not data or len(data) > MAX_FILE:
        raise ParseFailure("file_size_limit")
    try:
        if format in {"txt", "md"}:
            blocks = plain(data, format == "md")
        elif format == "html":
            parser = SafeHTML()
            parser.feed(data.decode("utf-8-sig"))
            blocks = parser.blocks
        elif format == "csv":
            csv.field_size_limit(65536)
            rows = csv.reader(io.StringIO(data.decode("utf-8-sig")))
            blocks = []
            header = next(rows)
            blocks.append(
                Block(text="Columns: " + " | ".join(header), locator="row:1", kind="schema")
            )
            for number, row in enumerate(rows, 2):
                if len(row) != len(header):
                    raise ParseFailure("inconsistent_columns")
                blocks.append(
                    Block(
                        text=" | ".join(
                            f"{key}: {value}" for key, value in zip(header, row, strict=True)
                        ),
                        locator=f"row:{number}",
                        kind="table",
                    )
                )
                if number > MAX_BLOCKS:
                    raise ParseFailure("row_limit")
        elif format == "docx":
            blocks = docx(data)
        elif format == "xlsx":
            blocks = xlsx(data)
        elif format == "pdf":
            if not data.startswith(b"%PDF-"):
                raise ParseFailure("mime_mismatch")
            reader = PdfReader(io.BytesIO(data), strict=True)
            if reader.is_encrypted:
                raise ParseFailure("encrypted_document")
            if len(reader.pages) > 200:
                raise ParseFailure("page_limit")
            blocks = []
            for number, page in enumerate(reader.pages, 1):
                text = page.extract_text()
                if text.strip():
                    blocks.append(Block(text=text, locator=f"page:{number}"))
                else:
                    raise ParseFailure("ocr_required")
        else:
            raise ParseFailure("unsupported_format")
        if not blocks:
            raise ParseFailure("no_text")
        if len(blocks) > MAX_BLOCKS or sum(len(b.text.encode()) for b in blocks) > MAX_TEXT:
            raise ParseFailure("extracted_size_limit")
        return Parsed(blocks=blocks)
    except ParseFailure:
        raise
    except Exception:
        raise ParseFailure("malformed_document") from None
