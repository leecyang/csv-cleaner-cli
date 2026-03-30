#!/usr/bin/env python3
"""Logic-level verifier for cleaned_data.csv."""

import csv
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

EXPECTED_HEADERS = [
    "user_id",
    "name",
    "email",
    "age",
    "signup_date",
    "status",
    "score",
    "notes",
]
EXPECTED_ROW_COUNT = 17
DROPPED_IDS = {"0", "-1", "2", "3", "4", "11", "12", "13", "17", "19", "24", "25"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def fail(message: str) -> None:
    print(message)
    sys.exit(1)


def strip_invisible_edges(value: str) -> str:
    return value.strip(" \t\u200b\u200d\ufeff")


def load_rows(path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        rows = list(reader)
    return headers, rows


def main() -> int:
    output_path = Path("cleaned_data.csv")

    # Step 1: hard guard requested by spec.
    if not output_path.exists():
        fail("Error: cleaned_data.csv was not generated")

    headers, rows = load_rows(output_path)
    if headers != EXPECTED_HEADERS:
        fail(f"Error: Header mismatch. Expected {EXPECTED_HEADERS}, got {headers}")

    if len(rows) != EXPECTED_ROW_COUNT:
        fail(f"Error: Row count mismatch. Expected {EXPECTED_ROW_COUNT}, got {len(rows)}")

    by_id: Dict[str, Dict[str, str]] = {}
    user_id_order: List[int] = []
    for row in rows:
        user_id = row.get("user_id", "")
        if user_id in by_id:
            fail(f"Error: Duplicate user_id remains after dedup: {user_id}")
        if not user_id.isdigit():
            fail(f"Error: user_id is not a positive integer in output: {user_id}")
        user_id_order.append(int(user_id))
        by_id[user_id] = row

    if user_id_order != sorted(user_id_order):
        fail("Error: Output rows are not sorted by numeric user_id ascending")

    for dropped_id in DROPPED_IDS:
        if dropped_id in by_id:
            fail(f"Error: Invalid row was not dropped, user_id={dropped_id}")
    if "abc" in by_id:
        fail("Error: Non-numeric user_id=abc should be dropped")
    if "" in by_id:
        fail("Error: Empty user_id should be dropped")

    for user_id, row in by_id.items():
        email = row["email"]
        if email != email.strip().lower():
            fail(f"Error: Email is not lowercased/trimmed for user_id={user_id}")
        if "@" not in email or "." not in email.split("@", 1)[1]:
            fail(f"Error: Email format is invalid for user_id={user_id}")

        age_text = row["age"]
        if not age_text.isdigit():
            fail(f"Error: Age is not integer for user_id={user_id}: {age_text}")
        age_value = int(age_text)
        if not (0 <= age_value <= 120):
            fail(f"Error: Age out of range for user_id={user_id}: {age_value}")

        for field in ("name", "status"):
            if row[field] != strip_invisible_edges(row[field]):
                fail(f"Error: Invisible edge chars not removed in {field} for user_id={user_id}")
        if row["status"] != row["status"].lower():
            fail(f"Error: status is not lowercased for user_id={user_id}")
        if row["signup_date"] and not DATE_RE.match(row["signup_date"]):
            fail(f"Error: signup_date is not in strict YYYY-MM-DD for user_id={user_id}: {row['signup_date']}")

    row1 = by_id.get("1")
    if row1 is None:
        fail("Error: Missing expected user_id=1")
    if row1["email"] != "alice@example.com":
        fail("Error: user_id=1 email normalization is incorrect")
    if row1["name"] != "Alice":
        fail(f"Error: user_id=1 name trimming failed, got '{row1['name']}'")
    if row1["status"] != "active":
        fail(f"Error: user_id=1 status trimming failed, got '{row1['status']}'")

    row7 = by_id.get("7")
    if row7 is None:
        fail("Error: Missing expected user_id=7")
    if row7["email"] != "seven.new@example.com":
        fail("Error: Dedup failed for user_id=7 (latest valid date row not kept)")
    if row7["signup_date"] != "2024-02-28":
        fail("Error: user_id=7 signup_date normalization/dedup is incorrect")

    row9 = by_id.get("9")
    if row9 is None:
        fail("Error: Missing expected user_id=9")
    if row9["email"] != "nine.high@example.com":
        fail("Error: Dedup tie-break by score failed for user_id=9")
    if row9["score"] != "2":
        fail("Error: user_id=9 expected higher score row")

    row10 = by_id.get("10")
    if row10 is None:
        fail("Error: Missing expected user_id=10")
    if "\n" not in row10["notes"] or "," not in row10["notes"]:
        fail("Error: CSV quoted multiline/comma notes were not preserved for user_id=10")

    row15 = by_id.get("15")
    if row15 is None:
        fail("Error: Missing expected user_id=15")
    if row15["name"] != "Dave":
        fail("Error: Zero-width spaces were not trimmed for user_id=15")

    row16 = by_id.get("16")
    if row16 is None:
        fail("Error: Missing expected user_id=16")
    if row16["signup_date"] != "2024-03-11":
        fail("Error: ISO datetime was not truncated/parsing failed for user_id=16")

    row18 = by_id.get("18")
    if row18 is None:
        fail("Error: Missing expected user_id=18")
    if row18["email"] != "order1@example.com":
        fail("Error: Input-order tie-break failed for user_id=18")

    row20 = by_id.get("20")
    if row20 is None:
        fail("Error: Empty/comma-only row handling failed around user_id=20")
    if row20["email"] != "empty@example.com":
        fail("Error: user_id=20 row parse is broken after comma-only line")

    row21 = by_id.get("21")
    if row21 is None:
        fail("Error: Missing expected user_id=21")
    if row21["email"] != "score2@example.com":
        fail("Error: score tie-break with invalid score-as-0 failed for user_id=21")
    if row21["score"] != "10":
        fail("Error: user_id=21 should keep valid score row")

    row22 = by_id.get("22")
    if row22 is None:
        fail("Error: Missing expected user_id=22")
    if row22["email"] != "ambig.second@example.com":
        fail("Error: Ambiguous slash-date priority is incorrect for user_id=22")
    if row22["signup_date"] != "2024-04-03":
        fail("Error: user_id=22 expected latest parsed date 2024-04-03")

    row23 = by_id.get("23")
    if row23 is None:
        fail("Error: Missing expected user_id=23")
    if row23["email"] != "cross.first@example.com":
        fail("Error: Same-day cross-format tie should keep first row for user_id=23")

    row26 = by_id.get("26")
    if row26 is None:
        fail("Error: Missing expected user_id=26")
    if row26["name"] != "Joiner":
        fail("Error: BOM/ZWJ trimming failed for name in user_id=26")
    if row26["status"] != "active":
        fail("Error: BOM/ZWJ trimming or lowercasing failed for status in user_id=26")

    row27 = by_id.get("27")
    if row27 is None:
        fail("Error: Missing expected user_id=27")
    if row27["score"] != "0":
        fail("Error: Invalid score output must be normalized to 0 for user_id=27")

    row28 = by_id.get("28")
    if row28 is None:
        fail("Error: Missing expected user_id=28")
    if row28["score"] != "0":
        fail("Error: Empty score output must be normalized to 0 for user_id=28")

    row29 = by_id.get("29")
    if row29 is None:
        fail("Error: Missing expected user_id=29")
    if row29["email"] != "score.valid.tie@example.com":
        fail("Error: Empty score should be treated as 0 in tie-break for user_id=29")
    if row29["score"] != "5":
        fail("Error: user_id=29 should keep numeric score row")

    print("All logic checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
