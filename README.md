# Synthea MS Data

[![Project website](https://img.shields.io/badge/website-EHDS%20Ready%20Data%20Product-brightgreen)](https://jrverbiest.eu/projects/get-ehds-ready/get-ehds-ready.html)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Synthea](https://img.shields.io/badge/built%20with-Synthea-blue)](https://github.com/JrVerbiest/synthea)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)

[![Last updated](https://img.shields.io/badge/last%20updated-2026--09--14-lightgrey.svg)](https://github.com/JrVerbiest/synthea-ms-data)

This repo provides a **synthetic** patient dataset for Multiple Sclerosis (MS), generated using [Synthea](https://github.com/synthetichealth/synthea) and the MS Disease Trajectory module.

> MS Disease Trajectory module simulates the disease trajectory of Multiple Sclerosis (MS) using a data-driven, synthetic patient modelling approach. It was developed within the framework of a master's thesis by **N. Rabah** at Universiteit Hasselt (master in Systems and Process Innovation in Healthcare), titled *["A Data-Driven Approach to Develop a Multiple Sclerosis Disease Trajectory using Modelling Techniques for Synthetic Data"](https://documentserver.uhasselt.be/bitstream/1942/46945/1/ebb0f956-7089-4e50-bd4d-29ceb47f9906.pdf)* - [GitHub](https://github.com/UHasselt-BiomedicalDataSciences/MS-Disease-Trajectory-Synthea.git).

The repo contains everything that is needed to regenerate the dataset from scratch — the disease module, the keep filter, a notebook that corrects the raw output, and step-by-step instructions for Unix-like terminals (Linux, macOS, WSL). A fixed random seed makes every run reproducible on any machine.

> ⚠️ **Usage Limitation:** This dataset is for **developing and testing data pipelines only**. It must not be used for clinical decision-making, patient care, or any production healthcare application.
> No real patients are involved. Every record is simulated, and identifiers such as SSNs, passports and email addresses are deliberately fake — SSNs fall in the never-issued `999-xx-xxxx` range and emails end in `@example.com`.

```text
synthea-ms-data/
├── data/
│   ├── raw/
│   │   ├── csv/              Synthea CSV export (Step 6), unmodified
│   │   └── metadata/         Run summary JSON (seed, patient count, module, run time)
│   └── corrected/            CSV files after EDSS correction (written by the notebook, Step 7)
├── filter/
│   └── keep_ms.json          Keep filter — retains only patients with an active MS diagnosis (Step 4)
├── module/
│   ├── multiple_sclerosis_disease_trajectory.json   MS Disease Trajectory module with corrected EDSS coding (Step 2)
│   └── MS disease trajectory Nadia Rabah.pdf        pdf describing the module
├── notebook/
│   └── ms-data-correction.ipynb   Removes negative EDSS values and snaps the rest to the 0.5 grid (Step 7)
├── requirements.txt          Python dependencies for the notebook (jupyter, pandas)
├── LICENSE                   MIT
└── README.md
```

| Folder / file | What it is | Used in |
|---------------|------------|---------|
| `data/raw/csv/` | The raw synthetic dataset generated using Synthea — 13 CSV files (patients, encounters, conditions, observations, medications, …). Never modified. | Step 6 |
| `data/raw/metadata/` | Synthea run summary: seed `12345`, 500 requested / 369 kept patients, module name, Java version, run time. | Step 6 |
| `data/corrected/` | The cleaned dataset produced by the notebook. Same 13 CSV files, same column layout as `data/raw/csv/`. | Step 7 |
| `filter/keep_ms.json` | Synthea keep module that discards patients without an active MS diagnosis (SNOMED CT `24700007`). | Step 4 |
| `module/multiple_sclerosis_disease_trajectory.json` | The MS Disease Trajectory module by N. Rabah, with the correted EDSS coding to SNOMED CT `273554001`. | Step 2 |
| `module/MS disease trajectory Nadia Rabah.pdf` | The module is based on. | Step 2 |
| `notebook/ms-data-correction.ipynb` | Jupyter notebook that reads `data/raw/csv`, removes patients with a negative EDSS value, rounds off-grid values to the nearest `0.5`, validates, and writes `data/corrected`. | Step 7 |
| `requirements.txt` | `jupyter` and `pandas`, the only dependencies needed to run the notebook. | Step 7 |

## Step 1 — Clone Synthea repositories

This dataset was generated using [JrVerbiest/synthea](https://github.com/JrVerbiest/synthea) (a fork of [synthetichealth/synthea](https://github.com/synthetichealth/synthea)) at commit [`d9d07a6`](https://github.com/JrVerbiest/synthea/commit/d9d07a6eef91ee5144293b42ab64224d84d124f8).

```bash
git clone https://github.com/JrVerbiest/synthea.git
cd synthea
```

> 💡 **Shortcut:** the [`enable-csv-export-ms-module`](https://github.com/JrVerbiest/synthea/tree/enable-csv-export-ms-module) branch already contains the corrected module file (Step 2), CSV export enabled (Step 3), and the keep filter (Step 4). Checking it out lets you skip straight to Step 5.
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

## Step 3 — Enable CSV export

In `synthea/src/main/resources/synthea.properties`, set:

```text
exporter.csv.export = true
```

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
 '-m', 'multiple_sclerosis_disease_trajectory', \
 '-k', 'src/main/resources/keep_modules/keep_ms.json'   \
]"
```

| Parameter | Value | Description |
|-----------|-------|-------------|
| `-s` | `12345` | Random seed — fixes the RNG for reproducibility |
| `-p` | `500` | Number of patients to generate |
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

## Step 7 — Correction

The generated dataset contains negative `edss_score` values (an artefact of the MS Disease Trajectory module). These negative values are removed from the dataset; valid `edss_score` values lie on the `0`–`10` scale in `0.5` steps (SNOMED CT `273554001`).

The notebook `ms-data-correction.ipynb` is available in folder `notebook`, and the corrected data (CSV format) is available in `data/corrected`.

### To run the notebook

Create and activate a Python virtual environment, then install the dependencies:

```bash
python3 -m venv --prompt synthea-ms-data .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Verify that `jupyter` and `pandas` are installed in the virtual environment:

```bash
pip show jupyter pandas
```

Launch Jupyter:

```bash
jupyter notebook
```

---
