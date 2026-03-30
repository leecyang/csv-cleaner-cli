#!/usr/bin/env python3
"""CSV 清洗命令行工具标准答案。"""

import argparse
import csv
import io
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Dict, List

ALLOWED_STATUS = {"active", "inactive", "pending"}
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
HEADER_ALIASES = {
    "user_id": "user_id",
    "userid": "user_id",
    "user": "user_id",
    "name": "name",
    "full_name": "name",
    "username": "name",
    "email": "email",
    "e_mail": "email",
    "email_address": "email",
    "mail": "email",
    "age": "age",
    "signup_date": "signup_date",
    "signup": "signup_date",
    "register_date": "signup_date",
    "created_at": "signup_date",
    "status": "status",
    "state": "status",
    "score": "score",
    "rating": "score",
    "notes": "notes",
    "note": "notes",
    "comment": "notes",
}
STATUS_ALIASES = {
    "active": "active",
    "enabled": "active",
    "open": "active",
    "inactive": "inactive",
    "disabled": "inactive",
    "closed": "inactive",
    "pending": "pending",
    "processing": "pending",
    "review": "pending",
}
MISSING_TOKENS = {
    "",
    "null",
    "none",
    "n/a",
    "na",
    "nan",
    "unknown",
    "error",
    "?",
    "-",
    "--",
    "nil",
}
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="清洗 CSV 数据")
    parser.add_argument("--input", required=True, help="输入 CSV 路径")
    parser.add_argument("--output", required=True, help="输出 CSV 路径")
    return parser.parse_args()


def normalize_text(value: str) -> str:
    cleaned = value.replace("\ufeff", "").replace("\x00", "")
    return cleaned.strip()


def normalize_name(name: str) -> str:
    raw = " ".join(normalize_text(name).split())
    if raw.lower() in MISSING_TOKENS:
        return "Unknown"
    if not raw:
        return "Unknown"
    return raw.title()


def normalize_email(email: str) -> str:
    value = normalize_text(email).lower()
    if value in MISSING_TOKENS:
        return ""
    if value.startswith("mailto:"):
        value = value[7:]
    if value.startswith("<") and value.endswith(">") and len(value) > 2:
        value = value[1:-1].strip()
    if not EMAIL_PATTERN.match(value):
        return ""
    return value


def normalize_age(age: str) -> str:
    value = normalize_text(age)
    if value.lower() in MISSING_TOKENS:
        return ""
    if not value:
        return ""
    value = re.sub(r"\s*years?$", "", value, flags=re.IGNORECASE).strip()
    try:
        if "." in value:
            parsed_decimal = Decimal(value)
            if parsed_decimal != parsed_decimal.to_integral_value():
                return ""
            parsed = int(parsed_decimal)
        else:
            parsed = int(value)
    except (ValueError, InvalidOperation):
        return ""
    if 0 <= parsed <= 120:
        return str(parsed)
    return ""


def parse_date_value(value: str):
    text = normalize_text(value)
    if text.lower() in MISSING_TOKENS:
        return "", None
    if not text:
        return "", None

    normalized = text
    if "T" in normalized:
        normalized = normalized.split("T", 1)[0]
    elif " " in normalized:
        normalized = normalized.split(" ", 1)[0]

    formats = ["%Y-%m-%d", "%d/%m/%Y", "%m-%d-%Y", "%Y/%m/%d", "%Y.%m.%d"]
    for fmt in formats:
        try:
            parsed = datetime.strptime(normalized, fmt).date()
            return parsed.isoformat(), parsed
        except ValueError:
            continue
    return "", None


def normalize_status(status: str) -> str:
    value = normalize_text(status).lower()
    if value in MISSING_TOKENS:
        return "inactive"
    mapped = STATUS_ALIASES.get(value, "")
    if mapped in ALLOWED_STATUS:
        return mapped
    return "inactive"


def normalize_score(score: str):
    value = normalize_text(score)
    if value.lower() in MISSING_TOKENS:
        return "", None
    if not value:
        return "", None
    value = re.sub(r"^[\$¥￥€£]\s*", "", value)
    value = value.replace(" ", "")
    value = value.replace(",", "")
    if value.endswith("%"):
        value = value[:-1].strip()

    try:
        number = Decimal(value)
    except InvalidOperation:
        return "", None

    if number.is_nan() or number.is_infinite():
        return "", None

    if number < 0 or number > 100:
        return "", None

    rounded = number.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{rounded:.2f}", rounded


