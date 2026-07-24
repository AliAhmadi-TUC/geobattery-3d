#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Export FIG 6's own geometry for the web lab — same move as export_fig_panels.

fig07_stress renders a 3 m sleeve of rock+concrete around the wetted wall,
sliced open at drift_frame z_open, and colours it three ways on a shared
camera: the geostatic field, the total at end of charge, and the thermally
induced increment.  The lab has no von Mises volume at all — only surface
arrays — so it cannot pose this: the closest it manages is stress on the
wetted wall, which is a different picture.  Build the real thing here with
fig07's own near_drift() and write it out.

The thermoelastic solve is cached in data/fig07_stress_fields.npz, so this
does not re-run a 100k-dof factorisation unless the inputs changed.

Writes, into geobattery-3d/data/fig6/:
    sleeve.vtp   the sliced sleeve surface, carrying vm_geo / vm_tot / vm_th
    meta.json    z_open, per-panel clims, camera direction/zoom, labels

Run:  ~/anaconda3/envs/fenicsx-073/bin/python export_fig6_panel.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import config as C
import render_common as rc
import fig07_stress as F7

OUT = Path(__file__).resolve().parent.parent / "geobattery-3d" / "data" / "fig6"

# what the printed panels are, in order
PANELS = [
    ("vm_tot", "(a) total σvM, end of charge"),
    ("vm_th",  "(b) thermally induced Δσ"),
    ("vm_geo", "(c) geostatic σvM"),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    run_dir = C.RUN_DIR
    T_path = run_dir / "y01_p0_charge" / "end_state" / "T.npy"
    geo_path = run_dir / "_geostatic" / "u_geo_solid.npy"
    for p in (T_path, geo_path):
        if not p.exists():
            raise SystemExit(f"missing {p}")

    F = F7.compute_fields(T_path, geo_path, use_cache=True)

    rc.start_headless()
    mesh, ct, ft = rc.load_domain()
    frame = rc.drift_frame(mesh, ct)
    water = rc.grid_for_regions(mesh, ct, [rc.TAG_WATER])
    water_surf = water.extract_surface().triangulate()

    driver = F7.load_driver()
    solid_cells = np.sort(np.concatenate(
        [ct.find(t) for t in driver.SOLID_TAGS])).astype(np.int32)
    dom_solid = driver._extract_submesh_from_cells(mesh, ct, ft, solid_cells, [])
    grid, full = F7.solid_grid(F, dom_solid.mesh)
    print(f"[fig6] solid grid: {grid.n_cells} cells")

    sleeve = F7.near_drift(grid, water_surf, frame)
    print(f"[fig6] sleeve: {sleeve.n_cells} cells "
          f"(SLEEVE_M = {F7.SLEEVE_M} m, cut at z_open = {frame['z_open']:.4f} m)")

    surf = sleeve.extract_surface().triangulate()
    # cell data -> point data so a web mapper can interpolate it like any field
    surf = surf.cell_data_to_point_data()
    keep = {k for k, _ in PANELS}
    for arr in list(surf.point_data.keys()):
        if arr not in keep:
            del surf.point_data[arr]
    for arr in list(surf.cell_data.keys()):
        del surf.cell_data[arr]
    f = OUT / "sleeve.vtp"
    surf.save(f, binary=True)
    print(f"[fig6] sleeve.vtp: {surf.n_cells} cells, {surf.n_points} pts, "
          f"{f.stat().st_size/1e6:.2f} MB, arrays {sorted(surf.point_data.keys())}")

    # The printed colour limits are the 99.9th VOLUME percentile over the sleeve
    # CELLS — not a point percentile over its surface, which is what I reached for
    # first and which reads 61 MPa against the panel's 30. fig07 says why: "on a
    # surveyed wall a count percentile still lets sliver cells set the map".
    # (a) and (b) then share vm_tot's limit so the eye compares like with like;
    # (c) has its own, as the caption states.
    near_vol = np.asarray(sleeve.compute_cell_sizes(
        length=False, area=False, volume=True).cell_data["Volume"], float)
    p999 = {k: float(F7.volume_percentile(sleeve.cell_data[k], near_vol, 0.999))
            for k in ("vm_geo", "vm_tot", "vm_th")}
    clim = {"vm_tot": [0.0, p999["vm_tot"]],
            "vm_th":  [0.0, p999["vm_th"]],
            "vm_geo": [0.0, p999["vm_tot"]]}      # (a) and (c) on the shared scale
    for key, _ in PANELS:
        v = np.asarray(surf.point_data[key], float)
        print(f"[fig6] {key:<7s} surface {np.nanmin(v):7.2f} .. {np.nanmax(v):7.2f} MPa"
              f" | volume p99.9 = {p999[key]:6.2f} -> clim {clim[key][1]:6.2f}")

    b = np.asarray(surf.bounds, float)
    meta = dict(
        z_open=float(frame["z_open"]),
        sleeve_m=float(F7.SLEEVE_M),
        cam_dir=[0.62, 0.78, -0.55],      # rc.camera_three_quarter
        zoom=1.42,
        panels=[k for k, _ in PANELS],
        panel_label={k: lab for k, lab in PANELS},
        clim=clim,
        p999={k: p999[k] for k in p999},
        bounds=[float(v) for v in b],
        cells=int(surf.n_cells), points=int(surf.n_points),
    )
    (OUT / "meta.json").write_text(json.dumps(meta, indent=1))
    print(f"[fig6] -> {OUT}")


if __name__ == "__main__":
    main()
