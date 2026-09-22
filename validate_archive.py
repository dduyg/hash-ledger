"""
-漫~*'¨¯¨'*·舞~ ꪜꪖꪶⅈᦔꪖ𝕥ꫀ_ꪖ𝕣ᥴꫝⅈꪜꫀ.ρꪗ

Checks hash_archive.csv for integrity:
- correct header/schema
- no duplicate hash values
- each hash matches its declared length and charset
- status values are one of the allowed options

Exits with a non-zero status (failing the CI run) if any check fails.
"""

import csv
import sys
from pathlib import Path

ARCHIVE_FILE = Path("hash_archive.csv")
EXPECTED_FIELDS = ["hash", "created_at", "length", "charset", "status", "label", "notes"]
ALLOWED_STATUS = {"active", "retired"}

CHARSETS = {
    "hex": set("0123456789abcdef"),
    "base36": set("0123456789abcdefghijklmnopqrstuvwxyz"),
    "base62": set("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"),
}


def main():
    if not ARCHIVE_FILE.exists():
        print(f"No {ARCHIVE_FILE} found — nothing to validate.")
        return

    errors = []
    seen = set()

    with ARCHIVE_FILE.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        if reader.fieldnames != EXPECTED_FIELDS:
            errors.append(
                f"Header mismatch.\n  Expected: {EXPECTED_FIELDS}\n  Found:    {reader.fieldnames}"
            )
            print("\n".join(errors))
            sys.exit(1)

        for i, row in enumerate(reader, start=2):  # row 1 is the header
            h = row.get("hash", "")
            charset_name = row.get("charset", "")
            length_str = row.get("length", "")
            status = row.get("status", "")

            if not h:
                errors.append(f"Row {i}: empty hash value.")
                continue

            if h in seen:
                errors.append(f"Row {i}: duplicate hash '{h}'.")
            seen.add(h)

            if charset_name not in CHARSETS:
                errors.append(f"Row {i}: unknown charset '{charset_name}' for hash '{h}'.")
                continue

            try:
                length = int(length_str)
            except ValueError:
                errors.append(f"Row {i}: invalid length '{length_str}' for hash '{h}'.")
                continue

            if len(h) != length:
                errors.append(f"Row {i}: hash '{h}' length {len(h)} does not match declared length {length}.")

            allowed_chars = CHARSETS[charset_name]
            if not set(h).issubset(allowed_chars):
                errors.append(f"Row {i}: hash '{h}' contains characters outside charset '{charset_name}'.")

            if status not in ALLOWED_STATUS:
                errors.append(f"Row {i}: invalid status '{status}' for hash '{h}' (expected one of {ALLOWED_STATUS}).")

    if errors:
        print(f"Archive validation failed with {len(errors)} issue(s):\n")
        print("\n".join(f"- {e}" for e in errors))
        sys.exit(1)

    print(f"Archive validation passed. {len(seen)} unique hash(es) checked.")


if __name__ == "__main__":
    main()