def normalize_row(row: dict):
    user_id_text = normalize_text(row.get("user_id", ""))
    try:
        user_id = int(user_id_text)
    except ValueError:
        return None

    if user_id <= 0:
        return None

    email = normalize_email(row.get("email", ""))
    if not email:
        return None

    signup_date_text, signup_date_obj = parse_date_value(row.get("signup_date", ""))
    score_text, score_value = normalize_score(row.get("score", ""))

    cleaned = {
        "user_id": str(user_id),
        "name": normalize_name(row.get("name", "")),
        "email": email,
        "age": normalize_age(row.get("age", "")),
        "signup_date": signup_date_text,
        "status": normalize_status(row.get("status", "")),
        "score": score_text,
        "notes": normalize_text(row.get("notes", "")),
    }

    return {
        "cleaned": cleaned,
        "signup_date_obj": signup_date_obj,
        "score_value": score_value,
        "order": None,
    }


def is_better(new_record: dict, old_record: dict) -> bool:
    new_date = new_record["signup_date_obj"]
    old_date = old_record["signup_date_obj"]

    if new_date and old_date:
        if new_date != old_date:
            return new_date > old_date
    elif new_date and not old_date:
        return True
    elif old_date and not new_date:
        return False

    new_score = new_record["score_value"]
    old_score = old_record["score_value"]

    if new_score is not None and old_score is not None:
        if new_score != old_score:
            return new_score > old_score
    elif new_score is not None and old_score is None:
        return True
    elif old_score is not None and new_score is None:
        return False

    return False


def open_csv_text(input_path: str) -> io.StringIO:
    raw = Path(input_path).read_bytes().replace(b"\x00", b"")
    for encoding in ("utf-8-sig", "gb18030", "latin-1"):
        try:
            text = raw.decode(encoding)
            return io.StringIO(text)
        except UnicodeDecodeError:
            continue
    return io.StringIO(raw.decode("utf-8", errors="replace"))


def normalize_header(cell: str) -> str:
    text = normalize_text(cell).lower()
    text = re.sub(r"[\s\-]+", "_", text)
    return HEADER_ALIASES.get(text, text)


def looks_like_header_row(row: List[str]) -> bool:
    probe = [normalize_header(v) for v in row[: len(FIELDNAMES)]]
    return probe == FIELDNAMES


def row_to_dict(headers: List[str], row: List[str]) -> Dict[str, str]:
    values = [v if v is not None else "" for v in row]
    if len(values) < len(headers):
        values.extend([""] * (len(headers) - len(values)))

    extras = []
    if len(values) > len(headers):
        extras = values[len(headers) :]
        values = values[: len(headers)]

    row_dict = {header: value for header, value in zip(headers, values)}

    if extras:
        extra_text = " | ".join(normalize_text(v) for v in extras if normalize_text(v))
        if extra_text:
            base_notes = normalize_text(row_dict.get("notes", ""))
            row_dict["notes"] = f"{base_notes} | {extra_text}" if base_notes else extra_text

    return row_dict


def clean_csv(input_path: str, output_path: str) -> None:
    dedup = {}

    with open_csv_text(input_path) as f:
        reader = csv.reader(f, skipinitialspace=True)
        header = None

        for raw_header in reader:
            if not raw_header:
                continue
            if all(not normalize_text(col) for col in raw_header):
                continue
            header = [normalize_header(h) for h in raw_header]
            break

        if header is None:
            raise ValueError("输入 CSV 缺少表头")

        for index, raw_row in enumerate(reader):
            if raw_row is None:
                continue

            if not raw_row:
                continue

            if all(normalize_text(value) == "" for value in raw_row):
                continue

            # 有些脏文件会把表头重复插入数据区，直接跳过
            if looks_like_header_row(raw_row):
                continue

            normalized_row = row_to_dict(header, raw_row)
            record = normalize_row(normalized_row)
            if record is None:
                continue

            record["order"] = index
            user_id = int(record["cleaned"]["user_id"])
            existing = dedup.get(user_id)
            if existing is None or is_better(record, existing):
                dedup[user_id] = record

    cleaned_rows = [dedup[key]["cleaned"] for key in sorted(dedup.keys())]

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(cleaned_rows)


def main() -> None:
    args = parse_args()
    clean_csv(args.input, args.output)


if __name__ == "__main__":
    main()
