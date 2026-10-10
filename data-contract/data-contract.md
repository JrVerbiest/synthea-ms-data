# Data contract

The ODCS file (data contract) describes the 6 tables according the [Open Data Contract Standard](https://bitol-io.github.io/open-data-contract-standard/) (ODCS) v3.2.0: per column its type, description and keys, and where the data is. A script generates a first version from the CSV files and Synthea's data dictionary; after review it moves to `data/synthea-ms-data.odcs.yaml`.

| File | What |
|---|---|
| `data-contract/generate_contract.py` | The script that generates the contract |
| `data-contract/settings.yaml` | Its settings: the tables, the contract's top-level fields and servers, and overrides |

## Generate Data contract

```sh
python data-contract/generate_contract.py
```

The same CSV files, wiki page, settings and datacontract-cli version always give the same file, byte for byte. The script works in four steps:

1. It reads Synthea's [CSV File Data Dictionary](https://github.com/synthetichealth/synthea/wiki/CSV-File-Data-Dictionary) from the wiki: a description per table, and per column a description, a type, and whether it is a primary or foreign key. Wiki column names are matched to the CSV headers ignoring case, spaces and underscores; `RENAMES` in the script holds the one the wiki names differently (`FIPS County Code` is `FIPS`).
2. It imports each CSV file with datacontract-cli. The import gives one schema object per table, with types guessed from the data, `required` when a column has no empty value and `unique` when no value repeats.
3. It writes the dictionary into the schema objects. The dictionary's descriptions, types and keys win over the import; `required` and `unique` stay as imported, because the contract describes the data that exists. A foreign key becomes a relationship only when it points to one of the 6 tables: `conditions.PATIENT` points to `patients.Id`, `encounters.PROVIDER` to nothing, as there is no `providers` table. The examples the import picks are dropped: it samples them at random, so they would differ on every run. A column that isn't in the dictionary is printed as `<table>.<column>: not in the dictionary, left as imported`; today there is none.
4. It merges the 6 schema objects into one contract, sets the top-level fields of `contract` in the settings, and applies the `overrides` last.

| Dictionary type | ODCS `logicalType` |
|---|---|
| `String` | `string` |
| `UUID` | `string`, with `logicalTypeOptions` `format: uuid` |
| `Numeric` | `number` |
| `Date` | `date` |
| `iso8601 UTC Date` | `timestamp` |

### The settings

`data-contract/settings.yaml`:

| Key | What |
|---|---|
| `data` | The folder with the CSV files: `data/csv` |
| `output` | Where the contract is written: `data-contract/synthea-ms-data.odcs.yaml` |
| `tables` | The tables, in the order they appear in the contract |
| `contract` | ODCS top-level fields, set on the contract: `apiVersion`, `id`, `name`, `domain`, `status`, `description`, `tags` and `servers` |
| `contract.apiVersion` | `v3.2.0`. It needs datacontract-cli 1.2.4 from `requirements.txt`, also on the PATH: dataproduct-cli lints the contract with the `datacontract` it finds there, and 1.0.2 rejects v3.2.0 ([Lint](odps-about.qmd#lint)) |
| `contract.servers` | Where the data is; `{model}` is the table name. `local`: the CSV files in this repo, `data/csv/{model}.csv`. `rustfs`: the landing bucket, `s3://synthea-ms-data/dev/v1/{model}.csv` ([Landing bucket](landing-bucket.qmd)) |
| `overrides` | Fields applied last: `<table>` sets fields on the schema object, `<table>.<COLUMN>` on a column. Today one: the description of `conditions.CODE` |

## 2. Review and enrich

Read `data-contract/synthea-ms-data.odcs.yaml` and improve it by hand:

- The descriptions: the wiki's are short, e.g. add codes and units.
- The fake personal data in `patients`: `SSN`, `DRIVERS`, `PASSPORT`, the names and the addresses. Mark them with `classification`, e.g. `classification: confidential` on the column.
- The keys and relationships.

A change you want back after every generation goes into `overrides` instead, e.g.:

```yaml
overrides:
  patients.SSN:
    classification: confidential
```

## 3. Move it to `data/`

The first time:

```sh
mv data-contract/synthea-ms-data.odcs.yaml data/
```

After a later generation, e.g. after a new Synthea run, compare the new version with the one in `data/` first:

```sh
datacontract changelog data/synthea-ms-data.odcs.yaml data-contract/synthea-ms-data.odcs.yaml
datacontract breaking --no-inline-references data/synthea-ms-data.odcs.yaml data-contract/synthea-ms-data.odcs.yaml
```

`changelog` lists every added, removed and changed field, including your hand edits, which a generation doesn't make: carry those over before you move the file. `breaking` exits `1` on a change that breaks a consumer, such as a removed or retyped column. Publish a breaking change as a new version, not over the old one: path `dev/v2/` in the landing bucket, a new contract `version` and a new Output Port, so `dp_ms_core_data` moves over in its own time.

## 4. Lint

```sh
datacontract lint --no-inline-references data/synthea-ms-data.odcs.yaml
```

It checks the file against the ODCS JSON schema of its `apiVersion`, and ends with `🟢 Data contract is valid.` `--no-inline-references` leaves references to other websites, such as a definition URL, unread: lint checks the file only.

## 5. Test

```sh
datacontract test --no-inline-references --server local data/synthea-ms-data.odcs.yaml
```

It reads the CSV files of the server `local` with DuckDB and run all the checks, such as each column's type, no missing values where `required`, no duplicates where `unique`, and each relationship. 
It ends with `🟢 Data contract is valid. Ran ... checks.`.

---
