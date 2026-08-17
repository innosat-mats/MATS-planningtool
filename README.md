# MATS-planningtool

**Author:** Ole Martin Christensen  
**Package:** `mats_planningtool`

Orbital Planning Tool (OPT) for the MATS (Mesospheric Airglow/Aerosol Tomography and Spectroscopy) satellite. Takes a high-level observation plan as a JSON configuration file, simulates the spacecraft orbit, schedules science modes into observation windows, and generates the command sequence XML file that is uplinked to the satellite.

---

## Overview

The tool performs two main stages that we operate, plus a third stage handled externally:

```
JSON Config  →  Science Mode Timeline (JSON)  →  Command Sequence (XML)  →  PLUTO Script
                      [TimelineGenerator]          [XMLGenerator]            [PLUTOGenerator]
                      ◄─────────────── operated by us ──────────────────►    ◄── OHB Sweden ──►
```

1. **Timeline generation** — reads the config, simulates the orbit using TLE data, and automatically schedules multiple science modes into a single timeline based on orbital geometry (e.g. when a bright star is in the field of view, or when the satellite is over the winter hemisphere). In practice we typically run a single operational science mode for the full timeline window.
2. **XML generation** — replays each scheduled mode step-by-step through the orbit simulator to calculate exact command arguments and timings, then writes a fully-specified InnoSat XML command sequence.
3. **PLUTO generation** — converts the XML into a PLUTO procedure script for the satellite's on-board command executor. This stage is performed by OHB Sweden and is not run here.

---

## Directory Structure

```
MATS-planningtool/
├── src/mats_planningtool/      # Main package
│   ├── configFile.py           # Central config class; entry point for all stages
│   ├── Library.py              # Coordinate transforms, logging, utility functions
│   ├── CheckConfigFile/        # Config file validation
│   ├── TimelineGenerator/      # Stage 1: schedule science modes → JSON
│   ├── XMLGenerator/           # Stage 2: JSON → InnoSat XML
│   ├── PLUTOGenerator/         # Stage 3: XML → PLUTO (run by OHB Sweden, not us)
│   ├── TimelinePlotter/        # Simulation and validation plots
│   ├── OrbitSimulator/         # Orbit propagation, FOV, star/moon detection
│   └── TimelineAnalyzer/       # Post-generation diagnostics
├── scripts/                    # Operational run scripts
│   ├── run_operational.py      # Main script for generating operational timelines
│   ├── run_planningtool.py     # General-purpose entry point
│   ├── plot_uv_latitudes.py    # Plot UV channel activation from XML
│   └── generate_overview.py   # Summary report of generated timelines
├── data/
│   └── Operational/            # Config files and generated timelines/XMLs
├── de421.bsp                   # JPL planetary ephemeris
└── hip_main.dat                # Hipparcos star catalogue
```

---

## Installation

```bash
pip install -e .
```

Requires Python 3.8+. Key dependencies: `skyfield`, `pyephem`, `lxml`, `numpy`, `scipy`, `h5py`.

---

## Configuration File

Everything starts from a JSON configuration file (see `data/Operational/configfile_1109_CROPFS.json` for a full example). The key sections are:

| Section | Purpose |
|---|---|
| `Timeline_settings` | Start date, duration, TLE, yaw correction, pointing altitude, CCD sync timing |
| `Modes_priority` | Ordered list of modes to schedule; unfilled time goes to Mode1/2/5 |
| `Operational_Science_Mode_settings` | Parameters for the primary science mode (lat threshold, timestep, CCD macro) |
| `CCD_macro_settings` | CCD window definitions for each macro (HighResUV, HighResIR, CustomBinning, …) |
| `Mode1XX_settings` | Per-mode parameters for calibration and special observation modes |

The four-digit instrument/config ID encodes the measurement type and major version:

**Operational modes** (first digit `1`):
```
1  1  0  9
│  │  └──┴─ major version (00–99)
│  └─────── science mode type
└─────────── 1 = operational
```

**Calibration measurements** (first digit `3`):
```
3  0  4  0
│  └──┤  └─ major version (0–9)
│     └──── calibration type (04 = star, 06 = dark, 20 = full-frame snapshot, …)
└────────── 3 = calibration
```

