# Modifications to the MS Disease Trajectory Module

## Why

**The dataset is meant for developing and testing data transformation pipelines**, so each patient needs EDSS scores that are valid and change over time. The [original module](https://github.com/UHasselt-BiomedicalDataSciences/MS-Disease-Trajectory-Synthea.git) gives most patients a single EDSS observation, and that value can be negative or off the `0.5` grid.

> ⚠️ All new probabilities, steps, delays and thresholds are placeholders. They were chosen only to produce usable test data, are **not clinically validated** and do not come from the literature.

| Problem in the original module | Change | States |
|---|---|---|
| The loops that produce repeat visits had probability `0` (dead code), so most patients went straight to `Terminal` after their first EDSS. | Probability moved from `Terminal` to the relapse, maintenance and progression loops. `Terminal` is now `0.02`: it only ends this submodule, not the patient's life (Synthea's death module handles that), and MS runs for decades. | `RRMS`, `PPMS`, `SPMS`, `PRMS` |
| The loops never recorded an EDSS observation, and the PPMS and PRMS loops did not change EDSS at all. | Each cycle now goes Gate → Increment/Decrement → an `EDSS Follow-up <subtype>` observation. | Gate, Increment, Decrement and Follow-up states |
| The first EDSS observation drew its own Gaussian value, while the `EDSS` attribute was fixed at `2`, so progression would start from 2 instead of the recorded score. | The Gaussian now sets the `EDSS` attribute, which is rounded and then recorded. The fixed `2` is removed. | `Initial EDSS <subtype> Value`, `... Round`, `Initial EDSS <subtype>`, `Neurology Consultation` |
| EDSS runs from 0 to 10 in `0.5` steps, but the unbounded Gaussian produced negative and off-grid values. | Values are bounded to 2–8 and rounded to `0.5` (`Round(x * 2) / 2`) at every step, so the correction notebook is no longer needed. | `Initial EDSS <subtype> Value`, `... Round`, Increment and Decrement states |
| A patient at the maximum EDSS would keep looping. | The trajectory stops once EDSS reaches 8. | `<subtype> EDSS 8 Check` |
| `LP241977-0` is a LOINC Part code, not a code for an observation result. | EDSS is coded as SNOMED CT `273554001` (Kurtzke multiple sclerosis rating scale). | `Initial EDSS <subtype>`, Follow-up states |
| Synthea expects plural time units (`years`). The singular `year` only went unnoticed because these states were never reached. | `year` → `years`. | `Maintenance_RRMS`, `SPMS Progression` |
| MS onset came 20–40 years after birth. With patients generated at ages 0–46 (`-a 0-46`), many never reached onset and were dropped by the keep filter, and the rest had few years left for follow-up. | Onset delay shortened to 5–15 years. | `Pre-Onset Delay Until MS` |
| Subtype transitions happened back to back, on the same date. | A 6–24 month delay before each transition. | `CIS Consultation Delay`, `SPMS Transition Delay`, `PRMS Transition Delay` |

## Change Log

### `Pre-Onset Delay Until MS`

**Change:** `range` changed from `low: 20, high: 40` to `low: 5, high: 15`.

**Why:** With patients aged 0–46, a 20–40 year delay meant many never reached MS onset, and the rest had few years left for follow-up.

### `RRMS` state

**Change:** Added a `remarks` block. `RRMS Relapse` changed from `"distribution": 0` to `0.45`. `Maintenance_RRMS` changed from `0` to `0.3577`. `Terminal` changed from `0.8277` to `0.02`. `Neurology Consultation: Transition from RRMS` (`0.1723`) unchanged.

**Why:** Relapse and Maintenance were `0` (dead code), so no repeat EDSS visits were made. `Terminal` is low because it only ends this submodule, not the patient's life.

### `RRMS Recovery` state

**Change:** Removed the `"actions"` block. `direct_transition` changed from `"RRMS"` to `"RRMS Recovery Gate"`.

**Why:** The `decrement_attribute` action cannot bound or round the value. The step moved to `RRMS Recovery Decrement`.

### New: `RRMS Recovery Gate` state

**Change:** New `Simple` state, `conditional_transition`: `EDSS > 0` → `RRMS Recovery Decrement`; else → `EDSS Follow-up RRMS`.

