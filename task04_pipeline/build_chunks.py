#!/usr/bin/env python
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable
from zipfile import ZipFile

try:
    from task04_pipeline.task03_adapter import get_insert_vectors
except ModuleNotFoundError:
    from task03_adapter import get_insert_vectors


DOC_TITLE_PREFIX = "中国科学院上海高等研究院"
DOC_CODE_RE = re.compile(
    r"[(（]?\s*"
    r"(?P<code>[^()（）\n]*?(?:〔|\[)\d{4}(?:〕|\])\s*\d+\s*号)"
    r"(?:\s*[,，]\s*(?P<date>\d{4}-\d{1,2}-\d{1,2})[^()（）\n]*)?"
    r"\s*[)）]?"
)
CHAPTER_RE = re.compile(r"^第[一二三四五六七八九十百零0-9]+章\s*(.+)$")
ARTICLE_RE = re.compile(r"^第[一二三四五六七八九十百零0-9]+条\s*(.*)$")
SECTION_RE = re.compile(r"^[一二三四五六七八九十]+、\s*(.+)$")
SUBSECTION_RE = re.compile(r"^[（(][一二三四五六七八九十0-9]+[)）]\s*(.+)$")
ENUM_RE = re.compile(r"^\d+[.．、]\s*(.+)$")
PAGE_ARTIFACT_RE = re.compile(r"^\s*[·•\-_]{3,}\s*$")
TITLE_ENDINGS = (
    "办法",
    "办法（试行）",
    "管理办法",
    "实施办法",
    "实施细则",
    "实施细则（暂行）",
    "规定",
    "条例",
    "细则",
    "协议书",
    "承诺书",
    "通知单",
    "登记表",
    "申请表",
    "任务书",
    "审批表",
    "小结",
    "结构表",
)


@dataclass
class SourceConfig:
    path: Path
    domain: str
    source_url: str | None = None
    source_name: str | None = None
    source_type: str | None = None
    publish_year: int | None = None
    extra_metadata: dict[str, Any] = field(default_factory=dict)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="任务 04: 双域语料自动化清洗、分块与入库流水线"
    )
    parser.add_argument(
        "--input",
        nargs="+",
        required=True,
        help="输入文件路径，支持 md/docx/pdf",
    )
    parser.add_argument(
        "--domain",
        required=True,
        choices=["graduate", "party"],
        help="语料域标识",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="输出 JSONL 文件路径",
    )
    parser.add_argument(
        "--manifest",
        help="可选 JSON 清单文件，用于补充来源链接、来源名称等元数据",
    )
    parser.add_argument(
        "--source-url",
        help="单文件场景下的来源链接，多个文件时建议使用 manifest",
    )
    parser.add_argument(
        "--source-name",
        help="单文件场景下的来源名称，例如“高研院研究生处”",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=820,
        help="每个文本块的目标字符数，默认 820",
    )
    parser.add_argument(
        "--min-chunk-size",
        type=int,
        default=180,
        help="最小分块字符数，默认 180",
    )
    parser.add_argument(
        "--insert",
        action="store_true",
        help="输出完成后调用任务 03 的 insert_vectors(data)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="同时额外输出一个缩进版 JSON 文件，便于人工抽查",
    )
    return parser.parse_args()


