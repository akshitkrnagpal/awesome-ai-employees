# Data

`companies.csv` is the source of truth for the list.

Generated files:

- `../README.md` listing sections
- `companies.json`

Update flow:

1. Edit `companies.csv`.
2. Run `make generate`.
3. Run `make check`.
4. Commit the CSV and generated files together.

README company names optionally include icons from `../assets/company-icons/manifest.json`.
Run `make icons` to refresh the cached images and regenerate the README, or `make generate`
to reuse the existing cache without network access. Companies without a usable cached icon
are rendered as plain-text names. The CSV schema and JSON company data do not include icon fields.

## CSV Schema

| Field | Required | Description |
|---|---:|---|
| `rank` | Yes | Stable numeric ordering used in README tables. |
| `category` | Yes | README category heading. Rows with the same category are grouped together. |
| `company` | Yes | Company or product name. |
| `ai_employee_angle` | Yes | Short factual description of the recurring job or workflow. |
| `link` | Yes | Public evidence URL for the listing. |

## Validation Rules

`make check` enforces:

- Required headers are present in the expected order.
- Every required field is filled.
- Ranks are unique, contiguous, and sorted from `1` to the number of rows.
- Company names are unique, case-insensitively.
- Each category appears in one contiguous block.
- Links are absolute `http` or `https` URLs.
- Links do not include common tracking or affiliate query parameters.