**Why:** Guards the decrement against the bottom of the EDSS scale. EDSS never drops below 2, so the else branch is never taken.

### New: `RRMS Recovery Decrement` state

**Change:** New `SetAttribute` state, `EDSS` via `"expression": "Round((if (#{EDSS} - 0.2) < 2 then 2 else (#{EDSS} - 0.2)) * 2) / 2"`. `direct_transition` to `EDSS Follow-up RRMS`. Includes a `remarks` block.

**Why:** Lowers EDSS after a relapse while keeping it ≥ 2 and on the `0.5` grid. Note: rounding undoes a `0.2` step, so EDSS does not actually go down.

### New: `EDSS Follow-up RRMS` state

**Change:** New `Observation` state, code `SNOMED-CT 273554001`, `"attribute": "EDSS"`. `direct_transition` to `RRMS EDSS 8 Check`.

**Why:** Records EDSS after each cycle. The original loop changed the attribute but never recorded it.

### New: `RRMS EDSS 8 Check` state

**Change:** New `Simple` state, `conditional_transition`: `EDSS >= 8` → `Terminal`; else → `RRMS`. Includes a `remarks` block.

**Why:** Stops MS follow-up once EDSS reaches 8 (bedridden) instead of looping forever.

### `Maintenance_RRMS` state

**Change:** `"unit": "year"` → `"unit": "years"`.

**Why:** Synthea expects plural time units. The bug went unnoticed because this state was never reached.

### `PPMS` state

**Change:** Added a `remarks` block. `Terminal` changed from `0.5882` to `0.02`. `PPMS Progression` changed from `0` to `0.5682`. `Neurology Consultation: Transition from PPMS` (`0.4118`) unchanged.

**Why:** Progression was `0` (dead code), so no repeat EDSS visits were made. `Terminal` is low because it only ends this submodule, not the patient's life.

### `SPMS` state

**Change:** Added a `remarks` block. `SPMS Progression` changed from `0` to `0.98`. `Terminal` changed from `1` to `0.02`.

**Why:** Progression was `0` (dead code), so no repeat EDSS visits were made. `Terminal` is low because it only ends this submodule, not the patient's life.

### `SPMS Progression` state

**Change:** `"unit": "year"` → `"unit": "years"`. Removed the `"actions"` block. `direct_transition` changed from `"SPMS"` to `"SPMS Progression Gate"`.

**Why:** Synthea expects plural time units. The `increment_attribute` action cannot bound or round the value, so the step moved to `SPMS Progression Increment`.

### New: `SPMS Progression Gate` state

**Change:** New `Simple` state, `conditional_transition`: `EDSS < 10` → `SPMS Progression Increment`; else → `EDSS Follow-up SPMS`.

**Why:** Guards the increment against the top of the EDSS scale. EDSS never exceeds 8, so the else branch is never taken.

### New: `SPMS Progression Increment` state

**Change:** New `SetAttribute` state, `EDSS` via `"expression": "Round((if (#{EDSS} + 0.4) > 8 then 8 else (#{EDSS} + 0.4)) * 2) / 2"`. `direct_transition` to `EDSS Follow-up SPMS`. Includes a `remarks` block.

**Why:** Raises EDSS each year while keeping it ≤ 8 and on the `0.5` grid. Note: rounding turns a `0.4` step into `0.5`.

### New: `EDSS Follow-up SPMS` state

**Change:** New `Observation` state, code `SNOMED-CT 273554001`, `"attribute": "EDSS"`. `direct_transition` to `SPMS EDSS 8 Check`.

**Why:** Records EDSS after each cycle. The original loop changed the attribute but never recorded it.

### New: `SPMS EDSS 8 Check` state

**Change:** New `Simple` state, `conditional_transition`: `EDSS >= 8` → `Terminal`; else → `SPMS`. Includes a `remarks` block.

**Why:** Stops MS follow-up once EDSS reaches 8 (bedridden) instead of looping forever.

### `Determine PPMS` state

**Change:** `direct_transition` changed from `"Initial EDSS PPMS"` to `"Initial EDSS PPMS Value"`. Removed the `"remarks": ["EDSS "]` stub.

**Why:** Routes through the new Value state so the initial EDSS is stored in the attribute. The stub remark was empty.

