#!/usr/bin/env python3
"""Reference solution for the CSV cleaner benchmark."""

import argparse
import csv
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

FIELDNAMES = [
    "user_id",
    "name",
    "email",
    "age",
    "signup_date",
    "status",
    "score",
    "notes",
]

# Ambiguous slash dates must prioritize MM/DD/YYYY over DD/MM/YYYY.
DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%m/%d/%Y",
    "%d/%m/%Y",
    "%m-%d-%Y",
    "%Y.%m.%d",
)
EDGE_INVISIBLE_RE = re.compile(r"^[\s\u200b\u200d\ufeff]+|[\s\u200b\u200d\ufeff]+$")


def strip_invisible(text: str) -> str:
    if text is None:
        return ""
    return EDGE_INVISIBLE_RE.sub("", text.replace("\x00", ""))


def parse_args() -> Tuple[str, str]:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_csv")
    parser.add_argument("output_csv")
    args = parser.parse_args()
    return args.input_csv, args.output_csv


def normalize_email(email: str) -> Optional[str]:
    value = strip_invisible(email).lower()
    if "@" not in value:
        return None
    local, _, domain = value.partition("@")
    if not local or "." not in domain:
        return None
    return value


def normalize_age(age_text: str) -> Optional[str]:
    value = strip_invisible(age_text)
    if not value:
        return None
    try:
        age = int(value)
    except ValueError:
        return None
    if age < 0 or age > 120:
        return None
    return str(age)


def normalize_user_id(raw: str) -> Optional[str]:
    value = strip_invisible(raw)
    if not value.isdigit():
        return None
    number = int(value)
    if number <= 0:
        return None
    return str(number)


def parse_signup_date(raw: str) -> Tuple[str, Optional[date]]:
    value = strip_invisible(raw)
    if not value:
        return "", None

    if "T" in value:
        value = value.split("T", 1)[0]
    elif " " in value:
        value = value.split(" ", 1)[0]

    for fmt in DATE_FORMATS:
        try:
            parsed = datetime.strptime(value, fmt).date()
            return parsed.isoformat(), parsed
        except ValueError:
            continue
    return "", None


def parse_score(raw: str) -> Tuple[float, str]:
    value = strip_invisible(raw)
    if not value:
        return 0.0, "0"
    try:
        number = float(value)
    except ValueError:
        return 0.0, "0"
    return number, value


def is_better(new_record: Dict[str, object], old_record: Dict[str, object]) -> bool:
    new_date = new_record["signup_date_obj"]
    old_date = old_record["signup_date_obj"]

    if new_date and old_date:
        if new_date != old_date:
            return bool(new_date > old_date)
    elif new_date and not old_date:
        return True
    elif old_date and not new_date:
        return False

    new_score = new_record["score_value"]
    old_score = old_record["score_value"]
    if new_score != old_score:
        return bool(new_score > old_score)
    return False


def clean_csv(input_csv: str, output_csv: str) -> None:
    dedup: Dict[str, Dict[str, object]] = {}
    input_path = Path(input_csv)
    output_path = Path(output_csv)

    with input_path.open("r", encoding="utf-8", newline="") as src:
        reader = csv.reader(src)
        try:
            raw_header = next(reader)
        except StopIteration:
            raw_header = []

        normalized_header = [strip_invisible(c).lower() for c in raw_header]
        if normalized_header != FIELDNAMES:
            raise ValueError("input header does not match required schema")

        for raw_row in reader:
            if len(raw_row) != len(FIELDNAMES):
                continue
            if all(strip_invisible(cell) == "" for cell in raw_row):
                continue

            row = dict(zip(FIELDNAMES, raw_row))
            user_id = normalize_user_id(row["user_id"])
            if user_id is None:
                continue

            email = normalize_email(row["email"])
            if email is None:
                continue

            age = normalize_age(row["age"])
            if age is None:
                continue

            score_value, score_text = parse_score(row["score"])
            signup_date_text, signup_date_obj = parse_signup_date(row["signup_date"])
            cleaned = {
                "user_id": user_id,
                "name": strip_invisible(row["name"]),
                "email": email,
                "age": age,
                "signup_date": signup_date_text,
                "status": strip_invisible(row["status"]).lower(),
                "score": score_text,
                "notes": row["notes"],
            }
            candidate = {
                "row": cleaned,
                "signup_date_obj": signup_date_obj,
                "score_value": score_value,
            }

            previous = dedup.get(user_id)
            if previous is None or is_better(candidate, previous):
                dedup[user_id] = candidate

    def sort_key(item: Tuple[str, Dict[str, object]]) -> Tuple[int, str]:
        key = item[0]
        return int(key), key

    ordered_rows: List[Dict[str, str]] = [record["row"] for _, record in sorted(dedup.items(), key=sort_key)]
    with output_path.open("w", encoding="utf-8", newline="") as dst:
        writer = csv.DictWriter(dst, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(ordered_rows)


def main() -> None:
    input_csv, output_csv = parse_args()
    clean_csv(input_csv, output_csv)


if __name__ == "__main__":
    main()