Examples: `1109` = operational, type 1, major version 09 — `3040` = calibration, star type, version 0 — `3204` = calibration, full-frame type, version 4.

The programme name after the underscore (e.g. `CROPFN`, `CROPFS`, `STAR`) is a free-form label of up to ~7 characters describing the observation programme — there is no strict naming system here.

Inside the config JSON, `version_ID` (e.g. `"02"`) acts as a **minor version** tag — incremented when settings are tweaked without changing the major version. Both are embedded in output filenames so any generated timeline can be traced back to the exact config revision that produced it:

**Bump the major version (last two digits) whenever a config's behaviour changes in a way that affects the generated commands** — e.g. enabling `lon_gate` (see below) on a programme that previously ran without it. The science mode type digit (second digit) stays the same, since the underlying Mode (1, 2, 5, …) hasn't changed — only the major version changes, so `1109_CROPFN` (no gate) becomes e.g. `1110_CROPFN` (gate enabled) rather than silently editing the `1109` config in place.

```
Science_Mode_Timeline_<ID>_<start_date><generation_date><version_ID><programme>.json
Science_Mode_Timeline_1109_23103023102502CROPFS.json
                           ──────┬──────  ─────┬───── ─┬ ──────┬──
                           start 2023-10-30  gen 2023-10-25  v02  CROPFS
```

---

## Stage 1: Timeline Generation

The timeline generator automatically combines multiple science modes into a single timeline. It works through the `Modes_priority` list in the config file, simulates the orbit for each candidate mode, finds suitable observation windows based on orbital geometry (star positions, hemisphere, season), and schedules them in order. Any time not claimed by a priority mode is filled with the operational science mode (Mode1, Mode2, or Mode5 depending on `Choose_Operational_Science_Mode`).

**In practice we almost always run a single operational science mode for the full duration** — the multi-mode scheduling capability is there but rarely used operationally. The `Modes_priority` list in the operational configs therefore only contains startup commands (power toggle, CCD setup, etc.) with no additional observation modes:

```json
"Modes_priority": [
    "Point_at_Standard",
    "Payload_Power_Toggle",
    "ArgEnableYawComp",
    "CCDFlushBadColumns",
    "CCDBadColumn",
    "CCDBIAS",
    "PM",
    "TurnONCCDs"
],
"Choose_Operational_Science_Mode": 1
```

A config that does combine modes looks like the following. The generator places Mode124 (Moon calibration) and Mode120 (star calibration) first, then fills remaining time with the operational mode:

```json
"Modes_priority": [
    "Payload_Power_Toggle", "ArgEnableYawComp", "CCDFlushBadColumns",
    "CCDBadColumn", "CCDBIAS", "PM", "TurnONCCDs",
    "Mode124", "Mode124",
    "Mode120", "Mode120",
    "Mode110", "Mode100",
    "Mode130", "Mode132", "Mode133", "Mode131", "Mode134"
],
"Choose_Operational_Science_Mode": 0
```

(`Choose_Operational_Science_Mode: 0` means no operational fill — only the priority modes are scheduled.)

```python
from mats_planningtool import configFile

cfg = configFile.configFile("data/Operational/configfile_1109_CROPFS.json",
                             "2025/01/18 00:00:00",
                             TLE1="...", TLE2="...")
cfg.CheckConfigFile()
cfg.Timeline_gen()
```

The output is a JSON file saved to `data/Operational_dump/`:

```json
[
  ["Timeline_settings", "...", {...settings...}, ["TLE1", "TLE2"]],
  ["Point_at_Standard", "2025/1/18 00:00:00", "2025/1/18 00:00:45", {}, "..."],
  ["Mode1", "2025/1/18 00:06:00", "2025/1/18 23:59:45",
   {"lat": 45, "timestep": 8, "Choose_Mode5CCDMacro": "HighResUV"}, "..."],
  ...
]
```

---

## Stage 2: XML Generation

```python
cfg.XML_gen("data/Operational_dump/Science_Mode_Timeline_...json")
```

