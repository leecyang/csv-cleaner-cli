#!/usr/bin/env python3
"""校验 CSV 清洗逻辑的测试脚本。"""

import argparse
import csv
import subprocess
import sys
import tempfile
from pathlib import Path

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
ALLOWED_STATUS = {"active", "inactive", "pending"}

EXPECTED_ROWS = [
    {
        "user_id": "1",
        "name": "Alice B",
        "email": "alice.b@example.com",
        "age": "30",
        "signup_date": "2024-02-01",
        "status": "active",
        "score": "95.20",
        "notes": "duplicate newer",
    },
    {
        "user_id": "3",
        "name": "Unknown",
        "email": "charlie@example.com",
        "age": "",
        "signup_date": "2024-03-20",
        "status": "inactive",
        "score": "77.78",
        "notes": "bad age and status",
    },
    {
        "user_id": "5",
        "name": "Eve",
        "email": "eve@example.com",
        "age": "",
        "signup_date": "2024-05-02",
        "status": "inactive",
        "score": "85.50",
        "notes": "age invalid",
    },
    {
        "user_id": "6",
        "name": "Frank",
        "email": "frank@example.com",
        "age": "28",
        "signup_date": "",
        "status": "active",
        "score": "82.00",
        "notes": "invalid date",
    },
    {
        "user_id": "7",
        "name": "Henry X",
        "email": "henryx@example.com",
        "age": "27",
        "signup_date": "2024-03-01",
        "status": "pending",
        "score": "72.00",
        "notes": "tie date higher score keep this",
    },
    {
        "user_id": "8",
        "name": "Isaac Newton",
        "email": "isaac@example.com",
        "age": "45",
        "signup_date": "2024-01-01",
        "status": "inactive",
        "score": "",
        "notes": "extra spaces",
    },
    {
        "user_id": "9",
        "name": "Jane",
        "email": "jane@example.com",
        "age": "33",
        "signup_date": "",
        "status": "active",
        "score": "90.00",
        "notes": "bad date",
    },
    {
        "user_id": "10",
        "name": "Kate",
        "email": "kate@example.com",
        "age": "25",
        "signup_date": "2024-06-01",
        "status": "inactive",
        "score": "",
        "notes": "bad score",
    },
    {
        "user_id": "11",
        "name": "Mary Jane",
        "email": "mary.jane+vip@example.com",
        "age": "0",
        "signup_date": "2024-07-15",
        "status": "active",
        "score": "100.00",
        "notes": "plus alias email",
    },
    {
        "user_id": "12",
        "name": "Noah",
        "email": "noah@example.com",
        "age": "",
        "signup_date": "2024-07-16",
        "status": "pending",
        "score": "100.00",
        "notes": "tab name and sci score",
    },
    {
        "user_id": "13",
        "name": "Liam",
        "email": "liam@example.com",
        "age": "31",
        "signup_date": "2024-07-01",
        "status": "inactive",
        "score": "",
        "notes": "",
    },
    {
        "user_id": "14",
        "name": "Mia",
        "email": "mia@example.com",
        "age": "22",
        "signup_date": "2024-07-02",
        "status": "active",
        "score": "88.00",
        "notes": "has extra | EXTRA1 | EXTRA2",
    },
    {
        "user_id": "15",
        "name": "Olivia, Smith",
        "email": "olivia@example.com",
        "age": "30",
        "signup_date": "2024-07-20",
        "status": "active",
        "score": "87.46",
        "notes": "quoted, note",
    },
    {
        "user_id": "16",
        "name": "Emma",
        "email": "emma@example.com",
        "age": "29",
        "signup_date": "2024-08-01",
        "status": "inactive",
        "score": "",
        "notes": "nan score",
    },
    {
        "user_id": "17",
        "name": "Jack",
        "email": "jack@example.com",
        "age": "40",
        "signup_date": "",
        "status": "active",
        "score": "75.00",
        "notes": "bad date",
    },
    {
        "user_id": "18",
        "name": "Sam",
        "email": "sam@example.com",
        "age": "30",
        "signup_date": "2024-07-21",
        "status": "active",
        "score": "88.00",
        "notes": "email brackets and iso datetime",
    },
    {
        "user_id": "19",
        "name": "Ava",
        "email": "ava@example.com",
        "age": "32",
        "signup_date": "2024-07-22",
        "status": "pending",
        "score": "1.00",
        "notes": "mailer style email",
    },
    {
        "user_id": "20",
        "name": "Ruby V2",
        "email": "ruby.v2@example.com",
        "age": "26",
        "signup_date": "2024-07-23",
        "status": "inactive",
        "score": "66.67",
        "notes": "duplicate same date higher rounded score",
    },
    {
        "user_id": "21",
        "name": "Leo",
        "email": "leo@example.com",
        "age": "",
        "signup_date": "2024-07-24",
        "status": "active",
        "score": "72.00",
        "notes": "non integer age",
    },
    {
        "user_id": "22",
        "name": "Ella",
        "email": "ella@example.com",
        "age": "20",
        "signup_date": "2024-07-25",
        "status": "active",
        "score": "",
        "notes": "comma score invalid by range",
    },
    {
        "user_id": "23",
        "name": "Nora",
        "email": "nora@example.com",
        "age": "22",
        "signup_date": "2024-07-26",
        "status": "pending",
        "score": "98.00",
        "notes": "review status alias",
    },
    {
        "user_id": "24",
        "name": "Tom New",
        "email": "tom.new@example.com",
        "age": "40",
        "signup_date": "2024-07-27",
        "status": "active",
        "score": "10.00",
        "notes": "newer valid date should win",
    },
    {
        "user_id": "25",
        "name": "Ann",
        "email": "ann@example.com",
        "age": "30",
        "signup_date": "2024-07-20",
        "status": "active",
        "score": "50.00",
        "notes": "latest date should win",
    },
    {
        "user_id": "26",
        "name": "Ben B",
        "email": "benb@example.com",
        "age": "29",
        "signup_date": "2024-07-28",
        "status": "active",
        "score": "0.00",
        "notes": "same date numeric score should win",
    },
    {
        "user_id": "27",
        "name": "Jean-Luc Picard",
        "email": "jean@example.com",
        "age": "59",
        "signup_date": "2024-07-29",
        "status": "active",
        "score": "88.80",
        "notes": "name hyphen and open status",
    },
    {
        "user_id": "28",
        "name": "Luna",
        "email": "luna@example.com",
        "age": "120",
        "signup_date": "2024-07-30",
        "status": "inactive",
        "score": "",
        "notes": "negative score",
    },
    {
        "user_id": "29",
        "name": "Max",
        "email": "max@example.com",
        "age": "",
        "signup_date": "2024-07-31",
        "status": "pending",
        "score": "70.00",
        "notes": "age high",
    },
    {
        "user_id": "30",
        "name": "Ivy",
        "email": "ivy@example.com",
        "age": "18",
        "signup_date": "",
        "status": "inactive",
        "score": "60.00",
        "notes": "invalid day in date",
    },
    {
        "user_id": "31",
        "name": "Unknown",
        "email": "valid31@example.com",
        "age": "44",
        "signup_date": "2024-08-02",
        "status": "active",
        "score": "42.10",
        "notes": "blank name should become unknown",
    },
    {
        "user_id": "32",
        "name": "Kelly",
        "email": "kelly@example.com",
        "age": "30",
        "signup_date": "2024-08-03",
        "status": "pending",
        "score": "100.00",
        "notes": "datetime with space",
    },
    {
        "user_id": "33",
        "name": "Mark",
        "email": "mark@example.com",
        "age": "27",
        "signup_date": "2024-08-04",
        "status": "active",
        "score": "0.10",
        "notes": "tiny scientific score",
    },
    {
        "user_id": "34",
        "name": "Nick",
        "email": "nick@example.com",
        "age": "23",
        "signup_date": "2024-08-05",
        "status": "active",
        "score": "88.00",
        "notes": "TAIL_A | TAIL_B",
    },
    {
        "user_id": "35",
        "name": "Sophia",
        "email": "sophia@example.com",
        "age": "27",
        "signup_date": "2024-08-06",
        "status": "active",
        "score": "89.50",
        "notes": "age with unit",
    },
    {
        "user_id": "36",
        "name": "Ethan",
        "email": "ethan@example.com",
        "age": "",
        "signup_date": "2024-08-07",
        "status": "inactive",
        "score": "",
        "notes": "placeholder tokens",
    },
    {
        "user_id": "37",
        "name": "Olive",
        "email": "olive@example.com",
        "age": "34",
        "signup_date": "2024-08-08",
        "status": "active",
        "score": "91.20",
        "notes": "currency score",
    },
    {
        "user_id": "39",
        "name": "Chloe",
        "email": "chloe@example.com",
        "age": "29",
        "signup_date": "2024-09-08",
        "status": "pending",
        "score": "88.00",
        "notes": "eu date format",
    },
    {
        "user_id": "40",
        "name": "Lucas",
        "email": "lucas@example.com",
        "age": "28",
        "signup_date": "2024-08-10",
        "status": "pending",
        "score": "0.00",
        "notes": "percent zero",
    },
    {
        "user_id": "41",
        "name": "Amelia",
        "email": "amelia@example.com",
        "age": "",
        "signup_date": "2024-08-11",
        "status": "active",
        "score": "100.00",
        "notes": "age missing token",
    },
    {
        "user_id": "42",
        "name": "Harper",
        "email": "harper@example.com",
        "age": "45",
        "signup_date": "2024-08-12",
        "status": "inactive",
        "score": "100.00",
        "notes": "spaced score digits",
    },
    {
        "user_id": "44",
        "name": "Baddate",
        "email": "baddate@example.com",
        "age": "30",
        "signup_date": "",
        "status": "active",
        "score": "77.00",
        "notes": "invalid month",
    },
    {
        "user_id": "45",
        "name": "Duptest New",
        "email": "dup.new@example.com",
        "age": "30",
        "signup_date": "2024-08-15",
        "status": "active",
        "score": "55.00",
        "notes": "newer record should win",
    },
    {
        "user_id": "46",
        "name": "Tiedate High",
        "email": "tie.high@example.com",
        "age": "30",
        "signup_date": "2024-08-16",
        "status": "active",
        "score": "50.10",
        "notes": "tie date high score",
    },
]


