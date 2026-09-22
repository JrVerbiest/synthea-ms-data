# Data contract

> This section is still 🚧 **Work in progress**  so the content here may still change.

```text
data-contract/
├── README.md
├── merge.yaml                   What to merge, plus everything written by hand: fundamentals, type corrections, quality rules
├── scripts/
│   ├── build_dictionary.py      Pulls the Synthea CSV data dictionary from the wiki - do not edit the file by hand!
│   └── merge_schemas.py         Merges the per-table contracts, applies the dictionary and the hand-written parts of merge.yaml
├── imports/                     One ODCS contract per CSV file, structure only (datacontract import csv)
│   ├── patients.yaml
│   ├── encounters.yaml
│   ├── conditions.yaml
│   └── observations.yaml
├── outputs/                     Everything merge_schemas.py and build_dictionary.py generate — never edit by hand
│   ├── data-dictionary.yaml     Descriptions, types, keys and foreign keys of all Synthea CSV tables (build_dictionary.py)
│   └── synthea-ms-data.odcs.yaml   The generated data contract (merge_schemas.py)
└── final/                       The final data contract, enriched by hand, and its documentation
    ├── synthea-ms-data.odcs.yaml   Copied from outputs/, then edited by hand
    └── synthea-ms-data.html     HTML documentation of the final contract (datacontract export html)
```

The sections below describe how to reproduce `synthea-ms-data.odcs.yaml` data contract from scratch.

## Generate the data contract from the CSV files

All commands below are run from the **repository root** (`synthea-ms-data/`): the CSV files are read from `data/corrected/`, the per-table contracts land in `data-contract/imports/`.

One table:

```bash
datacontract import csv --source data/corrected/patients.csv --output data-contract/imports/patients.yaml
```

All 13 tables:

```bash
for f in data/corrected/*.csv; do
 datacontract import csv --source "$f" --output "data-contract/imports/$(basename "$f" .csv).yaml"
done
```

Specific tables, for example `patients`, `encounters`, `conditions`, and `observations`:

```bash
for t in patients encounters conditions observations; do
 datacontract import csv --source "data/corrected/$t.csv" --output "data-contract/imports/$t.yaml"
done
```

**REMARK**: A CSV file carries no information about what its columns mean or how tables relate — there are no descriptions and no `PRIMARY KEY` / `FOREIGN KEY` metadata as in a SQL DDL — so the imported contracts have placeholder descriptions (`Generated model of data/corrected/patients.csv`), no keys and no `relationships` between them. **Synthea documents all of that on its wiki**.

## Merge the per-table contracts into one

### 1. Build the data dictionary from the wiki

```bash
python data-contract/scripts/build_dictionary.py
```

