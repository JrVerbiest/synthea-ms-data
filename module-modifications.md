# Modifications to the MS Disease Trajectory Module

## Change Log

### `Pre-Onset Delay Until MS`

**Change:** `range` changed from `low: 20, high: 40` to `low: 5, high: 15`.

### `RRMS` state

**Change:** Added a `remarks` block. `RRMS Relapse` changed from `"distribution": 0` to `0.45`. `Maintenance_RRMS` changed from `0` to `0.3577`. `Terminal` changed from `0.8277` to `0.02`. `Neurology Consultation: Transition from RRMS` (`0.1723`) unchanged.

### `RRMS Recovery` state

**Change:** Removed the `"actions"` block. `direct_transition` changed from `"RRMS"` to `"RRMS Recovery Gate"`.

### New: `RRMS Recovery Gate` state

**Change:** New `Simple` state, `conditional_transition`: `EDSS > 0` → `RRMS Recovery Decrement`; else → `EDSS Follow-up RRMS`.

### New: `RRMS Recovery Decrement` state

**Change:** New `SetAttribute` state, `EDSS` via `"expression": "Round((if (#{EDSS} - 0.2) < 2 then 2 else (#{EDSS} - 0.2)) * 2) / 2"`. Includes a `remarks` block.

### New: `EDSS Follow-up RRMS` state

**Change:** New `Observation` state, code `SNOMED-CT 273554001`, `"attribute": "EDSS"`. `direct_transition` to `RRMS EDSS 8 Check`.

### New: `RRMS EDSS 8 Check` state

**Change:** New `Simple` state, `conditional_transition`: `EDSS >= 8` → `Terminal`; else → `RRMS`. Includes a `remarks` block.

### `Maintenance_RRMS` state

**Change:** `"unit": "year"` → `"unit": "years"`.

### `PPMS` state

**Change:** Added a `remarks` block. `Terminal` changed from `0.5882` to `0.02`. `PPMS Progression` changed from `0` to `0.5682`. `Neurology Consultation: Transition from PPMS` (`0.4118`) unchanged.

### `SPMS` state

**Change:** Added a `remarks` block. `SPMS Progression` changed from `0` to `0.98`. `Terminal` changed from `1` to `0.02`.

### `SPMS Progression` state

**Change:** `"unit": "year"` → `"unit": "years"`. Removed the `"actions"` block. `direct_transition` changed from `"SPMS"` to `"SPMS Progression Gate"`.

### New: `SPMS Progression Gate` state

**Change:** New `Simple` state, `conditional_transition`: `EDSS < 10` → `SPMS Progression Increment`; else → `EDSS Follow-up SPMS`.

### New: `SPMS Progression Increment` state

**Change:** New `SetAttribute` state, `EDSS` via `"expression": "Round((if (#{EDSS} + 0.4) > 8 then 8 else (#{EDSS} + 0.4)) * 2) / 2"`. Includes a `remarks` block.

### New: `EDSS Follow-up SPMS` state

**Change:** New `Observation` state, code `SNOMED-CT 273554001`, `"attribute": "EDSS"`. `direct_transition` to `SPMS EDSS 8 Check`.

### New: `SPMS EDSS 8 Check` state

**Change:** New `Simple` state, `conditional_transition`: `EDSS >= 8` → `Terminal`; else → `SPMS`. Includes a `remarks` block.

### `Determine PPMS` state

**Change:** `direct_transition` changed from `"Initial EDSS PPMS"` to `"Initial EDSS PPMS Value"`. Removed the `"remarks": ["EDSS "]` stub.

### New: `Initial EDSS PPMS Value`, `Initial EDSS CIS Value`, `Initial EDSS RRMS Value`, `Initial EDSS SPMS Value`, `Initial EDSS PRMS Value` states

**Change:** New `SetAttribute` state per subtype, holding the Gaussian `distribution` (with added `"min": 2, "max": 8`) previously on the corresponding `Initial EDSS <Subtype>` Observation state, setting `"attribute": "EDSS"`. `direct_transition` to a new `Initial EDSS <Subtype> Round` state.

### New: `Initial EDSS PPMS Round`, `Initial EDSS CIS Round`, `Initial EDSS RRMS Round`, `Initial EDSS SPMS Round`, `Initial EDSS PRMS Round` states

**Change:** New `SetAttribute` state per subtype, `"attribute": "EDSS"`, `"expression": "Round(#{EDSS} * 2) / 2"`. `direct_transition` to the corresponding `Initial EDSS <Subtype>` Observation state.

### `Initial EDSS PPMS`, `Initial EDSS CIS`, `Initial EDSS RRMS`, `Initial EDSS SPMS`, `Initial EDSS PRMS` states

