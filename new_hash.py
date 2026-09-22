"""
 ❖︎♋︎●︎♓︎♎︎♋︎⧫︎ 🕊 ⋆ 🐚 𝒏𝒆𝒘_𝒉𝒂𝒔𝒉.𝒑𝒚

Generates unique random hashes and logs them to a CSV archive so a
hash is never generated twice. Supports multiple charsets and
lengths, an ambiguous-character filter, optional prefixes/labels,
and an optional reserved/blocklist file.

Usage:
    python3 new_hash.py
    python3 new_hash.py --count 5
    python3 new_hash.py --length 6 --charset base36
    python3 new_hash.py --charset base62 --strict
    python3 new_hash.py --prefix usr --label "namedrop"
    python3 new_hash.py --archive hash_archive.csv --reserved reserved.csv

Archive schema (hash_archive.csv):
    hash,created_at,length,charset,status,label,notes
    9c8b,2026-09-22T14:03:11Z,4,hex,active,,
"""

import argparse
import csv
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

ARCHIVE_FILE = Path("hash_archive.csv")
RESERVED_FILE = Path("reserved.csv")
FIELDNAMES = ["hash", "created_at", "length", "charset", "status", "label", "notes"]

CHARSETS = {
    "hex": "0123456789abcdef",
    "base36": "0123456789abcdefghijklmnopqrstuvwxyz",
    "base62": "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
}

# Visually ambiguous characters, excluded when --strict is set and the
# charset contains letters (hex has no letters worth filtering).
AMBIGUOUS = set("0O1lI")


def get_charset(name: str, strict: bool) -> str:
    if name not in CHARSETS:
        raise ValueError(f"Unknown charset '{name}'. Choose from: {', '.join(CHARSETS)}")
    chars = CHARSETS[name]
    if strict and name != "hex":
        chars = "".join(c for c in chars if c not in AMBIGUOUS)
    return chars


def load_existing_hashes(archive_file: Path) -> set:
    if not archive_file.exists():
        return set()
    with archive_file.open(newline="", encoding="utf-8") as f:
        return {row["hash"] for row in csv.DictReader(f) if row.get("hash")}


def load_reserved(reserved_file: Path) -> set:
    if not reserved_file.exists():
        return set()
    with reserved_file.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if "hash" not in (reader.fieldnames or []):
            return set()
        return {row["hash"] for row in reader if row.get("hash")}


def generate_hash(existing: set, blocked: set, charset: str, length: int) -> str:
    while True:
        h = "".join(secrets.choice(charset) for _ in range(length))
        if h not in existing and h not in blocked:
            return h


def append_rows(archive_file: Path, rows: list) -> None:
    file_exists = archive_file.exists()
    with archive_file.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(description="Generate and archive unique hashes.")
    parser.add_argument("--count", type=int, default=1, help="How many hashes to generate (default: 1)")
    parser.add_argument("--length", type=int, default=4, help="Hash length in characters (default: 4)")
    parser.add_argument(
        "--charset",
        default="hex",
        choices=list(CHARSETS),
        help="Character set: hex, base36, or base62 (default: hex)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exclude visually ambiguous characters (0/O, 1/l/I) for base36/base62",
    )
    parser.add_argument("--prefix", default="", help="Optional prefix printed with the hash, e.g. usr-9c8b")
    parser.add_argument("--label", default="", help="Optional label stored alongside the hash (e.g. project name)")
    parser.add_argument("--notes", default="", help="Optional freeform notes stored alongside the hash")
    parser.add_argument("--archive", default=str(ARCHIVE_FILE), help="Path to the archive CSV file")
    parser.add_argument("--reserved", default=str(RESERVED_FILE), help="Path to a reserved/blocklist CSV file")
    args = parser.parse_args()

    if args.length < 1:
        print("Length must be at least 1.", file=sys.stderr)
        sys.exit(1)

    archive_file = Path(args.archive)
    reserved_file = Path(args.reserved)

    try:
        charset = get_charset(args.charset, args.strict)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    existing = load_existing_hashes(archive_file)
    blocked = load_reserved(reserved_file)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    new_rows = []
    for _ in range(args.count):
        h = generate_hash(existing, blocked, charset, args.length)
        existing.add(h)
        new_rows.append(
            {
                "hash": h,
                "created_at": now,
                "length": args.length,
                "charset": args.charset,
                "status": "active",
                "label": args.label,
                "notes": args.notes,
            }
        )

    append_rows(archive_file, new_rows)

    for row in new_rows:
        display = f"{args.prefix}-{row['hash']}" if args.prefix else row["hash"]
        print(display)

    print(f"\nLogged {len(new_rows)} hash(es) to: {archive_file.resolve()}", file=sys.stderr)


if __name__ == "__main__":
    main()