The XML generator loads the Science Mode Timeline and processes each entry. For each science mode it calls the corresponding function in `XMLGenerator/Modes_and_Tests/MODES.py`, which re-runs the orbit simulator for that mode's time window to compute exact command arguments (CCD settings, pointing offsets, synchronisation parameters).

Every state change during a mode is written as one or more XML commands with a `<relativeTime>` (seconds from timeline start) and human-readable `<comment>` that includes the current LP latitude and sun angle. For example, in Mode1 a command is issued whenever either the UV-on/off state or the day/night state changes.

The output XML follows the InnoSat timeline format:

```xml
<InnoSatTimeline>
  <description>
    <validity><startingDate>2025-01-18T00:00:00</startingDate></validity>
  </description>
  <listOfCommands>
    <command mnemonic="TC_acfLimbPointingAltitudeOffset">
      <relativeTime>0</relativeTime>
      <tcArguments>
        <tcArgument mnemonic="Initial">92500</tcArgument>
      </tcArguments>
    </command>
    ...
  </listOfCommands>
</InnoSatTimeline>
```

---

## Science Modes

### Operational Science Modes (fill all available time)

| Mode | Physical purpose | UV channels |
|---|---|---|
| **Mode1** | Noctilucent Cloud (NLC) imaging — winter hemisphere | ON only when LP latitude exceeds the `lat` threshold |
| **Mode2** | Mesospheric airglow — summer hemisphere | IR-focused; UV handling mirrors Mode1 |
| **Mode5** | Default limb observations | Always on |

Mode1 is the workhorse of operational science. It independently tracks two binary conditions and issues a new command whenever either changes:

**UV channels (UV1, UV2)** — controlled by LP latitude. The UV channels are ON when the limb point latitude is poleward of the `lat` threshold in `Operational_Science_Mode_settings`:
- Positive `lat`: UV on when LP latitude > threshold (northern hemisphere, e.g. CROPFN: `lat=45` → UV on above 45°N)
- Negative `lat`: UV on when LP latitude < threshold (southern hemisphere, e.g. CROPD: `lat=-45` → UV on below 45°S)

**Nadir camera** — controlled by day/night at the satellite's nadir point. The Nadir camera is ON during night and OFF during day. "Night" is defined by the solar zenith angle at nadir exceeding a threshold computed from the height at which sunlight is deemed to scatter in the atmosphere (set to 35 km altitude):

```
nadir_eclipse_angle = arccos(R_earth / (R_earth + 35000)) / π × 180 + 90°
```

When `sun_angle > nadir_eclipse_angle` the satellite's nadir is in eclipse (night) and the Nadir camera is enabled.

The state machine tracks `{UV_on, Nadir_on}` as a combined state. A command macro is issued whenever **either** flag changes. This means that a `UV_off` command is re-sent at every day/night crossing even when UV is already off — the macro is re-issued because the Nadir state changed. Each orbit therefore produces one true UV transition (at the latitude threshold) plus additional re-sends at the two day/night boundaries while UV is off.

The four possible states in the XML comments are:

| State | UV | Nadir |
|---|---|---|
| `Mode1_night_UV_on` | ON | ON |
| `Mode1_night_UV_off` | OFF | ON |
| `Mode1_day_UV_on` | ON | OFF |
| `Mode1_day_UV_off` | OFF | OFF |

**Longitude idle gate** — optional, applies to Mode1, Mode2, and Mode5. Set `lon_gate: [lon_min, lon_max]` (degrees) in `Operational_Science_Mode_settings` to put the payload in idle mode (`TC_pafMODE=2`) whenever the estimated LP longitude falls inside the band, resuming normal operation once it exits. Defaults to `[-999, -999]` (disabled) if omitted, so existing configs are unaffected. Per the versioning convention above, turning this on for a programme should bump the config's major version (new 4-digit ID) rather than editing the existing one in place.

**Which side is idle is not symmetric in the two numbers** — the idle band is the arc swept going from `lon_min` to `lon_max` in the increasing/eastward direction, wrapping across the ±180° antimeridian if `lon_min > lon_max`:
- `lon_gate: [-100, 100]` → `lon_min <= lon_max`, so idle is the *direct* interval −100° to 100° (200° wide — Americas/Atlantic/Europe/Africa/Middle East). Active is the 160° Pacific/East-Asia complement.
- `lon_gate: [100, -100]` → `lon_min > lon_max`, so idle *wraps*: 100° → 180° → −180° → −100° (160° wide — Pacific/East Asia). Active is the 200° complement above.

