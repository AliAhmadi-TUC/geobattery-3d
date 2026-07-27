#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FIG 6 for the web lab, stepped over the whole annual cycle.

The printed panel shows one phase three ways (total, thermally induced,
geostatic).  The lab can afford four solves, so it shows the more useful thing:
TOTAL von Mises at the end of each of the four phases, with the geostatic field
as the reference it is measured against.  The thermally induced increment is
dropped because it is total minus geostatic, which a reader can now see
directly by stepping the slider.

Geometry is fig07_stress.near_drift() exactly as the paper builds it — a 3 m
sleeve of rock+concrete around the wetted wall, sliced open at drift_frame
z_open.  One thermoelastic solve per phase; fig07's cache is keyed on the
temperature file, so a phase already computed is reused.

Writes geobattery-3d/data/fig6/{sleeve.vtp, meta.json}.
Run:  ~/anaconda3/envs/fenicsx-073/bin/python export_fig6_phases.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

import config as C
import render_common as rc
import fig07_stress as F7

OUT = Path(__file__).resolve().parent.parent / "geobattery-3d" / "data" / "fig6"

PHASES = [("y01_p0_charge", "charge"), ("y01_p1_store", "store"),
          ("y01_p2_discharge", "discharge"), ("y01_p3_recover", "recover")]
LABELS = {"vm_geo": "geostatic σvM · before any heat",
          "charge": "total σvM · end of charge",
          "store": "total σvM · end of storage",
          "discharge": "total σvM · end of discharge",
          "recover": "total σvM · end of recovery"}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    geo_path = C.RUN_DIR / "_geostatic" / "u_geo_solid.npy"
    if not geo_path.exists():
        raise SystemExit(f"missing {geo_path}")

    rc.start_headless()
    mesh, ct, ft = rc.load_domain()
    frame = rc.drift_frame(mesh, ct)
    water = rc.grid_for_regions(mesh, ct, [rc.TAG_WATER])
    water_surf = water.extract_surface().triangulate()

    driver = F7.load_driver()
    solid_cells = np.sort(np.concatenate(
        [ct.find(t) for t in driver.SOLID_TAGS])).astype(np.int32)
    dom_solid = driver._extract_submesh_from_cells(mesh, ct, ft, solid_cells, [])

    sleeve = None
    cells = {}                      # array name -> per-cell MPa on the sleeve
    for stem, name in PHASES:
        T_path = C.RUN_DIR / stem / "end_state" / "T.npy"
        if not T_path.exists():
            print(f"[fig6] {name}: no T.npy, skipped")
            continue
        t0 = time.time()
        F = F7.compute_fields(T_path, geo_path, use_cache=True)
        grid, _ = F7.solid_grid(F, dom_solid.mesh)
        near = F7.near_drift(grid, water_surf, frame)
        if sleeve is None:                      # the clip is identical every time
            sleeve = near
            cells["vm_geo"] = np.asarray(near.cell_data["vm_geo"], float)
        cells[name] = np.asarray(near.cell_data["vm_tot"], float)
        print(f"[fig6] {name:<10s} {near.n_cells} cells, "
              f"max {cells[name].max():6.2f} MPa, {time.time()-t0:5.1f} s",
              flush=True)

    if sleeve is None:
        raise SystemExit("no phase produced a field")

    # Colour limits: the 99.9th VOLUME percentile, as fig07 uses — a count
    # percentile lets sliver cells on a surveyed wall set the map. Every TOTAL
    # panel shares one limit so the four phases are comparable at a glance;
    # geostatic keeps its own, because it is a different quantity.
    vol = np.asarray(sleeve.compute_cell_sizes(
        length=False, area=False, volume=True).cell_data["Volume"], float)
    p999 = {k: float(F7.volume_percentile(v, vol, 0.999)) for k, v in cells.items()}
    tot_max = max(p999[n] for _, n in PHASES if n in p999)
    clim = {k: [0.0, p999["vm_geo"] if k == "vm_geo" else tot_max] for k in cells}

    for k in cells:
        sleeve.cell_data[k] = cells[k]
    surf = sleeve.extract_surface().triangulate().cell_data_to_point_data()
    for arr in list(surf.point_data.keys()):
        if arr not in cells:
            del surf.point_data[arr]
    for arr in list(surf.cell_data.keys()):
        del surf.cell_data[arr]
    f = OUT / "sleeve.vtp"
    surf.save(f, binary=True)
    print(f"[fig6] sleeve.vtp: {surf.n_cells} cells, {surf.n_points} pts, "
          f"{f.stat().st_size/1e6:.2f} MB, arrays {sorted(surf.point_data.keys())}")
    for k in cells:
        print(f"[fig6] {k:<10s} p99.9 = {p999[k]:6.2f} -> clim 0..{clim[k][1]:.2f} MPa")

    order = ["vm_geo"] + [n for _, n in PHASES if n in cells]
    meta = dict(
        z_open=float(frame["z_open"]), sleeve_m=float(F7.SLEEVE_M),
        cam_dir=[0.62, 0.78, -0.55], zoom=1.42,
        panels=order, panel_label={k: LABELS[k] for k in order},
        clim=clim, p999=p999,
        bounds=[float(v) for v in np.asarray(surf.bounds, float)],
        cells=int(surf.n_cells), points=int(surf.n_points),
    )
    (OUT / "meta.json").write_text(json.dumps(meta, indent=1))
    print(f"[fig6] -> {OUT}")


if __name__ == "__main__":
    main()