**Change:** Code system changed from `LOINC LP241977-0` to `SNOMED-CT 273554001`. Removed the `"distribution"` block; added `"attribute": "EDSS"`.

### `Determine CIS`, `Transition RRMS`, `Transition SPMS`, `Transition PRMS` states

**Change:** `direct_transition` for each changed to the corresponding new `Initial EDSS <Subtype> Value` state.

### `CIS` state

**Change:** `"Neurology Consultation: Transition from CIS"` transition target replaced with new state `"CIS Consultation Delay"`.

### New: `CIS Consultation Delay` state

**Change:** New `Delay` state, `UNIFORM` distribution, `low: 6, high: 24` months. `direct_transition` to `"Neurology Consultation: Transition from CIS"`. Includes a `remarks` block.

### `Neurology Consultation: Transition from RRMS` state

**Change:** `direct_transition` changed from `"Transition SPMS"` to `"SPMS Transition Delay"`.

### New: `SPMS Transition Delay` state

**Change:** New `Delay` state, `UNIFORM` distribution, `low: 6, high: 24` months. `direct_transition` to `"Transition SPMS"`. Includes a `remarks` block.

### `Neurology Consultation` state

**Change:** Removed the `"actions": [{"action": "set_attribute", "target": "EDSS", "value": 2}]` block.

### `Neurology Consultation: Transition from PPMS` state

**Change:** `direct_transition` changed from `"Transition PRMS"` to `"PRMS Transition Delay"`.

### New: `PRMS Transition Delay` state

**Change:** New `Delay` state, `UNIFORM` distribution, `low: 6, high: 24` months. `direct_transition` to `"Transition PRMS"`. Includes a `remarks` block.

### `PRMS` state

**Change:** Added a `remarks` block. `Terminal` changed from `1` to `0.02`. `PRMS Relapse` changed from `0` to `0.49`. `PRMS Progression` changed from `0` to `0.49`.

### `PPMS Progression` state

**Change:** Removed the `"actions"` block. `direct_transition` changed from `"PPMS"` to `"PPMS Progression Gate"`.

### New: `PPMS Progression Gate` state

**Change:** New `Simple` state, `conditional_transition`: `EDSS < 10` → `PPMS Progression Increment`; else → `EDSS Follow-up PPMS`.

### New: `PPMS Progression Increment` state

**Change:** New `SetAttribute` state, `EDSS` via `"expression": "Round((if (#{EDSS} + 0.3) > 8 then 8 else (#{EDSS} + 0.3)) * 2) / 2"`. Includes a `remarks` block.

### New: `EDSS Follow-up PPMS` state

**Change:** New `Observation` state, code `SNOMED-CT 273554001`, `"attribute": "EDSS"`. `direct_transition` to `PPMS EDSS 8 Check`.

### New: `PPMS EDSS 8 Check` state

**Change:** New `Simple` state, `conditional_transition`: `EDSS >= 8` → `Terminal`; else → `PPMS`. Includes a `remarks` block.

### `PRMS Progression` state

**Change:** `direct_transition` changed from `"PRMS"` to `"PRMS Progression Gate"`.

### New: `PRMS Progression Gate` state

**Change:** New `Simple` state, `conditional_transition`: `EDSS < 10` → `PRMS Progression Increment`; else → `EDSS Follow-up PRMS`.

### New: `PRMS Progression Increment` state

**Change:** New `SetAttribute` state, `EDSS` via `"expression": "Round((if (#{EDSS} + 0.3) > 8 then 8 else (#{EDSS} + 0.3)) * 2) / 2"`. Includes a `remarks` block.

### `PRMS Recovery` state

**Change:** Removed the `"actions"` block. `direct_transition` changed from `"PRMS"` to `"PRMS Recovery Gate"`.

### New: `PRMS Recovery Gate` state

**Change:** New `Simple` state, `conditional_transition`: `EDSS > 0` → `PRMS Recovery Decrement`; else → `EDSS Follow-up PRMS`.

### New: `PRMS Recovery Decrement` state

**Change:** New `SetAttribute` state, `EDSS` via `"expression": "Round((if (#{EDSS} - 0.15) < 2 then 2 else (#{EDSS} - 0.15)) * 2) / 2"`. Includes a `remarks` block.

### New: `EDSS Follow-up PRMS` state

**Change:** New `Observation` state, code `SNOMED-CT 273554001`, `"attribute": "EDSS"`. `direct_transition` to `PRMS EDSS 8 Check`. Shared by both `PRMS Progression` and `PRMS Recovery`.

### New: `PRMS EDSS 8 Check` state

**Change:** New `Simple` state, `conditional_transition`: `EDSS >= 8` → `Terminal`; else → `PRMS`. Includes a `remarks` block.