To make the resolved band unambiguous at generation time, `XML_gen` logs a line like `lon_gate [100, -100] -> idle 160.0° (100 to -100, wraps antimeridian), active 200.0°` whenever the gate is enabled. Use `scripts/plot_longitude_gate.py` to visualise it on a world map before committing to a config.

### Calibration and Special Modes

| Mode | Purpose |
|---|---|
| **Mode100** | Altitude sweep — steps pointing altitude from low to high |
| **Mode110** | Continuous altitude sweep at fixed rate |
| **Mode120** | Automatic star calibration — simulates orbit to find windows when a bright star passes through the FOV |
| **Mode124** | Moon calibration |
| **Mode130–134** | Targeted science observations |

---

## CCD Configuration

MATS has seven CCD channels: UV1, UV2, IR1, IR2, IR3, IR4, and Nadir. Each is identified by a `CCDSEL` bitmask value. CCD settings are grouped into named macros in the config:

| Macro | Use |
|---|---|
| `HighResUV` | Operational NLC science — cropped windows tuned to the mesopause altitude and the configured hemisphere |
| `HighResIR` | Operational IR science |
| `CustomBinning` | Full-frame moderate binning |
| `BinnedCalibration` | Calibration with on-chip binning |
| `FullReadout` | Full-frame no binning (large data volume) |
| `LowPixel` | Heavy binning, minimal data |

The CROPF and CROPD observation programmes differ in their `HighResUV` crop windows (NRSKIP, NROW) which are tuned to keep the NLC layer in the CCD frame at +45° and −45° latitude respectively, and in their pointing altitude (CROPF: 92.5 km, CROPD: 87.5 km).

**If you need to change CCD settings**, make sure you edit the macro that is actually being used. The active macro depends on `Choose_Operational_Science_Mode` in `Timeline_settings` and `Choose_Mode5CCDMacro` in `Operational_Science_Mode_settings`:

| `Choose_Operational_Science_Mode` | Mode | CCD macro used |
|---|---|---|
| `1` | Mode1 (NLC) | `HighResUV` |
| `2` | Mode2 (airglow) | `HighResUV` |
| `5` / `6` / `7` | Mode5/6/7 | set by `Choose_Mode5CCDMacro` |

Editing a macro that is not selected by these settings has no effect on the generated timeline.

---

## Utility Scripts

### run_operational.py

`scripts/run_operational.py` is the central script for all operational timeline generation. It contains several generator functions and also serves as a chronological logbook — every timeline ever generated is preserved as a commented-out call at the bottom of the file.

#### `get_MATS_tle()`

Fetches the current two-line element set for MATS (NORAD ID 54227) from Celestrak. Raises `LookupError` if Celestrak is rate-limiting (returns HTML instead of TLE data) — wait ~2 hours and retry.

---

#### `generate_operational_mode(startdate, duration, mode, name, iterate, tle, yaw)`

The main workhorse. Generates a standard operational science timeline.

| Parameter | Type | Description |
|---|---|---|
| `startdate` | `datetime` | Start of the timeline |
| `duration` | `float` | Duration in hours (fractional hours allowed) |
| `mode` | `str` | Instrument/config ID — used to construct `configfile_<mode>_<name>.json` |
| `name` | `str` | Config variant (e.g. `CROPFN`, `CROPFS`, `CROPD`) |
| `iterate` | `str/int` | Suffix appended to the output filename — required when generating multiple timelines for the same date, as files are named by date and would otherwise overwrite each other |
| `tle` | `list` | `[TLE1, TLE2]`; fetched from Celestrak if `None` |
| `yaw` | `bool` | Override yaw correction setting from config |

Steps: fetch TLE → load config → override start date, duration, TLE, yaw → validate → `Timeline_gen()` → `XML_gen()`. Output goes to `data/Operational_dump/`.

Typical usage — one 24-hour block:

