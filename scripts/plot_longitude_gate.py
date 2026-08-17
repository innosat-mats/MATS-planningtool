"""Verify a Mode1/Mode2/Mode5 longitude idle-gate: re-simulate the ground track for a
config + generated XML and plot (1) the track on a world map colored by idle state, and
(2) longitude/latitude vs time with the actual generated TC_pafMODE commands overlaid, to
confirm the simulated gate crossings match the commands the XML generator actually wrote.
"""

import datetime as DT
import json
import math
import sys
import xml.etree.ElementTree as ET

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import skyfield.api

from mats_planningtool import configFile as configFile
from mats_planningtool.OrbitSimulator.MatsBana import Satellite_Simulator
from mats_planningtool.XMLGenerator.Modes_and_Tests.MODES import check_lat, check_lon

# Same eclipse-angle formula as MODES.py's Mode1/Mode2 (height at which sunlight is
# deemed to scatter in the atmosphere, 35 km, determines the day/night Nadir threshold).
R_MEAN = 6371000.0
HEIGHT_ABOVE_SURFACE = 35000.0
NADIR_ECLIPSE_ANGLE = math.degrees(math.acos(R_MEAN / (R_MEAN + HEIGHT_ABOVE_SURFACE))) + 90


def simulate_ground_track(cfg, start_date, duration_s, step_s=15):
    Timeline_settings = cfg.Timeline_settings()
    TLE = cfg.getTLE()
    pointing_altitude_km = Timeline_settings["StandardPointingAltitude"] / 1000
    satellite = skyfield.api.EarthSatellite(TLE[0], TLE[1])

    times, lons, lats, sun_angles = [], [], [], []
    for i in range(0, duration_s, step_s):
        t = start_date + DT.timedelta(seconds=i)
        d = Satellite_Simulator(satellite, t, Timeline_settings, pointing_altitude_km, False, None)
        times.append(i)
        lons.append(float(d["EstimatedLongitude_LP [degrees]"]))
        lats.append(float(d["EstimatedLatitude_LP [degrees]"]))
        sun_angles.append(float(d["SolarZenithAngleNadir"]))
    return np.array(times), np.array(lons), np.array(lats), np.array(sun_angles)


def transition_times(mask, times):
    idx = np.where(np.diff(mask.astype(int)) != 0)[0] + 1
    return times[idx]


def mask_to_intervals(times, mask, step_s):
    """Convert a boolean per-sample mask into (start, duration) run-length intervals,
    for matplotlib's broken_barh."""
    intervals = []
    in_run = False
    start = None
    for t, m in zip(times, mask):
        if m and not in_run:
            start, in_run = t, True
        elif not m and in_run:
            intervals.append((start, t - start))
            in_run = False
    if in_run:
        intervals.append((start, times[-1] + step_s - start))
    return intervals