def load_manifest(manifest_path: str | None) -> dict[str, dict[str, Any]]:
    if not manifest_path:
        return {}

    path = Path(manifest_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return data
    if isinstance(data, list):
        result: dict[str, dict[str, Any]] = {}
        for item in data:
            key = item["path"]
            result[key] = item
        return result
    raise ValueError("manifest 必须是 JSON 对象或对象数组")


def build_source_configs(args: argparse.Namespace) -> list[SourceConfig]:
    manifest = load_manifest(args.manifest)
    configs: list[SourceConfig] = []
    for raw_input in args.input:
        path = Path(raw_input).resolve()
        manifest_item = (
            manifest.get(raw_input)
            or manifest.get(raw_input.replace("\\", "/"))
            or manifest.get(path.name)
            or manifest.get(str(path))
            or manifest.get(path.as_posix())
            or {}
        )
        source_url = manifest_item.get("source_url", args.source_url)
        source_name = manifest_item.get("source_name", args.source_name)
        source_type = manifest_item.get("source_type")
        publish_year = manifest_item.get("publish_year")
        extra_metadata = manifest_item.get("extra_metadata", {})
        configs.append(
            SourceConfig(
                path=path,
                domain=args.domain,
                source_url=source_url,
                source_name=source_name,
                source_type=source_type,
                publish_year=publish_year,
                extra_metadata=extra_metadata,
            )
        )
    return configs


def read_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".md":
        return path.read_text(encoding="utf-8")
    if suffix == ".docx":
        return read_docx(path)
    if suffix == ".pdf":
        return read_pdf(path)
    raise ValueError(f"暂不支持的文件类型: {path.suffix}")


def read_docx(path: Path) -> str:
    from xml.etree import ElementTree as ET

    with ZipFile(path) as zf:
        xml = zf.read("word/document.xml")

    root = ET.fromstring(xml)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs: list[str] = []
    for p in root.findall(".//w:p", ns):
        texts = [node.text for node in p.findall(".//w:t", ns) if node.text]
        if texts:
            paragraphs.append("".join(texts).strip())
        else:
            paragraphs.append("")
    return "\n".join(paragraphs)


def read_pdf(path: Path) -> str:
    pdftotext_result = try_pdftotext(path)
    if pdftotext_result:
        return pdftotext_result

    for module_name in ("pypdf", "PyPDF2"):
        try:
            if module_name == "pypdf":
                from pypdf import PdfReader  # type: ignore
            else:
                from PyPDF2 import PdfReader  # type: ignore
            reader = PdfReader(str(path))
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n".join(pages)
        except ModuleNotFoundError:
            continue

    raise RuntimeError(
        "PDF 解析失败：未找到 pdftotext，且当前环境未安装 pypdf/PyPDF2。"
    )


def try_pdftotext(path: Path) -> str | None:
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", str(path), "-"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None

    return result.stdout


def normalize_text(text: str) -> str:
    text = text.replace("\ufeff", "")
    text = text.replace("\u3000", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("﹞", "〕")
    text = text.replace("（暂行)", "（暂行）")
    lines = [normalize_line(line) for line in text.split("\n")]

    normalized: list[str] = []
    previous_blank = False
    for line in lines:
        if not line:
            if not previous_blank:
                normalized.append("")
            previous_blank = True
            continue
        normalized.append(line)
        previous_blank = False

    return "\n".join(normalized).strip()


def normalize_line(line: str) -> str:
    line = re.sub(r"[ \t]+", " ", line.strip())
    if PAGE_ARTIFACT_RE.match(line):
        return ""
    return line


def split_compilation_into_documents(text: str) -> list[list[str]]:
    lines = text.splitlines()
    documents: list[list[str]] = []
    current: list[str] = []
    started = False

    for index, line in enumerate(lines):
        next_line = lines[index + 1] if index + 1 < len(lines) else ""
        if is_document_start(line, next_line, current):
            if current:
                documents.append(trim_document_lines(current))
                current = []
            started = True

        if started:
            current.append(line)

    if current:
        documents.append(trim_document_lines(current))

    if not documents:
        return [trim_document_lines(lines)]
    return [doc for doc in documents if doc]


def is_document_start(line: str, next_line: str, current: list[str]) -> bool:
    if not line or not line.startswith(DOC_TITLE_PREFIX):
        return False
    if not is_possible_doc_title(line, next_line):
        return False
    if not current:
        return True
    previous_non_empty = next((item for item in reversed(current) if item.strip()), "")
    if "文件清单" in previous_non_empty:
        return True
    if previous_non_empty.startswith(DOC_TITLE_PREFIX):
        return False
    return True


def is_possible_doc_title(line: str, next_line: str) -> bool:
    stripped = line.strip()
    if stripped == DOC_TITLE_PREFIX:
        return True
    if is_complete_title(stripped):
        return True
    return should_append_title_line(stripped, next_line)


def trim_document_lines(lines: list[str]) -> list[str]:
    trimmed = list(lines)
    while trimmed and not trimmed[0].strip():
        trimmed.pop(0)
    while trimmed and not trimmed[-1].strip():
        trimmed.pop()
    return trimmed


def extract_doc_metadata(
    doc_lines: list[str],
    source: SourceConfig,
) -> tuple[dict[str, Any], list[str]]:
    title_parts: list[str] = []
    body_start = 0
    title_parts.append(doc_lines[0].strip())

    if len(doc_lines) > 1 and should_append_title_line(doc_lines[0], doc_lines[1]):
        title_parts.append(doc_lines[1].strip())
        body_start = 2
    else:
        body_start = 1

    title = "".join(part for part in title_parts if part)
    doc_code = None
    publish_date = None
    publish_year = source.publish_year

    if body_start < len(doc_lines):
        code_match = DOC_CODE_RE.search(doc_lines[body_start])
        if code_match:
            doc_code = code_match.group("code").strip()
            publish_date = code_match.group("date")
            if publish_date:
                publish_year = int(publish_date[:4])
            body_start += 1

    metadata: dict[str, Any] = {
        "domain": source.domain,
        "source_file": source.path.name,
        "source_path": str(source.path),
        "source_type": source.source_type or source.path.suffix.lower().lstrip("."),
        "source_url": source.source_url,
        "source_name": source.source_name,
        "doc_title": title,
        "doc_code": doc_code,
        "publish_date": publish_date,
        "publish_year": publish_year,
    }
    metadata.update(source.extra_metadata)
    body_lines = trim_document_lines(doc_lines[body_start:])
    return metadata, body_lines


def looks_like_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    return any(
        pattern.match(stripped)
        for pattern in (CHAPTER_RE, ARTICLE_RE, SECTION_RE, SUBSECTION_RE, ENUM_RE)
    )


def should_append_title_line(first_line: str, second_line: str) -> bool:
    first = first_line.strip()
    second = second_line.strip()
    if not second or looks_like_heading(second):
        return False
    if DOC_CODE_RE.search(second):
        return False
    if second in {"研究生处", "年 月 日"}:
        return False
    if first == DOC_TITLE_PREFIX:
        return True
    return not is_complete_title(first)


def is_complete_title(title: str) -> bool:
    stripped = title.strip()
    return any(stripped.endswith(ending) for ending in TITLE_ENDINGS)


def build_chunks_from_document(
    doc_lines: list[str],
    doc_meta: dict[str, Any],
    chunk_size: int,
    min_chunk_size: int,
) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    chapter = ""
    article = ""
    section = ""
    paragraph_buffer: list[str] = []

    def flush_buffer() -> None:
        nonlocal paragraph_buffer
        if not paragraph_buffer:
            return
        base_text = "\n".join(line for line in paragraph_buffer if line).strip()
        paragraph_buffer = []
        if not base_text:
            return

        for text in split_large_text(base_text, chunk_size, min_chunk_size):
            section_path = [item for item in [chapter, article, section] if item]
            metadata = dict(doc_meta)
            metadata["section_path"] = " > ".join(section_path) if section_path else None
            metadata["chapter_title"] = chapter or None
            metadata["article_title"] = article or None
            metadata["section_title"] = section or None
            chunks.append({"text": text, "metadata": metadata})

    for raw_line in doc_lines:
        line = raw_line.strip()
        if not line:
            flush_buffer()
            continue

        chapter_match = CHAPTER_RE.match(line)
        if chapter_match:
            flush_buffer()
            chapter = line
            article = ""
            section = ""
            continue

        article_match = ARTICLE_RE.match(line)
        if article_match:
            flush_buffer()
            article = line
            section = ""
            paragraph_buffer.append(line)
            continue

        section_match = SECTION_RE.match(line)
        if section_match:
            flush_buffer()
            section = line
            paragraph_buffer.append(line)
            continue

        subsection_match = SUBSECTION_RE.match(line)
        if subsection_match and paragraph_buffer:
            flush_buffer()
            section = line
            paragraph_buffer.append(line)
            continue

        if is_noise_line(line):
            continue

        paragraph_buffer.append(line)

    flush_buffer()
    return merge_small_chunks(chunks, chunk_size, min_chunk_size)


def is_noise_line(line: str) -> bool:
    if line == "研究生教育管理规章制度汇编文件清单":
        return True
    if re.match(r"^\d+\.\s*中国科学院上海高等研究院", line):
        return True
    if len(line) <= 3 and re.fullmatch(r"[一二三四五六七八九十]+", line):
        return True
    return False


def split_large_text(text: str, chunk_size: int, min_chunk_size: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text]

    sentences = split_sentences(text)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if not current:
            current = sentence
            continue
        if len(current) + len(sentence) <= chunk_size:
            current += sentence
            continue
        chunks.append(current.strip())
        current = sentence
    if current:
        chunks.append(current.strip())

    if len(chunks) >= 2 and len(chunks[-1]) < min_chunk_size:
        chunks[-2] = chunks[-2] + chunks[-1]
        chunks.pop()
    return chunks


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[。！？；])", text)
    return [part for part in parts if part]


def merge_small_chunks(
    chunks: list[dict[str, Any]],
    chunk_size: int,
    min_chunk_size: int,
) -> list[dict[str, Any]]:
    if not chunks:
        return []

    merged: list[dict[str, Any]] = []
    for item in chunks:
        if (
            merged
            and len(item["text"]) < min_chunk_size
            and len(merged[-1]["text"]) + len(item["text"]) <= chunk_size + min_chunk_size
            and merged[-1]["metadata"]["doc_title"] == item["metadata"]["doc_title"]
            and merged[-1]["metadata"].get("section_path") == item["metadata"].get("section_path")
        ):
            merged[-1]["text"] = merged[-1]["text"].rstrip() + "\n" + item["text"].lstrip()
            continue
        merged.append(item)
    return merged


def finalize_chunks(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    finalized: list[dict[str, Any]] = []
    for index, item in enumerate(chunks, start=1):
        metadata = dict(item["metadata"])
        doc_title = metadata["doc_title"]
        section_path = metadata.get("section_path") or ""
        stable_key = f"{doc_title}|{section_path}|{item['text']}"
        chunk_id = hashlib.sha1(stable_key.encode("utf-8")).hexdigest()[:16]
        metadata["chunk_id"] = chunk_id
        metadata["chunk_index"] = index
        metadata["char_count"] = len(item["text"])
        metadata["token_estimate"] = estimate_zh_tokens(item["text"])
        finalized.append(
            {
                "id": chunk_id,
                "text": item["text"],
                "metadata": metadata,
            }
        )
    return finalized


def estimate_zh_tokens(text: str) -> int:
    return max(1, int(len(text) * 0.9))


def build_records(
    sources: Iterable[SourceConfig],
    chunk_size: int,
    min_chunk_size: int,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for source in sources:
        raw_text = read_text(source.path)
        normalized_text = normalize_text(raw_text)
        documents = split_compilation_into_documents(normalized_text)
        for doc_lines in documents:
            doc_meta, body_lines = extract_doc_metadata(doc_lines, source)
            if not body_lines:
                continue
            doc_chunks = build_chunks_from_document(
                body_lines,
                doc_meta,
                chunk_size=chunk_size,
                min_chunk_size=min_chunk_size,
            )
            records.extend(doc_chunks)
    return finalize_chunks(records)


def write_outputs(records: list[dict[str, Any]], output_path: Path, pretty: bool) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    if pretty:
        pretty_path = output_path.with_suffix(".json")
        pretty_path.write_text(
            json.dumps(records, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def print_summary(records: list[dict[str, Any]]) -> None:
    unique_docs = sorted({record["metadata"]["doc_title"] for record in records})
    summary = {
        "chunk_count": len(records),
        "document_count": len(unique_docs),
        "documents": unique_docs,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def main() -> int:
    args = parse_args()
    sources = build_source_configs(args)
    records = build_records(
        sources=sources,
        chunk_size=args.chunk_size,
        min_chunk_size=args.min_chunk_size,
    )
    output_path = Path(args.output).resolve()
    write_outputs(records, output_path, pretty=args.pretty)
    print_summary(records)

    if args.insert:
        insert_vectors = get_insert_vectors()
        insert_vectors(records)
        print("insert_vectors(data) 调用完成。")

    return 0


if __name__ == "__main__":
    sys.exit(main())