### New: `Initial EDSS PPMS Value`, `Initial EDSS CIS Value`, `Initial EDSS RRMS Value`, `Initial EDSS SPMS Value`, `Initial EDSS PRMS Value` states

**Change:** New `SetAttribute` state per subtype, holding the Gaussian `distribution` (with added `"min": 2, "max": 8`) previously on the corresponding `Initial EDSS <Subtype>` Observation state, setting `"attribute": "EDSS"`. `direct_transition` to a new `Initial EDSS <Subtype> Round` state.

**Why:** Stores the initial EDSS in the attribute so later steps start from the recorded score, not a fixed `2`. The 2–8 bounds stop negative values.

### New: `Initial EDSS PPMS Round`, `Initial EDSS CIS Round`, `Initial EDSS RRMS Round`, `Initial EDSS SPMS Round`, `Initial EDSS PRMS Round` states

**Change:** New `SetAttribute` state per subtype, `"attribute": "EDSS"`, `"expression": "Round(#{EDSS} * 2) / 2"`. `direct_transition` to the corresponding `Initial EDSS <Subtype>` Observation state.

**Why:** EDSS is scored in `0.5` steps. The Gaussian gave values such as `2.7`.

### `Initial EDSS PPMS`, `Initial EDSS CIS`, `Initial EDSS RRMS`, `Initial EDSS SPMS`, `Initial EDSS PRMS` states

**Change:** Code system changed from `LOINC LP241977-0` to `SNOMED-CT 273554001`. Removed the `"distribution"` block; added `"attribute": "EDSS"`.

**Why:** `LP241977-0` is a LOINC Part code, not a code for an observation result. The value now comes from the attribute, so the observation and the attribute are the same.

### `Determine CIS`, `Transition RRMS`, `Transition SPMS`, `Transition PRMS` states

**Change:** `direct_transition` for each changed to the corresponding new `Initial EDSS <Subtype> Value` state.

**Why:** Routes through the new Value state so the initial EDSS is stored in the attribute.

### `CIS` state

**Change:** `"Neurology Consultation: Transition from CIS"` transition target replaced with new state `"CIS Consultation Delay"`.

**Why:** Adds time between CIS and the MS diagnosis. They happened on the same date.

### New: `CIS Consultation Delay` state

**Change:** New `Delay` state, `UNIFORM` distribution, `low: 6, high: 24` months. `direct_transition` to `"Neurology Consultation: Transition from CIS"`. Includes a `remarks` block.

**Why:** Spreads subtype transitions out in time.

### `Neurology Consultation: Transition from RRMS` state

**Change:** `direct_transition` changed from `"Transition SPMS"` to `"SPMS Transition Delay"`.

**Why:** Adds time between the consultation and the switch to SPMS. They happened on the same date.

### New: `SPMS Transition Delay` state

**Change:** New `Delay` state, `UNIFORM` distribution, `low: 6, high: 24` months. `direct_transition` to `"Transition SPMS"`. Includes a `remarks` block.

**Why:** Spreads subtype transitions out in time.

### `Neurology Consultation` state

**Change:** Removed the `"actions": [{"action": "set_attribute", "target": "EDSS", "value": 2}]` block.

**Why:** The attribute was fixed at `2` whatever the recorded score. The Value states now set it.

### `Neurology Consultation: Transition from PPMS` state

**Change:** `direct_transition` changed from `"Transition PRMS"` to `"PRMS Transition Delay"`.

**Why:** Adds time between the consultation and the switch to PRMS. They happened on the same date.

### New: `PRMS Transition Delay` state

**Change:** New `Delay` state, `UNIFORM` distribution, `low: 6, high: 24` months. `direct_transition` to `"Transition PRMS"`. Includes a `remarks` block.

**Why:** Spreads subtype transitions out in time.

### `PRMS` state

**Change:** Added a `remarks` block. `Terminal` changed from `1` to `0.02`. `PRMS Relapse` changed from `0` to `0.49`. `PRMS Progression` changed from `0` to `0.49`.

**Why:** Relapse and Progression were `0` (dead code), so no repeat EDSS visits were made. `Terminal` is low because it only ends this submodule, not the patient's life.

### `PPMS Progression` state