def run_cleaner(cleaner_path: Path, input_path: Path, output_path: Path):
    command = [
        sys.executable,
        str(cleaner_path),
        "--input",
        str(input_path),
        "--output",
        str(output_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def read_csv_rows(path: Path):
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        rows = list(reader)
    return headers, rows


def evaluate_cleaner(cleaner_path: Path, dirty_path: Path):
    if not cleaner_path.exists():
        return False, f"未找到 cleaner 脚本: {cleaner_path}"

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_root = Path(tmp_dir)
        output_path = tmp_root / "cleaned.csv"

        code, stdout, stderr = run_cleaner(cleaner_path, dirty_path, output_path)
        if code != 0:
            return (
                False,
                f"cleaner 执行失败，退出码={code}\nstdout:\n{stdout}\nstderr:\n{stderr}",
            )

        if not output_path.exists():
            return False, "cleaner 未生成输出文件"

        headers, rows = read_csv_rows(output_path)
        if headers != EXPECTED_HEADERS:
            return False, f"表头不匹配。期望: {EXPECTED_HEADERS}，实际: {headers}"

        # 基础结构约束：有序、唯一、字段合法
        user_ids = [int(row["user_id"]) for row in rows]
        if user_ids != sorted(user_ids):
            return False, "user_id 未按升序排序"
        if len(user_ids) != len(set(user_ids)):
            return False, "user_id 去重失败，存在重复主键"

        for row in rows:
            if row["status"] not in ALLOWED_STATUS:
                return False, f"status 非法: {row['status']}"
            if row["email"] != row["email"].lower():
                return False, f"email 未转为小写: {row['email']}"
            if "@" not in row["email"]:
                return False, f"email 格式异常: {row['email']}"

        if rows != EXPECTED_ROWS:
            return False, f"清洗结果不匹配。期望 {len(EXPECTED_ROWS)} 行，实际 {len(rows)} 行"

        return True, "校验通过"


def assert_verifier_rejects_bad_solution(dirty_path: Path):
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_root = Path(tmp_dir)
        bad_cleaner = tmp_root / "bad_cleaner.py"
        bad_cleaner.write_text(
            """
import argparse
import shutil

parser = argparse.ArgumentParser()
parser.add_argument('--input', required=True)
parser.add_argument('--output', required=True)
args = parser.parse_args()
shutil.copyfile(args.input, args.output)
            """.strip()
            + "\n",
            encoding="utf-8",
        )

        ok, _ = evaluate_cleaner(bad_cleaner, dirty_path)
        if ok:
            raise AssertionError("验证器未能拦截错误答案（仅复制文件）")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CSV 清洗逻辑测试")
    parser.add_argument("--cleaner", default="solution/cleaner.py", help="待验证 cleaner.py 路径")
    parser.add_argument("--dirty", default="environment/dirty_data.csv", help="脏数据路径")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cleaner_path = Path(args.cleaner)
    dirty_path = Path(args.dirty)

    assert_verifier_rejects_bad_solution(dirty_path)

    ok, message = evaluate_cleaner(cleaner_path, dirty_path)
    if not ok:
        print(message)
        return 1

    print(message)
    return 0


if __name__ == "__main__":
    sys.exit(main())
