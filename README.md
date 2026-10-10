# Synthea MS Data

![Work in Progress](https://img.shields.io/badge/status-work%20in%20progress-orange.svg)

[![Project website](https://img.shields.io/badge/website-EHDS%20Ready%20Data%20Product-brightgreen)](https://jrverbiest.eu/projects/get-ehds-ready/get-ehds-ready.html)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Synthea](https://img.shields.io/badge/built%20with-Synthea-blue)](https://github.com/JrVerbiest/synthea)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Data Contract CLI](https://img.shields.io/badge/datacontract--cli-1.2.4-blue)](https://cli.datacontract.com/)
[![ODCS](https://img.shields.io/badge/Open%20Data%20Contract%20Standard-v3.2.0-blue)](https://bitol-io.github.io/open-data-contract-standard/latest/)

This repo provides a **synthetic** Multiple Sclerosis (MS) patient dataset. The data can be found in folder `/data/csv`. It is generated using [Synthea](https://github.com/synthetichealth/synthea) and the MS Disease Trajectory module.

> **⚠️ Usage Limitation:** This dataset is specific **developed for use in a reference data product design**.
> It may **NOT** be used for clinical decision-making, statistical modelling, patient care, or any production healthcare application.

---

## Data Product

This repo is also the data product `synthea-ms-data` with a the data product manifest, data contract, and the about page. 

The docs in [`docs/`](docs/) explain each step. Read them with [Quarto](https://quarto.org):

```bash
cd docs && quarto preview
```

### Data Product Manifest

The ODPS file (data product manifest) describes the data product and its output port and is written according the [Open Data Product Standard](https://github.com/bitol-io/open-data-product-standard) (ODPS) v1.1.0.

```sh
dataproduct lint synthea-ms-data.odps.yaml --local-references
```

It checks the file against the ODPS JSON schema. With `--local-references` it also looks in the repo for the contract with the `id` in `contractId`, prints `resolvable: Found at data/synthea-ms-data.odcs.yaml`, and lints that contract. It ends with `🟢 Data product is valid.`

dataproduct-cli lints the contract with the `datacontract` on the PATH. The contract is ODCS v3.2.0, which needs datacontract-cli 1.2.4 from `requirements.txt`: an older one, such as 1.0.2, fails the contract, yet `dataproduct lint` exits `0`. So run it in the repo's virtual environment.

### Data Contract

The ODCS file (data contract) describes the 6 tables according the [Open Data Contract Standard](https://bitol-io.github.io/open-data-contract-standard/) (ODCS) v3.2.0: per column its type, description and keys, and where the data is. A script generates a first version from the CSV files and Synthea's data dictionary.

The data contract can be found in: `data/synthea-ms-data.odcs.yaml`.

How to regenerate, review, lint and test it: [data-contract/data-contract.md](data-contract/data-contract.md).

---

## Regenerate the dataset from scratch

The repo contains everything that is needed to regenerate the dataset from scratch — the disease module, the keep filter, a notebook that corrects the raw output, and step-by-step instructions for Unix-like terminals (Linux, macOS, WSL). A fixed random seed makes every run reproducible on any machine.

> Note: The MS Disease Trajectory module simulates the disease trajectory of Multiple Sclerosis (MS) using a data-driven, synthetic patient modelling approach. It was developed as part of a master's thesis by **N. Rabah** at Universiteit Hasselt (master in Systems and Process Innovation in Healthcare), titled *["A Data-Driven Approach to Develop a Multiple Sclerosis Disease Trajectory using Modelling Techniques for Synthetic Data"](https://documentserver.uhasselt.be/bitstream/1942/46945/1/ebb0f956-7089-4e50-bd4d-29ceb47f9906.pdf)* - The unmodified MS Disease Trajectory module can be found on [GitHub](https://github.com/UHasselt-BiomedicalDataSciences/MS-Disease-Trajectory-Synthea.git).

### Step 1 — Clone Synthea repositories

This dataset was generated using [JrVerbiest/synthea](https://github.com/JrVerbiest/synthea) (a fork of [synthetichealth/synthea](https://github.com/synthetichealth/synthea)) at commit [`d9d07a6`](https://github.com/JrVerbiest/synthea/commit/d9d07a6eef91ee5144293b42ab64224d84d124f8).

```bash
git clone https://github.com/JrVerbiest/synthea.git
cd synthea
```

> 💡 **Shortcut:** the [`enable-csv-export-ms-module`](https://github.com/JrVerbiest/synthea/tree/enable-csv-export-ms-module) branch already contains the corrected module file (Step 2), `synthea.properties` changes (Step 3), and the keep filter (Step 4). Checking it out lets you skip straight to Step 5.
>
> ```bash
> git clone --branch enable-csv-export-ms-module https://github.com/JrVerbiest/synthea.git
> cd synthea
> ```

### Step 2 — Install the MS Disease Trajectory Module

> **⚠️ The MS Disease Trajectory module has been modified to generate a dataset for both development and testing data transformation pipelines.**<br>
> **⚠️ These modifications are NOT CLINICALLY VALIDATED.**
> 
The applied modifications - changelog - are described in
[`module/module-modifications.md`](module/module-modifications.md).

Copy `module/multiple_sclerosis_disease_trajectory.json` (from this repo) into `synthea/src/main/resources/modules/`.

### Step 3 — `synthea.properties`

In `synthea/src/main/resources/synthea.properties`, set:

```text
exporter.csv.export = true
exporter.years_of_history = 0
```

1. `exporter.csv.export` — enables the CSV exporter. Off by default; Synthea only writes FHIR bundles otherwise. This is what produces the `csv/` folder used in Step 6.

2. `exporter.years_of_history` — The number of years of patient history to include in patient records, defaults to `10`. For example, if set to 5, then all patient histories older than 5 years (from the time you execute the program) will not be included in the exported records. Note that conditions and medications that are currently active will still be exported, regardless of this setting. Set this to 0 to keep all history in the patient record.

### Step 4 — Create a keep filter

Copy `filter/keep_ms.json` (from this repo) into `synthea/src/main/resources/keep_modules/keep_ms.json`.

This filter discards any patient without an active MS diagnosis (SNOMED CT `24700007`). Patients who pass the filter still carry comorbidities and lifecycle conditions from Synthea core modules.

**keep_ms.json:**

```json
{
  "name": "Generated Keep Module",
  "states": {
    "Initial": {
      "type": "Initial",
      "name": "Initial",
      "conditional_transition": [
 {
          "transition": "Keep",
          "condition": {
            "condition_type": "Active Condition",
            "codes": [
 {
                "system": "SNOMED-CT",
                "code": "24700007",
                "display": "Multiple Sclerosis"
 }
 ]
 }
 },
 {
          "transition": "Terminal"
 }
 ]
 },
    "Terminal": {
      "type": "Terminal",
      "name": "Terminal"
 },
    "Keep": {
      "type": "Terminal",
      "name": "Keep"
 }
 },
  "gmf_version": 2
}
```

### Step 5 — Build

```bash
./gradlew build check -x test
```

### Step 6 — Generate the dataset

To generate the dataset, run:

```bash
./gradlew run -Params="[  \
 '-s', '12345',          \
 '-p', '500',            \
 '-a', '0-46',           \
 '-m', 'multiple_sclerosis_disease_trajectory', \
 '-k', 'src/main/resources/keep_modules/keep_ms.json'   \
]"
```

| Parameter | Value | Description |
|-----------|-------|-------------|
| `-s` | `12345` | Random seed — fixes the RNG for reproducibility |
| `-p` | `500` | Number of patients to generate |
| `-a` | `0-46` | Age range at generation time — birthdate is computed relative to today, so `0-46` puts every patient's birth year roughly between 1980 and today. |
| `-m` | `multiple_sclerosis_disease_trajectory` | Activates the MS module alongside Synthea's core modules |
| `-k` | `src/main/resources/keep_modules/keep_ms.json` | Discards patients without an active MS diagnosis |

For the full list of command-line options, see the Synthea wiki page: [Basic Setup and Running](https://github.com/synthetichealth/synthea/wiki/Basic-Setup-and-Running).

Because the keep filter discards patients without an active MS diagnosis, the number of output patients will be fewer than the value passed to `-p`.

The generated files will be in `synthea/output/`:

| Folder | Format | Description |
|--------|--------|-------------|
| `fhir/` | FHIR R4 JSON | One bundle per patient |
| `csv/` | CSV | clinical domain tables |
| `metadata/` | JSON | Run summary (seed, patient count, module, Synthea version, run time) |

The Data Dictionary for the CSV files can be found in the Synthea wiki page: [CSV File Data Dictionary](https://github.com/synthetichealth/synthea/wiki/CSV-File-Data-Dictionary).

From `synthea/output/` copy:

- `patients.csv`
- `conditions.csv`
- `observations.csv`
- `encounters.csv`
- `medications.csv`
- `procedures.csv`

into `data/csv`.

### Step 7 — Create environment

The Python environment is managed with [uv](https://docs.astral.sh/uv/). Create the virtual environment with Python 3.12, activate it and install the dependencies:

```bash
uv venv --python 3.12 --seed --prompt synthea-ms-data .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

`--seed` adds `pip` to the environment, which uv omits by default; IDEs such as VS Code use it to list installed packages. Activating before installing ensures `uv pip` targets this environment rather than another that happens to be active.

> 💡 Without uv, the standard library works as well: `python3.12 -m venv --prompt synthea-ms-data .venv && source .venv/bin/activate && pip install -r requirements.txt`.

Verify the installation:

```bash
uv pip show jupyter pandas   # or: pip show jupyter pandas
datacontract --version       # 1.2.4
dataproduct --version        # 0.3.2
```

`requirements.txt` holds `jupyter`, `pandas` and `matplotlib` for the notebook, and `datacontract-cli[csv,duckdb]` and `dataproduct-cli` for the [Data Product](#data-product), pinned so a reproduction uses the same versions.

---

## GitHub Action

A GitHub Actions workflow checks every pull request and every push to `main`: it lints the ODPS file and the data contract, fails a pull request with a breaking change to the contract, and runs the contract test on `data/csv/`.

How it works and how to require the check: [github-action.md](github-action.md).
