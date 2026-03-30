# CSV Cleaner CLI (Invisible Errors + Business Logic)

Implement a Python CLI tool `cleaner.py` to clean one CSV table.

## CLI Contract
Your program must accept only one invocation mode:

1. Positional mode only:
```bash
python cleaner.py <input_csv> <output_csv>
```

## Input Schema
Use this exact header:

`user_id,name,email,age,signup_date,status,score,notes`

## Hard Rules
1. **Primary Key Validation**
   - `user_id` must be a non-empty positive integer.
   - Drop rows with empty `user_id` or non-numeric `user_id` (for example `abc`).

2. **Row Structure Validation**
   - Each data row must have exactly 8 columns.
   - Drop rows with fewer or extra columns.

3. **Type & Range**
   - `age` must be an integer in `[0, 120]`.
   - If `age` is out of range or cannot be converted (for example `notanumber`, `N/A`, empty), drop the entire row.

4. **String Normalization**
   - `email` must be trimmed and lowercased.
   - If `email` is not a basic valid format (must contain `@` and at least one `.` after `@`), drop the entire row.

5. **Invisible Errors**
   - For text fields `name` and `status`, remove leading/trailing invisible characters:
     - spaces
     - tabs (`\t`)
     - zero-width spaces
     - zero-width joiners (`\u200d`)
     - BOM (`\ufeff`)

6. **Complex Deduplication (Business Logic)**
   - Deduplicate by `user_id`.
   - For duplicate `user_id`, keep the record with the latest **valid** `signup_date`.
   - If `signup_date` ties, keep the one with higher numeric `score`. Treat invalid or empty scores as `0` during this comparison.
   - If still tied, keep the first one in input order.
   - Date parsing must support:
     - `YYYY-MM-DD`
     - `YYYY/MM/DD`
     - `MM/DD/YYYY`
     - `DD/MM/YYYY`
     - `MM-DD-YYYY`
     - `YYYY.MM.DD`
     - ISO datetime (truncate to date before parsing)
   - Ambiguous slash dates (for example `03/04/2024`) must be parsed with this priority:
     - `MM/DD/YYYY` first, then `DD/MM/YYYY`.
   - Invalid dates are allowed to exist but must lose against valid dates in dedup comparison.

7. **Output Format**
   - The output CSV must keep the exact same header:
     - `user_id,name,email,age,signup_date,status,score,notes`
   - `signup_date` must be output in strict `YYYY-MM-DD` format when valid, otherwise output an empty string.
   - `email`, `name`, and `status` must be output in their cleaned forms.
     - `email`: trimmed + lowercased
     - `name`: trimmed (including zero-width/tab/space edges removed)
     - `status`: trimmed + lowercased
   - `score` output rule:
     - keep a trimmed numeric string when score is numeric
     - output `0` when score is invalid or empty
   - Final output rows must be sorted by numeric `user_id` ascending.

## Additional Notes
- Use Python standard library (`csv`) to parse/write files.
- The dirty dataset contains quoted fields with commas and line breaks.
- Do not parse CSV using `split(',')`.
- All file read/write operations MUST use `utf-8` encoding.