```python
generate_operational_mode(DT.datetime(2025, 6, 25, 0, 0), 24, '1109', name='CROPFN')
```

Splitting a day into 6-hour segments (fetch TLE once to keep all segments consistent):

```python
tle = get_MATS_tle()
generate_operational_mode(DT.datetime(2025, 6, 25,  0, 0), 6, '1109', name='CROPFN', iterate=1, tle=tle)
generate_operational_mode(DT.datetime(2025, 6, 25,  6, 0), 6, '1109', name='CROPFN', iterate=2, tle=tle)
generate_operational_mode(DT.datetime(2025, 6, 25, 12, 0), 6, '1109', name='CROPFN', iterate=3, tle=tle)
generate_operational_mode(DT.datetime(2025, 6, 25, 18, 0), 6, '1109', name='CROPFN', iterate=4, tle=tle)
```

---

#### `generate_star_staring_mode(startdate, duration, mode, name, iterate)`

Generates a star calibration timeline (Mode120). Works like `generate_operational_mode` but also overrides `Mode120_settings['TimeToConsider']` to match the requested duration, so the star-finder simulation searches the right time window.

---

#### `generate_fullframe_snapshot(startdate, mode, name, snapshottimes, exptimes, altitude, iterate)`

Generates a timeline for one or more full-frame snapshot exposures at specified absolute times. This is particularly useful when the target observation times have been calculated offline by an external orbit simulator or conjunction tool — you supply the pre-computed datetimes directly and the tool builds the command sequence around them.

| Parameter | Description |
|---|---|
| `snapshottimes` | List of `datetime` objects — when each snapshot should fire |
| `exptimes` | `[UV_exptime_ms, IR_exptime_ms]` — exposure times for each snapshot |
| `altitude` | Pointing altitude in metres (`-1` to keep config default) |

The timeline duration is calculated automatically from the last snapshot time plus a 15-minute margin.

Snapshots are issued with `TC_pafCCDSnapshot` — **no attitude freeze**. The satellite continues its normal limb-pointing attitude during the exposure. (Attitude freeze is only used by the inertial star-staring modes, `Snapshot_Inertial_macro`, not by this function.)

---

#### `generate_rad_measurements(data_frame)`

Batch-generates fullframe snapshot timelines from a pandas DataFrame (loaded via `read_snaptimes()`). Each row in the DataFrame specifies one snapshot event with its time and exposure settings. Calls `generate_fullframe_snapshot()` once per row, incrementing the `iterate` counter automatically.

---

#### `generate_overview(folder)`

Scans a folder for all `Science_Mode_Timeline*.json` and matching XML files, extracts metadata from each (start/end date, instrument ID, config name, pointing altitudes, yaw correction, star names for Mode120), and writes a summary CSV. Used to produce a schedule overview before uplink.

---

#### `read_snaptimes(filename)`

Reads a CSV file of snapshot times (with a `date` and `texpms` column) into a DataFrame. Used as input to `generate_rad_measurements()`.

### Plot UV channel activation

```bash
python scripts/plot_uv_latitudes.py data/Operational/STP-MTS-1109_...xml
```

Parses the XML comments to extract every UV on/off transition with its LP latitude and plots them as a scatter over time (blue = UV on, red = UV off). Note that UV_off commands are re-issued at every day/night boundary even when UV is already off, because the Nadir state changes simultaneously.

### Timeline validation

```python
from mats_planningtool.TimelinePlotter.Core import Timeline_Plotter
Timeline_Plotter(configFile, Science_Mode_Path="...", OHB_H5_Path="...")
```

Re-simulates the timeline and produces time-series plots of MATS latitude, longitude, altitude, yaw, RA/Dec of optical axis, and LP position. Can be compared against OHB telemetry (H5 file) or STK ephemeris (CSV) to validate pointing predictions.

---

## Logging

Each pipeline stage writes detailed logs to its own directory:

| Stage | Log directory |
|---|---|
| Config validation | `Logs_CheckConfigFile/` |
| Timeline generation | `Logs_Timeline_generator/` |
| XML generation | `Logs_XML_generator/` |
| configFile | `Logs_configFile/` |
