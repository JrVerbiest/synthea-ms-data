# Synthea MS Data

![Work in Progress](https://img.shields.io/badge/status-work%20in%20progress-orange.svg)

[![Project website](https://img.shields.io/badge/website-EHDS%20Ready%20Data%20Product-brightgreen)](https://jrverbiest.eu/projects/get-ehds-ready/get-ehds-ready.html)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Synthea](https://img.shields.io/badge/built%20with-Synthea-blue)](https://github.com/JrVerbiest/synthea)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Data Contract CLI](https://img.shields.io/badge/datacontract--cli-1.2.0-blue)](https://cli.datacontract.com/)
[![ODCS](https://img.shields.io/badge/Open%20Data%20Contract%20Standard-v3.2.0-blue)](https://bitol-io.github.io/open-data-contract-standard/latest/)

This repo provides a **synthetic** patient dataset for Multiple Sclerosis (MS), generated using [Synthea](https://github.com/synthetichealth/synthea) and the MS Disease Trajectory module.

> **⚠️ Usage Limitation:** This dataset is specific **developed for use in a reference data product design (see step 8).**
> It must **NOT** be used for clinical decision-making, statistical modelling, patient care, or any production healthcare application.
>
> ⚠️ The MS Disease Trajectory module has been modified to support use of the dataset in both development and testing data transformation pipelines.
> 
> ⚠️ These modifications are **NOT CLINICALLY VALIDATED.**

The repo contains everything that is needed to regenerate the dataset from scratch — the disease module, the keep filter, a notebook that corrects the raw output, and step-by-step instructions for Unix-like terminals (Linux, macOS, WSL). A fixed random seed makes every run reproducible on any machine.

> Note: The MS Disease Trajectory module simulates the disease trajectory of Multiple Sclerosis (MS) using a data-driven, synthetic patient modelling approach. It was developed as part of a master's thesis by **N. Rabah** at Universiteit Hasselt (master in Systems and Process Innovation in Healthcare), titled *["A Data-Driven Approach to Develop a Multiple Sclerosis Disease Trajectory using Modelling Techniques for Synthetic Data"](https://documentserver.uhasselt.be/bitstream/1942/46945/1/ebb0f956-7089-4e50-bd4d-29ceb47f9906.pdf)* - The unmodified MS Disease Trajectory module can be found on [GitHub](https://github.com/UHasselt-BiomedicalDataSciences/MS-Disease-Trajectory-Synthea.git).

---

```text
synthea-ms-data/
├── data/
│   ├── csv/                                          Synthea CSV export (Step 6), unmodified
│   └── metadata/                                     Run summary JSON (seed, patient count, module, run time)
├── docs/
│   └── MS disease trajectory Nadia Rabah.pdf         Describing the initial module
├── filter/
│   └── keep_ms.json                                  Keep filter — retains only patients with an active MS diagnosis (Step 4)
├── module/
│   └── multiple_sclerosis_disease_trajectory.json    MS Disease Trajectory module with modifications (Step 8)
├── data-contract/                                    Data contract of the corrected dataset and how it is built (Step 10)
│   ├── README.md
│   ├── merge.yaml                                    What to merge, plus the hand-written parts: fundamentals, type corrections, quality rules
│   └── scripts/                                      build_dictionary.py, enrich_schemas.py, merge_schemas.py
├── notebook/
│   └── edss-observations.ipynb                       Notebook to explore the Expanded Disability Status Scale 
├── requirements.txt                                  Python dependencies: jupyter, pandas, datacontract-cli[csv,duckdb]
├── LICENSE                                           MIT
└── README.md
```

## Step 1 — Clone Synthea repositories

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

## Step 2 — MS Disease Trajectory Module

### Correction: EDSS Coding in MS Disease Trajectory Module

In `synthea-ms-data/module/multiple_sclerosis_disease_trajectory.json`, a correction was made to the coding of the **Expanded Disability Status Scale (EDSS) score**.

- **Previous (incorrect):** LOINC `LP241977-0`
- **Corrected to:** SNOMED CT `273554001` — *Kurtzke multiple sclerosis rating scale (assessment scale)*

### Install the module

Copy `module/multiple_sclerosis_disease_trajectory.json` (from this repo) into `synthea/src/main/resources/modules/`.

## Step 3 — `synthea.properties`

In `synthea/src/main/resources/synthea.properties`, set:

```text
exporter.csv.export = true
exporter.years_of_history = 0
```

1. `exporter.csv.export` — enables the CSV exporter. Off by default; Synthea only writes FHIR bundles otherwise. This is what produces the `csv/` folder used in Step 6.

2. `exporter.years_of_history` — The number of years of patient history to include in patient records, defaults to `10`. For example, if set to 5, then all patient histories older than 5 years (from the time you execute the program) will not be included in the exported records. Note that conditions and medications that are currently active will still be exported, regardless of this setting. Set this to 0 to keep all history in the patient record.


> **⚠️ The MS Disease Trajectory module has been modified to generate a dataset for both development and testing data transformation pipelines.**<br>
> **⚠️ These modifications are NOT CLINICALLY VALIDATED.**
> 
The applied modifications - changelog - are described in
[`docs/module-modifictions.md`](docs/module-modifictions.md).

## Step 4 — Create a keep filter

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

## Step 5 — Build

```bash
./gradlew build check -x test
```

## Step 6 — Generate the dataset

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

Copy the contents of `synthea/output/` into `data/raw`.

## Step 7 — Create environment

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
datacontract --version       # 1.2.0
```

`requirements.txt` holds `jupyter` and `pandas` for the notebook (Step 8) and `datacontract-cli[csv,duckdb]` for the data contract (Step 9).

## Step 8 - Using the synthetic MS dataset in a Data Product

This section is still 🚧 **Work in progress**, so the content here may change.

The central artefact in the design of a data product is the data contract, which serves as the design specification against which the transformation pipeline is built and tested. A data contract is an agreement between a data producer and its consumers - [Andrew Jones](https://andrew-jones.com/). It specifies exactly what the data product exposes, its structure, semantics, quality rules, and service-level commitments, and is machine-readable, so it can be automatically enforced rather than just documented and forgotten.

The data contracts for the Synthea MS data are located in the [`data-contract/`](data-contract/) folder. See [data-contract/README.md](data-contract/README.md) for the full write-up. This data contract can be used in a concrete data product implementation.

---
