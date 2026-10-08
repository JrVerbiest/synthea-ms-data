# synthea-ms-data

A synthetic daatset of multiple sclerosis (MS) patients in 6 CSV tables.

Not for clinical decision-making, statistical modelling, research conclusions, patient care or any production healthcare application.

| Table | What |
|---|---|
| `patients` | Patient demographic data |
| `encounters` | Patient encounter data |
| `conditions` | Patient conditions or diagnoses |
| `observations` | Patient observations including vital signs and lab reports |
| `medications` | Patient medication data |
| `procedures` | Patient procedure data including surgeries |

`patients.Id` is the patient key: every other table refers to it in `PATIENT`, and `conditions`, `observations`, `medications` and `procedures` refer to `encounters.Id` in `ENCOUNTER`.

---
