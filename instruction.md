# CSV Cleaner CLI Task

Build a Python command-line tool named `cleaner.py` that cleans a messy CSV file.

## Input and Output
- Input file: `environment/dirty_data.csv`
- Output file: any path provided by CLI argument (for example `cleaned_data.csv`)

Your program must support:

```bash
python cleaner.py --input <input_csv_path> --output <output_csv_path>
```

## Required Cleaning Rules
1. Skip blank rows.
2. Trim leading/trailing spaces for every field.
3. Keep and normalize this exact header order:
   - `user_id,name,email,age,signup_date,status,score,notes`
4. `user_id` must be a positive integer. Drop row if invalid.
5. `name`:
   - Collapse repeated internal spaces into one.
   - Convert to title case.
   - If empty, use `Unknown`.
6. `email`:
   - Convert to lowercase.
   - Must be in a valid basic email format (contains one `@`, valid domain with dot).
   - Drop row if invalid.
7. `age`:
   - Keep integer if it is in `[0, 120]`.
   - Otherwise write empty string.
8. `signup_date`:
   - Accept these input formats: `YYYY-MM-DD`, `DD/MM/YYYY`, `MM-DD-YYYY`, `YYYY/MM/DD`, `YYYY.MM.DD`.
   - If the value includes time part (for example `YYYY-MM-DDTHH:MM:SSZ`), use only the date part.
   - Convert valid dates to `YYYY-MM-DD`.
   - Invalid date becomes empty string.
9. `status`:
   - Case-insensitive allowed values: `active`, `inactive`, `pending`.
   - Also normalize aliases: `enabled -> active`, `disabled -> inactive`, `closed -> inactive`, `processing -> pending`, `review -> pending`.
   - Any other value becomes `inactive`.
10. `score`:
    - Keep numeric values in `[0, 100]`.
    - Accept optional `%` suffix (for example `88%`) and treat it as numeric value `88`.
    - Accept thousands separators (for example `1,234.56`) before numeric validation.
    - Round to 2 decimal places.
    - Invalid value becomes empty string.
11. Deduplicate by `user_id`:
    - Keep the row with the latest valid `signup_date`.
    - If dates tie, keep the one with higher numeric `score`.
    - If still tied, keep the first encountered row.
12. Final output must be sorted by `user_id` ascending.
13. Robustness rules for messy files:
    - Rows with fewer columns should be treated as missing trailing fields.
    - Rows with extra columns should append extras into `notes` (joined with ` | `).
    - Repeated header rows inside data must be ignored.
    - Unexpected null bytes (`\x00`) should not crash the parser.
    - `email` may contain wrappers such as `mailto:` prefix or angle brackets (`<user@example.com>`), and should still be normalized if valid.
    - `age` can be an integer-like decimal string (for example `30.0`) and should be normalized to integer if valid.

## Notes
- Use Python standard library only.
- The program must work in Linux.