**Change:** `direct_transition` changed from `"PPMS"` to `"PPMS Progression Gate"`.

**Why:** The original loop did not change EDSS at all. It now goes through a progression step.

### New: `PPMS Progression Gate` state

**Change:** New `Simple` state, `conditional_transition`: `EDSS < 10` → `PPMS Progression Increment`; else → `EDSS Follow-up PPMS`.

**Why:** Guards the increment against the top of the EDSS scale. EDSS never exceeds 8, so the else branch is never taken.

### New: `PPMS Progression Increment` state

**Change:** New `SetAttribute` state, `EDSS` via `"expression": "Round((if (#{EDSS} + 0.3) > 8 then 8 else (#{EDSS} + 0.3)) * 2) / 2"`. `direct_transition` to `EDSS Follow-up PPMS`. Includes a `remarks` block.

**Why:** Raises EDSS each year while keeping it ≤ 8 and on the `0.5` grid. Note: rounding turns a `0.3` step into `0.5`.

### New: `EDSS Follow-up PPMS` state

**Change:** New `Observation` state, code `SNOMED-CT 273554001`, `"attribute": "EDSS"`. `direct_transition` to `PPMS EDSS 8 Check`.

**Why:** Records EDSS after each cycle.

### New: `PPMS EDSS 8 Check` state

**Change:** New `Simple` state, `conditional_transition`: `EDSS >= 8` → `Terminal`; else → `PPMS`. Includes a `remarks` block.

**Why:** Stops MS follow-up once EDSS reaches 8 (bedridden) instead of looping forever.

### `PRMS Progression` state

**Change:** `direct_transition` changed from `"PRMS"` to `"PRMS Progression Gate"`.

**Why:** The original loop did not change EDSS at all. It now goes through a progression step.

### New: `PRMS Progression Gate` state

**Change:** New `Simple` state, `conditional_transition`: `EDSS < 10` → `PRMS Progression Increment`; else → `EDSS Follow-up PRMS`.

**Why:** Guards the increment against the top of the EDSS scale. EDSS never exceeds 8, so the else branch is never taken.

### New: `PRMS Progression Increment` state

**Change:** New `SetAttribute` state, `EDSS` via `"expression": "Round((if (#{EDSS} + 0.3) > 8 then 8 else (#{EDSS} + 0.3)) * 2) / 2"`. `direct_transition` to `EDSS Follow-up PRMS`. Includes a `remarks` block.

**Why:** Raises EDSS each year while keeping it ≤ 8 and on the `0.5` grid. Note: rounding turns a `0.3` step into `0.5`.

### `PRMS Recovery` state

**Change:** `direct_transition` changed from `"PRMS"` to `"PRMS Recovery Gate"`.

**Why:** The original loop did not change EDSS at all. It now goes through a recovery step.

### New: `PRMS Recovery Gate` state

**Change:** New `Simple` state, `conditional_transition`: `EDSS > 0` → `PRMS Recovery Decrement`; else → `EDSS Follow-up PRMS`.

**Why:** Guards the decrement against the bottom of the EDSS scale. EDSS never drops below 2, so the else branch is never taken.

### New: `PRMS Recovery Decrement` state

**Change:** New `SetAttribute` state, `EDSS` via `"expression": "Round((if (#{EDSS} - 0.15) < 2 then 2 else (#{EDSS} - 0.15)) * 2) / 2"`. `direct_transition` to `EDSS Follow-up PRMS`. Includes a `remarks` block.

**Why:** Lowers EDSS after a relapse while keeping it ≥ 2 and on the `0.5` grid. Note: rounding undoes a `0.15` step, so EDSS does not actually go down.

### New: `EDSS Follow-up PRMS` state

**Change:** New `Observation` state, code `SNOMED-CT 273554001`, `"attribute": "EDSS"`. `direct_transition` to `PRMS EDSS 8 Check`. Shared by both `PRMS Progression` and `PRMS Recovery`.

**Why:** Records EDSS after each cycle.

### New: `PRMS EDSS 8 Check` state

**Change:** New `Simple` state, `conditional_transition`: `EDSS >= 8` → `Terminal`; else → `PRMS`. Includes a `remarks` block.

**Why:** Stops MS follow-up once EDSS reaches 8 (bedridden) instead of looping forever.
