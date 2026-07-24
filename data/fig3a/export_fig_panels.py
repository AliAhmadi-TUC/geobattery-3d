#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Export the printed panels' OWN geometry for the web lab.

The lab cannot reproduce FIG 3A by posing its generic surfaces: the panel is a
7 m sleeve of rock around the wetted wall, sliced at z_open, with the cut face
carrying the temperature field and the distance-to-wall used for the 3.87 m
markers.  None of that exists as a loadable body — it is built by
fig06_thermal_plume.build_geometry and then thrown away when the PNG is
written.  So build it here with the SAME call and write it out, rather than
approximating it with a full-domain slice of a 236 x 294 x 206 m block.

Writes, into geobattery-3d/data/fig3a/:
    face.vtp        the cut face at z_open: per-phase T + implicit distance
    rock_body.vtp   the sleeve below the cut (surface of it)
    conc_body.vtp   the concrete plugs below the cut
    water.vtp       the water body surface, per-phase T
    outline.vtp     the drift outline on the face
    meta.json       z_open, clim, camera yaw/elev, phase names, bounds

Run:  ~/anaconda3/envs/fenicsx-073/bin/python export_fig_panels.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pyvista as pv

import config as C
import render_common as R
import fig06_thermal_plume as F6

OUT = Path(__file__).resolve().parent.parent / "geobattery-3d" / "data" / "fig3a"


def _surface(grid):
    """A grid -> its triangulated boundary surface, point data preserved."""
    if grid is None:
        return None
    s = grid.extract_surface() if hasattr(grid, "extract_surface") else grid
    return s.triangulate()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    R.start_headless()
    mesh, ct, _ = R.load_domain()

    fields = F6.load_phase_fields(C.RUN_DIR)
    if not fields:
        raise SystemExit(f"no phase fields under {C.RUN_DIR}")
    print(f"[export] phases: {list(fields)}")

    geo = F6.build_geometry(mesh, ct, fields)
    z_open = float(geo["z_open"])

    parts = {
        "face": geo["face"],                 # already a surface (a slice)
        "outline": geo["outline"],           # polyline
        "rock_body": _surface(geo["rock_body"]),
        "conc_body": _surface(geo["conc_body"]),
        "water": _surface(geo["water"]),
    }

    written = {}
    for name, part in parts.items():
        if part is None or part.n_points == 0:
            print(f"[export] {name}: empty, skipped")
            continue
        # keep only what the lab reads: the phase temperatures and the wall distance
        keep = set(fields) | {"implicit_distance"}
        for arr in list(part.point_data.keys()):
            if arr not in keep:
                del part.point_data[arr]
        for arr in list(part.cell_data.keys()):
            del part.cell_data[arr]
        f = OUT / f"{name}.vtp"
        part.save(f, binary=True)
        written[name] = dict(cells=int(part.n_cells), points=int(part.n_points),
                             arrays=sorted(part.point_data.keys()),
                             bytes=f.stat().st_size)
        print(f"[export] {name}: {part.n_cells} cells, {part.n_points} pts, "
              f"{f.stat().st_size/1e6:.2f} MB, arrays {sorted(part.point_data.keys())}")

    # the printed panel titles each quote the VOLUME-mean water temperature
    # ("end of charge · water 66 °C"), not a point mean — the wall region is the
    # most finely meshed and the coldest, so an unweighted mean under-reads it.
    wmean = {n: float(F6.water_mean_T(geo["water"], n)) for n in fields}
    label = {n: lab for _, n, lab, _ in F6.PHASES}
    day = {n: float(d) for _, n, _, d in F6.PHASES}
    for n in fields:
        print(f"[export] {n:<10s} volume-mean water T = {wmean[n]:6.2f} °C  ({label.get(n,'')})")

    b = np.asarray(parts["face"].bounds, float)
    meta = dict(
        z_open=z_open,
        sleeve_m=float(F6.SLEEVE_M), depth_m=float(F6.DEPTH_M),
        elev_deg=float(F6.ELEV_DEG), yaw_deg=0.0, zoom=float(F6.ZOOM),
        clim=[float(C.T_INITIAL), float(C.T_HOT)],
        cmap_gamma=float(F6.CMAP_GAMMA),
        delta_m=float(C.penetration_depth(C.PHASE_DAYS["store"] * C.DAY)),
        phases=list(fields),
        water_mean={n: wmean[n] for n in fields},
        phase_label={n: label.get(n, n) for n in fields},
        phase_day={n: day.get(n, 0.0) for n in fields},
        bounds=[float(v) for v in b],
        parts=written,
    )
    (OUT / "meta.json").write_text(json.dumps(meta, indent=1))
    print(f"[export] meta: z_open={z_open:.4f} m, clim={meta['clim']}, "
          f"delta={meta['delta_m']:.3f} m, elev={meta['elev_deg']}")
    print(f"[export] -> {OUT}")


if __name__ == "__main__":
    main()
