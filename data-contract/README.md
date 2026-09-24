# Data contract

This section is still 🚧 **Work in progress**, so the content here may change.

The sections below describe how to reproduce the `synthea-ms-data.odcs.yaml` data contract from scratch.

## Step 1 - Generate the contract for each table

All commands below are run from the **repository root** (`synthea-ms-data/`): the CSV files are read from `data/csv/`, the per-table contracts land in `data-contract/tmp/`. `datacontract import` does not create the folder, so make it once:

```bash
mkdir -p data-contract/tmp
```

Data contract for one table:

```bash
datacontract import csv --source data/csv/patients.csv --output data-contract/tmp/patients.yaml
```

Data contract all 13 tables:

```bash
for f in data/csv/*.csv; do
 datacontract import csv --source "$f" --output "data-contract/tmp/$(basename "$f" .csv).yaml"
done
```

Data contract specific tables, for example, `patients`, `encounters`, `conditions`, and `observations`:

```bash
for t in patients encounters conditions observations; do
 datacontract import csv --source "data/csv/$t.csv" --output "data-contract/tmp/$t.yaml"
done
```

> **REMARK**: A CSV file carries no information about what its columns mean or how tables relate — there are no descriptions and no `PRIMARY KEY` / `FOREIGN KEY` metadata as in a SQL DDL — so the imported contracts have placeholder descriptions (`Generated model of data/corrected/patients.csv`), no keys and no `relationships` between them.

> **The Synthea data dictionary documents all of that on its wiki page**.

## Step 2 - Fetch the data dictionary from the wiki

```bash
python data-contract/scripts/build_dictionary.py
```

The script `build_dictionary.py` fetches the [CSV-File-Data-Dictionary.md](https://raw.githubusercontent.com/wiki/synthetichealth/synthea/CSV-File-Data-Dictionary.md), parses the file list and the per-table column tables, and writes `data-contract/tmp/data-dictionary.yaml` covering all 18 CSV files Synthea can export (256 columns). Re-run it whenever the wiki changes; the file records the source URL, the retrieval date, and a SHA-256 hash of the page, so any change shows up in the diff.

## Step 3 - Enrich based on data dictionary

```bash
python data-contract/scripts/enrich_schemas.py data-contract/tmp/{patients,encounters,conditions,observations}.yaml
```

`enrich_schemas.py` reads `data-contract/tmp/data-dictionary.yaml` and writes what it knows into the
contracts **in place**: every file passed on the command line is overwritten.

## 4. Merge

The [`merge.yaml`](merge.yaml) says what to merge and holds everything that is written by hand; the *meaning* of the columns is already in the per-table contracts after step 3. Paths in the YAML are relative to the YAML file, except `server.path`, which `datacontract test` resolves from the directory it is run in. Run the script from the repository root:

> Note: the provided `merge.yaml` merges the patient, encounter, condition and observation contracts.

```bash
python data-contract/scripts/merge_schemas.py data-contract/merge.yaml
```

This writes `data-contract/tmp/synthea-ms-data.odcs.yaml`, next to the per-table contracts. The script uses only the ODCS model that ships with `datacontract-cli`, so no additional dependencies are needed.

## Step 5 - Review, enrich, validate and test

The manual step is run by hand from the repository root:

- The first time, copy the generated contract into `data-contract` and edit that file by hand:

 ```bash
  cp data-contract/tmp/synthea-ms-data.odcs.yaml data-contract/synthea-ms-data.odcs.yaml
 ```

- After every re-merge, compare the final contract with the generated one, so that what a re-import, a rebuilt dictionary or a change to `merge.yaml` changed is visible and can be carried over into the data-contract by hand:

 ```bash
  datacontract changelog data-contract/synthea-ms-data.odcs.yaml data-contract/tmp/synthea-ms-data.odcs.yaml
 ```

 (To start over from the generated contract, delete `final/synthea-ms-data.odcs.yaml` and copy it again.)

Final:

1. Validate the contract against the ODCS schema and best practices

```bash
datacontract lint data-contract/synthea-ms-data.odcs.yaml
```

2. Test the contract against the CSV data in data/corrected (schema and quality checks)
  
```bash
datacontract test data-contract/synthea-ms-data.odcs.yaml
```

3. Optionally, you can render the contract as a self-contained HTML page

```bash
datacontract export html data-contract/final/synthea-ms-data.odcs.yaml --output data-contract/synthea-ms-data.html
```

---