#!/usr/bin/env python3
"""Validate data/news.json before it goes live.

Checks: valid JSON, required fields and allowed values, school ids that exist
in index.html, no duplicate ids / URLs / headlines (including URLs listed under
relatedCoverage), ISO dates that aren't in the future, and that every
school-scoped article carries at least one Momentum signal.

Usage:  python3 scripts/validate_news.py          (exit code 1 on any error)
"""
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NEWS = ROOT / "data" / "news.json"
INDEX = ROOT / "index.html"

REQUIRED = ["id", "storyId", "schoolName", "title", "publication", "date",
            "isoDate", "url", "tags", "sectorType", "scope", "signals", "snippet"]
SECTORS = {"public", "charter", "private"}
SCOPES = {"school", "district"}


def school_ids():
    html = INDEX.read_text(encoding="utf-8")
    start = html.index("const SF_SCHOOLS = [")
    block = html[start:html.index("\n    ];", start)]
    # top-level school objects are indented 8 spaces: `        id: "presidio",`
    return set(re.findall(r'^\s{8}id: "([a-z0-9_]+)"', block, flags=re.M))


def norm_url(u):
    u = (u or "").lower()
    u = re.sub(r"^https?://(www\.)?", "", u)
    u = re.sub(r"[?#].*$", "", u)
    return u.rstrip("/")


def norm_title(t):
    return re.sub(r"[^a-z0-9]+", " ", (t or "").lower()).strip()


def main():
    errors, warnings = [], []
    try:
        articles = json.loads(NEWS.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: data/news.json is not valid JSON: {e}")
        return 1
    if not isinstance(articles, list):
        print("ERROR: data/news.json must be a JSON array")
        return 1

    valid_ids = school_ids()
    if len(valid_ids) < 40:
        errors.append(f"Only found {len(valid_ids)} school ids in index.html — parser may be broken")

    today = dt.date.today()
    seen_ids, seen_urls, seen_titles = set(), {}, {}

    for i, a in enumerate(articles):
        tag = a.get("id", f"#{i}")
        for k in REQUIRED:
            if k not in a:
                errors.append(f"{tag}: missing field '{k}'")
        if a.get("sectorType") not in SECTORS:
            errors.append(f"{tag}: sectorType must be one of {sorted(SECTORS)}")
        if a.get("scope") not in SCOPES:
            errors.append(f"{tag}: scope must be one of {sorted(SCOPES)}")

        try:
            d = dt.date.fromisoformat(a.get("isoDate", ""))
            if d > today:
                errors.append(f"{tag}: isoDate {d} is in the future")
        except ValueError:
            errors.append(f"{tag}: isoDate '{a.get('isoDate')}' is not YYYY-MM-DD")

        if not str(a.get("url", "")).startswith("https://"):
            errors.append(f"{tag}: url must start with https://")

        # school references
        refs = [a.get("schoolId")] + list(a.get("relatedSchoolIds") or [])
        refs += [s.get("schoolId") for s in a.get("signals") or []]
        for sid in filter(None, refs):
            if sid not in valid_ids:
                errors.append(f"{tag}: unknown school id '{sid}'")

        # signals
        sigs = a.get("signals") or []
        if a.get("scope") == "school" and not sigs:
            errors.append(f"{tag}: school-scoped article needs at least one signal")
        if a.get("scope") == "district" and sigs:
            errors.append(f"{tag}: district-scoped article must have no signals")
        for s in sigs:
            if s.get("sentiment") not in (-1, 0, 1):
                errors.append(f"{tag}: sentiment must be -1, 0 or 1")
            if s.get("strength") not in (0.5, 1):
                errors.append(f"{tag}: strength must be 0.5 or 1")
            if not s.get("note"):
                warnings.append(f"{tag}: signal for {s.get('schoolId')} has no note")

        # duplicates
        if tag in seen_ids:
            errors.append(f"duplicate id '{tag}'")
        seen_ids.add(tag)
        urls = [a.get("url")] + [r.get("url") for r in a.get("relatedCoverage") or []]
        for u in urls:
            n = norm_url(u)
            if n in seen_urls:
                errors.append(f"{tag}: URL already used by {seen_urls[n]} → {u}")
            seen_urls[n] = tag
        t = norm_title(a.get("title"))
        if t in seen_titles:
            errors.append(f"{tag}: headline duplicates {seen_titles[t]}")
        seen_titles[t] = tag

    # same storyId may appear twice only if intentional; flag for review
    stories = {}
    for a in articles:
        stories.setdefault(a.get("storyId"), []).append(a.get("id"))
    for sid, ids in stories.items():
        if len(ids) > 1:
            warnings.append(f"storyId '{sid}' used by {ids} — Momentum counts it once (most recent)")

    for w in warnings:
        print("WARN:", w)
    for e in errors:
        print("ERROR:", e)
    print(f"{len(articles)} articles checked — {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