def parse_mode_commands(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    commands = []
    for c in root[1]:
        if c.attrib.get("mnemonic") != "TC_pafMODE":
            continue
        rt = int(c.find("relativeTime").text)
        mode = int(c.find("tcArguments").find("tcArgument").text)
        comment = c.find("comment").text or ""
        commands.append((rt, mode, comment))
    return commands


def parse_ccd_commands(xml_path):
    """Every TC_pafCCD command as (relativeTime, CCDSEL, TEXPMS) — the real, ground-truth
    record of when each CCD's exposure time was actually set, as opposed to re-deriving it
    from an idealized orbit simulation."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    commands = []
    for c in root[1]:
        if c.attrib.get("mnemonic") != "TC_pafCCD":
            continue
        rt = int(c.find("relativeTime").text)
        args = {a.attrib.get("mnemonic"): a.text for a in c.find("tcArguments")}
        commands.append((rt, int(args["CCDSEL"]), int(args["TEXPMS"])))
    return commands


def step_values(sample_times, event_times, event_values, initial_value):
    """Evaluate a step function (defined by (event_time, value) pairs, holding each value
    until the next event) at each of sample_times."""
    if not event_times:
        return np.full(len(sample_times), initial_value)
    order = np.argsort(event_times)
    event_times = np.asarray(event_times)[order]
    event_values = np.asarray(event_values)[order]
    idx = np.searchsorted(event_times, sample_times, side="right") - 1
    return np.where(idx >= 0, event_values[np.clip(idx, 0, None)], initial_value)


def real_channel_state(times, mode_commands, ccd_commands, ccdsel_bits):
    """Ground-truth 'is this channel actually exposing' at each sample time, from the real
    commands: TEXPMS != 0 for that CCDSEL AND the payload is in TC_pafMODE=1 (operational) —
    matching bits of a combined CCDSEL (e.g. 127 for an all-channel flush) count too.
    """
    mode_state = step_values(times, [c[0] for c in mode_commands], [c[1] for c in mode_commands],
                              initial_value=2)
    events = [(rt, texpms != 0) for rt, ccdsel, texpms in ccd_commands if ccdsel & ccdsel_bits]
    events.sort(key=lambda e: e[0])
    channel_on = step_values(times, [e[0] for e in events], [e[1] for e in events],
                              initial_value=False)
    return (channel_on.astype(bool)) & (mode_state == 1)


def plot_world_map(lons, lats, idle_mask, lon_gate, out_path, title):
    fig = plt.figure(figsize=(12, 6))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_global()
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
    ax.add_feature(cfeature.BORDERS, linewidth=0.3)
    ax.gridlines(draw_labels=True, linewidth=0.3, linestyle="--")

    lon_min, lon_max = lon_gate
    if lon_min <= lon_max:
        ax.axvspan(lon_min, lon_max, color="tab:red", alpha=0.12, zorder=1)
    else:
        ax.axvspan(lon_min, 180, color="tab:red", alpha=0.12, zorder=1)
        ax.axvspan(-180, lon_max, color="tab:red", alpha=0.12, zorder=1)

    # Break the track into contiguous same-state runs so idle/operational segments are
    # colored separately without drawing spurious lines across the +/-180 seam. Python
    # slicing means lons[a:b] and lons[b:c] never draw the connecting line between point
    # b-1 and point b — invisible when samples are close together, but a real multi-degree
    # gap near the poles where the ground track moves fast per sample (e.g. near 100E in
    # this run). Extend color-change segments by one point to draw that connector; seam
    # breaks keep the gap on purpose (that's the true antimeridian discontinuity).
    change = set((np.where(np.diff(idle_mask.astype(int)) != 0)[0] + 1).tolist())
    seam = set((np.where(np.abs(np.diff(lons)) > 180)[0] + 1).tolist())
    breaks = sorted(change | seam | {0, len(lons)})
    for a, b in zip(breaks[:-1], breaks[1:]):
        end = b + 1 if (b in change and b not in seam and b < len(lons)) else b
        if end - a < 2:
            continue
        color = "tab:red" if idle_mask[a] else "tab:blue"
        ax.plot(lons[a:end], lats[a:end], color=color, linewidth=1.6,
                transform=ccrs.PlateCarree(), zorder=3)

    legend = [
        mpatches.Patch(color="tab:red", alpha=0.5, label=f"idle (lon_gate {lon_gate})"),
        mpatches.Patch(color="tab:blue", label="operational"),
    ]
    ax.legend(handles=legend, loc="lower left")
    ax.set_title(title)
    plt.tight_layout()
    plt.savefig(out_path, dpi=130)
    plt.close(fig)
    print("wrote", out_path)


def classify_command(rt, mode, gate_times, uv_times, nadir_times, tolerance=60):
    """Which real transition (if any) a TC_pafMODE command actually corresponds to.

    Every routine UV or Nadir CCD toggle also brackets through idle/resume (see
    Macros.Mode1), so a command's own MODE number can't tell gate crossings apart from
    routine ones — nearest-neighbour distance to each independently-simulated
    transition type can.
    """
    candidates = {
        "gate": np.min(np.abs(gate_times - rt)) if len(gate_times) else np.inf,
        "uv": np.min(np.abs(uv_times - rt)) if len(uv_times) else np.inf,
        "nadir": np.min(np.abs(nadir_times - rt)) if len(nadir_times) else np.inf,
    }
    best = min(candidates, key=candidates.get)
    if candidates[best] >= tolerance:
        return "unknown"
    # UV and Nadir can legitimately flip within the same command (Macros.Mode1 checks
    # both every call) — report "both" when the runner-up is equally close.
    others_close = [k for k, v in candidates.items() if k != best and v < tolerance]
    if best in ("uv", "nadir") and others_close and "gate" not in others_close:
        return "uv+nadir"
    return best


CCDSEL_UV = 16 | 32
CCDSEL_NADIR = 64
CCDSEL_IR = 1 | 2 | 4 | 8


def plot_timeseries(times, lons, lats, idle_mask, uv_mask, nadir_mask, mode_commands,
                     ccd_commands, lon_gate, out_path, title):
    fig, (ax1, ax2, ax3) = plt.subplots(
        3, 1, figsize=(14, 9.5), sharex=True, gridspec_kw={"height_ratios": [2, 1.3, 1.1]}
    )

    ax1.plot(times, lons, color="k", linewidth=0.8)
    lon_min, lon_max = lon_gate
    ax1.fill_between(times, -180, 180, where=idle_mask, color="tab:red", alpha=0.15,
                      step="post", label=f"lon_gate {lon_gate} (idle)")
    ax1.axhline(lon_min, color="tab:red", linestyle="--", linewidth=0.6)
    ax1.axhline(lon_max, color="tab:red", linestyle="--", linewidth=0.6)
    ax1.set_ylabel("LP longitude [deg]")
    ax1.set_ylim(-180, 180)
    ax1.legend(loc="upper right")

    ax2.plot(times, lats, color="k", linewidth=0.8)
    ax2.fill_between(times, -90, 90, where=idle_mask, color="tab:red", alpha=0.15, step="post")
    ax2.set_ylabel("LP latitude [deg]")

    # Classify each command against the independently-simulated transition times for
    # the gate, UV threshold, and Nadir day/night threshold, so the three causes of a
    # TC_pafMODE command are visually distinct instead of collapsing into "red vs green"
    # (which conflates routine single-CCD toggles with real gate crossings) or
    # overlapping into what looks like one thicker line (a UV and Nadir crossing landing
    # in the same command, since Macros.Mode1 checks both every call).
    gate_times = transition_times(idle_mask, times)
    uv_times = transition_times(uv_mask, times)
    nadir_times = transition_times(nadir_mask, times)

    kind_style = {
        "gate": {2: ("tab:red", 1.2, 0.85), 1: ("tab:green", 1.2, 0.85)},
        "uv": {2: ("tab:orange", 0.8, 0.6), 1: ("tab:orange", 0.8, 0.6)},
        "nadir": {2: ("tab:purple", 0.8, 0.6), 1: ("tab:purple", 0.8, 0.6)},
        "uv+nadir": {2: ("tab:brown", 0.9, 0.7), 1: ("tab:brown", 0.9, 0.7)},
        "unknown": {2: ("gray", 0.6, 0.4), 1: ("gray", 0.6, 0.4)},
    }

    for rt, mode, comment in mode_commands:
        kind = classify_command(rt, mode, gate_times, uv_times, nadir_times)
        color, lw, alpha = kind_style[kind][mode]
        for ax in (ax1, ax2, ax3):
            ax.axvline(rt, color=color, linewidth=lw, alpha=alpha)

    legend = [
        mpatches.Patch(color="tab:red", alpha=0.4, label="simulated idle region"),
        plt.Line2D([0], [0], color="tab:red", label="gate: TC_pafMODE=2 (idle)"),
        plt.Line2D([0], [0], color="tab:green", label="gate: TC_pafMODE=1 (resume)"),
        plt.Line2D([0], [0], color="tab:orange", alpha=0.7, label="UV threshold toggle"),
        plt.Line2D([0], [0], color="tab:purple", alpha=0.7, label="Nadir day/night toggle"),
        plt.Line2D([0], [0], color="tab:brown", alpha=0.7, label="UV + Nadir toggle together"),
    ]
    ax1.legend(handles=legend, loc="upper right", fontsize=8)

    # Third sub-figure: per-channel exposure state, from the REAL generated commands
    # (TC_pafCCD's own CCDSEL/TEXPMS, gated by the real TC_pafMODE state) rather than the
    # idealized orbit simulation — so this row shows what the instrument actually did,
    # including the ~40-50s CCD-sync-driven lag between the true crossing and the command
    # that was actually scheduled. The pink shading above (idle_mask) stays tied to the
    # ideal/physical crossing for reference, per your call to keep those separate.
    step_s = int(times[1] - times[0]) if len(times) > 1 else 15
    channel_rows = [
        ("Nadir", real_channel_state(times, mode_commands, ccd_commands, CCDSEL_NADIR), 2),
        ("UV1 / UV2", real_channel_state(times, mode_commands, ccd_commands, CCDSEL_UV), 1),
        ("IR1–IR4", real_channel_state(times, mode_commands, ccd_commands, CCDSEL_IR), 0),
    ]
    ax3.fill_between(times, -0.6, 2.6, where=idle_mask, color="tab:red", alpha=0.15, step="post")
    for _, chan_mask, y in channel_rows:
        ax3.broken_barh(mask_to_intervals(times, chan_mask, step_s), (y - 0.35, 0.7),
                         facecolors="tab:green")
    ax3.set_yticks([row[2] for row in channel_rows])
    ax3.set_yticklabels([row[0] for row in channel_rows])
    ax3.set_ylim(-0.6, 2.6)
    ax3.set_xlabel("Relative time [s]")
    ax3.legend(
        handles=[
            mpatches.Patch(color="tab:green", label="exposing (from real TC_pafCCD/TC_pafMODE commands)"),
            mpatches.Patch(color="tab:red", alpha=0.3, label="idealized idle region (for reference)"),
        ],
        loc="upper right", fontsize=8,
    )

    fig.suptitle(title)
    plt.tight_layout()
    plt.savefig(out_path, dpi=130)
    plt.close(fig)
    print("wrote", out_path)


def main():
    if len(sys.argv) < 4:
        print("Usage: python plot_longitude_gate.py <config.json> <xml_path> <out_prefix> [start_date] [duration_hours] [TLE1] [TLE2]")
        sys.exit(1)

    config_path, xml_path, out_prefix = sys.argv[1:4]
    start_date_str = sys.argv[4] if len(sys.argv) > 4 else None
    duration_hours = float(sys.argv[5]) if len(sys.argv) > 5 else 6.0
    # Must match the TLE actually used to generate xml_path — the config's own
    # baked-in TLE1/TLE2 is typically a stale placeholder overridden at generation
    # time (see generate_operational_mode's tle= argument), so re-simulating
    # without passing the same TLE here silently diverges from the real orbit.
    tle1 = sys.argv[6] if len(sys.argv) > 6 else None
    tle2 = sys.argv[7] if len(sys.argv) > 7 else None

    with open(config_path) as f:
        raw_cfg = json.load(f)

    if tle1 is None:
        print("WARNING: no TLE1/TLE2 given — falling back to the config's own baked-in "
              f"TLE1={raw_cfg.get('TLE1')!r}, which is very likely a stale placeholder "
              "unless that's genuinely what generated xml_path. Pass the TLE used at "
              "generation time as the 6th/7th arguments to get a trustworthy comparison.")

    cfg = configFile.configFile(config_path, start_date_str, TLE1=tle1, TLE2=tle2)
    lon_gate = cfg.Operational_Science_Mode_settings()["lon_gate"]
    lat_threshold = cfg.Operational_Science_Mode_settings()["lat"]
    start_date = DT.datetime.strptime(cfg.Timeline_settings()["start_date"], "%Y/%m/%d %H:%M:%S")

    times, lons, lats, sun_angles = simulate_ground_track(cfg, start_date, int(duration_hours * 3600))
    idle_mask = np.array([check_lon(lon, lon_gate) for lon in lons])
    uv_mask = np.array([check_lat(lat, lat_threshold) for lat in lats])
    nadir_mask = sun_angles > NADIR_ECLIPSE_ANGLE

    mode_commands = parse_mode_commands(xml_path)
    ccd_commands = parse_ccd_commands(xml_path)

    label = f"{raw_cfg['ID']}_{raw_cfg['name']} — {start_date:%Y-%m-%d %H:%M} UTC, lon_gate={lon_gate}"
    plot_world_map(lons, lats, idle_mask, lon_gate, out_prefix + "_map.png", label)
    plot_timeseries(times, lons, lats, idle_mask, uv_mask, nadir_mask, mode_commands,
                     ccd_commands, lon_gate, out_prefix + "_timeseries.png", label)


if __name__ == "__main__":
    main()