The script fetches the [CSV-File-Data-Dictionary.md](https://raw.githubusercontent.com/wiki/synthetichealth/synthea/CSV-File-Data-Dictionary.md), parses the file list and the per-table column tables, and writes `data-contract/outputs/data-dictionary.yaml` covering all 18 CSV files Synthea can export (256 columns). Re-run it whenever the wiki changes; the file records the source URL, the retrieval date and a SHA-256 of the page, so a change shows up in the diff.

Following common data-dictionary practice, each column entry carries more than the description:

```yaml
tables:
  patients:
    file: patients.csv
    description: Patient demographic data.
    columns:
      Id:
        description: Primary Key. Unique Identifier of the patient.
        type: UUID
        required: true
        key: primary
      DEATHDATE:
        description: The date the patient died.
        type: Date
        format: YYYY-MM-DD
        required: false
      # ...
  conditions:
    columns:
      PATIENT:
        description: Foreign key to the Patient.
        type: UUID
        required: true
        key: foreign
        references: patients.Id
```

| Field | Meaning |
|-------|---------|
| `description` | The wiki's description, Markdown and HTML markup removed |
| `type`, `format` | The wiki's *Data Type*, split into type and the format in parentheses (`Date (YYYY-MM-DD)`) |
| `required` | The wiki's *Required?* column — the *contract*, as opposed to the `required` the importer infers from what happened to be filled in one run |
| `key` | `primary` (:key: on the wiki) or `foreign` (:old_key:) |
| `references` | For foreign keys, the referenced `table.Id`, derived from the description text ("Foreign key to the supervising Provider" → `providers.Id`) |

- Column names are those of the CSV headers, not the wiki's: the wiki writes `BirthDate`, `FIPS County Code` and `Patient ID` where the files have `BIRTHDATE`, `FIPS` and `PATIENTID`. 
- Each wiki name is matched to the header of `data/corrected/<table>.csv` ignoring case, spaces and underscores; the handful of columns where the wiki and the exporter genuinely disagree (`immunizations.Cost` → `BASE_COST`, `payer_transitions.Start_Year` → `START_DATE`, …) are listed in `RENAMES` in the script.
- Columns present in the CSV but not on the wiki are reported — currently `NPI` in `organizations` and `providers`.

### 2. Merge

The [`merge.yaml`](merge.yaml) says what to merge and holds everything that is written by hand; the *meaning* of the columns comes from the dictionary. Paths in the YAML are relative to the YAML file, except `server.path`, which `datacontract test` resolves from the directory it is run in. Run the script from the repository root:

> Note: the provided `merge.yaml` shows the merge of the encounter, condition and observation data contracts.

```bash
python data-contract/scripts/merge_schemas.py data-contract/merge.yaml
```

This writes `data-contract/outputs/synthea-ms-data.odcs.yaml`. The script uses only the ODCS model that ships with `datacontract-cli`, so no extra dependency is needed. What it does:

- **Schema** — one `schema` entry per table listed under `tables`, read from `imports/<table>.yaml`, in that order.
- **Fundamentals** — every field under `contract` (`id`, `name`, `domain`, `description`, `tags`, …, any ODCS top-level field) is set on the merged contract; what is not set there (`version`, `apiVersion`, …) is copied from the first table's contract.
- **Server** — the per-table `production` servers collapse into the single server from `server`. `datacontract test` replaces `{model}` with each table name, so one entry covers every CSV file under `data/corrected/`.
- **Descriptions** — for every merged table, the dictionary's `description` replaces the importer's placeholder on the schema object, and each column's `description` is set on the property. A column the dictionary does not know is reported (`providers: not in the dictionary: NPI`).
- **Primary keys** — every column the dictionary marks `key: primary` gets `primaryKey: true` (`patients.Id`, `encounters.Id`; `conditions` and `observations` are event rows without a key).
- **Relationships** — every column whose dictionary entry `references` a table that is *also being merged* gets an ODCS `relationships` block of type `foreignKey`, e.g. on `conditions.PATIENT`:

  ```yaml
  relationships:
    - type: foreignKey
      to: patients.Id
  ```

  For these four tables that yields five relationships. `encounters.ORGANIZATION`, `PROVIDER` and `PAYER` reference tables that are not merged here and are left as plain columns; add `organizations`, `providers` or `payers` to `tables` and their relationships appear on the next run.
- **Overrides** — applied last, so they win over both the importer and the dictionary. A key `<table>` sets fields on the schema object, `<table>.<COLUMN>` on the column; the value is written exactly as it would be in the contract, and `null` removes a field:

  ```yaml
  overrides:
    patients.DEATHDATE:
      logicalType: date            # the importer inferred string
    patients.FIPS:
      logicalType: string          # a code, not a number
      logicalTypeOptions: null     # drop the min/max the importer inferred for a number
    conditions:
      quality:
        - type: sql
          description: Every condition belongs to a patient in the patients table.
          query: SELECT COUNT(*) FROM conditions WHERE PATIENT NOT IN (SELECT Id FROM patients)
          mustBe: 0
  ```

The full pipeline, from the repository root:

```bash
python data-contract/scripts/build_dictionary.py                       # 1. wiki -> outputs/data-dictionary.yaml (run only when the wiki changed)
for t in patients encounters conditions observations; do               # 2. CSV  -> imports/<table>.yaml
  datacontract import csv --source "data/corrected/$t.csv" --output "data-contract/imports/$t.yaml"
done
python data-contract/scripts/merge_schemas.py data-contract/merge.yaml # 3. merge + dictionary + merge.yaml overrides -> outputs/synthea-ms-data.odcs.yaml as defined in `merge.yaml`
```

## Enrich the contract by hand, review, validate and test

The manual step is run by hand from the repository root:

- The first time, copy the generated contract into `final/` and edit that file by hand:

  ```bash
  mkdir -p data-contract/final
  cp data-contract/outputs/synthea-ms-data.odcs.yaml data-contract/final/synthea-ms-data.odcs.yaml
  ```

- After every re-merge, compare the final contract with the generated one, so what a re-import, a rebuilt dictionary or a change to `merge.yaml` changed is visible and can be carried over into `final/` by hand:

  ```bash
  datacontract changelog data-contract/final/synthea-ms-data.odcs.yaml data-contract/outputs/synthea-ms-data.odcs.yaml
  ```

  (To start over from the generated contract, delete `final/synthea-ms-data.odcs.yaml` and copy it again.)

Then lint and test `final/synthea-ms-data.odcs.yaml` and render `final/synthea-ms-data.html` with the commands in the next section. Re-run them after every hand edit.

> ⚠️ `merge_schemas.py` overwrites `outputs/synthea-ms-data.odcs.yaml` on every run; hand edits go into `final/` or `merge.yaml`, never into `outputs/`.

The dictionary gives the contract the *generic* Synthea meaning of every column. What it cannot give is the domain knowledge specific to this dataset:

- `description`, `domain`, `status`, `tags` and a `team` / owner of the contract
- code systems and the codes that matter here: `conditions.CODE` is SNOMED CT, MS is `24700007`, the EDSS score is `273554001`
- `logicalType` corrections where inference was too weak: the dictionary says `DEATHDATE` is a `Date`, the importer inferred `string`; `FIPS` and `ZIP` are codes, not numbers
- quality rules: `edss_score` in `0`–`10` on a `0.5` grid, no negative values, `conditions.PATIENT` must exist in `patients.Id`
- terms of use: *synthetic data, pipeline development and testing only*

Your job is to enrich, correct and perform a review, validate, test and (optional) export.

```bash
# Validate the contract against the ODCS schema and best practices
datacontract lint data-contract/final/synthea-ms-data.odcs.yaml

# Test the contract against the CSV data in data/corrected (schema and quality checks)
datacontract test data-contract/final/synthea-ms-data.odcs.yaml

# Render the contract as a self-contained HTML page
datacontract export html data-contract/final/synthea-ms-data.odcs.yaml --output data-contract/final/synthea-ms-data.html
```

The HTML page shows the fundamentals, the servers, one section per table with all columns, types, constraints and examples, the quality rules and terms, and — because the contract has `relationships` — an ER diagram of the tables at the top. It has no external dependencies, so it can be committed alongside the contract, attached to a data product's documentation, or served from a static site. Regenerate it after every merge or hand edit.

See the [CLI documentation](https://cli.datacontract.com/) for all import, export and test options.

---
