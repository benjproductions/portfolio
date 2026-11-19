#!/usr/bin/env python3
import json
import re
import pathlib

TODAY = "2026-11-19"
ROOT = pathlib.Path("/workspace/serum2-transcripts")
RAW = ROOT / "raw"
DOCS = ROOT / "docs"
DOCS.mkdir(exist_ok=True)

playlist = json.loads((ROOT / "playlist.json").read_text())
details = {
    d["video_id"]: d
    for d in json.loads((RAW / "details_all.json").read_text())
}

MARKER_RE = re.compile(
    r"\[(?:Music|Applause|music|applause|♪♪♪|MUSIC|APPLAUSE)\]|♪"
)


def clean_transcript(text: str) -> str:
    if not text or not text.strip():
        return "NO TRANSCRIPT AVAILABLE"
    text = MARKER_RE.sub(" ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"(?<=[.!?])\s+", text)
    parts = [p.strip() for p in parts if p.strip()]
    paras = []
    buf = []
    for p in parts:
        buf.append(p)
        if len(buf) >= 5:
            paras.append(" ".join(buf))
            buf = []
    if buf:
        paras.append(" ".join(buf))
    return "\n\n".join(paras) if paras else text


def safe_name(title: str) -> str:
    s = re.sub(r'[/\\:*?"<>|]', "", title)
    s = re.sub(r"\s+", " ", s).strip()
    return s


summary = []
combined = []
missing_files = []

for v in playlist:
    vid = v["video_id"]
    pos = v["pos"]
    title = v["title"]
    url = v["url"]
    det = details.get(vid, {})
    upload = det.get("upload_date") or det.get("published_at") or ""
    upload_day = upload[:10] if upload else "unknown"

    raw_path = RAW / f"{vid}.json"
    status = "none"
    body = "NO TRANSCRIPT AVAILABLE"
    if raw_path.exists():
        data = json.loads(raw_path.read_text())
        kind = data.get("kind")
        has = data.get("has_transcript")
        ft = data.get("full_text") or ""
        if has and ft.strip():
            body = clean_transcript(ft)
            status = "OK" if kind == "manual" else "auto-captions"
        else:
            status = "none"
            body = "NO TRANSCRIPT AVAILABLE"
    else:
        missing_files.append(vid)

    lesson_num = f"{pos:02d}"
    fname = f"TRANSCRIPT - {TODAY} - Xfer Serum 2 Tutorials - {safe_name(title)}"
    doc = (
        f"Course: Xfer Serum 2 Tutorials (The Sound Design Channel)\n"
        f"Lesson: {lesson_num} - {title}\n"
        f"Source: {url}\n"
        f"Transcript: Captions pulled {TODAY}\n"
        f"\n"
        f"{body}\n"
    )
    (DOCS / f"{fname}.txt").write_text(doc)
    combined.append(f"File name: {fname}\n\n{doc}")
    wc = 0 if body == "NO TRANSCRIPT AVAILABLE" else len(body.split())
    summary.append(
        {
            "pos": pos,
            "title": title,
            "url": url,
            "upload_date": upload_day,
            "status": status,
            "word_count": wc,
            "filename": fname,
            "video_id": vid,
        }
    )

(ROOT / "ALL_TRANSCRIPTS.md").write_text("\n======\n\n".join(combined))
(ROOT / "summary.json").write_text(json.dumps(summary, indent=2))
print("docs", len(summary), "missing_raw", missing_files)
print("total_words", sum(s["word_count"] for s in summary))
