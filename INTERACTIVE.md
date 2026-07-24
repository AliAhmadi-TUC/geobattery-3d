# The interactive poster — build notes

`/poster/index.html` is the ALERT 2026 A0 poster shown as an image with clickable figure
hotspots; each opens a modal that rebuilds that figure as a live instrument. `/index.html`
is the vtk.js 3-D lab, which the poster deep-links into. Both are single self-contained
files: hand-written SVG/canvas, no libraries, no build step.

---

## 1 · What each figure is

| hotspot | opens | what it is |
|---|---|---|
| FIG 1 | `m-solar` | The 2023 metered record — **8760 hourly values** of 50 Hz-zone PV and load, packed as two little-endian uint16 base64 blobs. Three bands on one calendar axis (daily PV + storable, HDD mirrored, an hour×day heat map). Drag the charge/discharge windows; the gap between them **is** t_store → Fo → RF. Drag the red `f` tab to redefine surplus (PV above f×load). |
| FIG 2 | lab `?fig=cutaway` | The drift as the printed panel renders it. **Not a clip** — a translucent slab built around the geometry, parts named with leader lines, parallel projection. |
| FIG 3A/3B/6 | lab `?fig=plume/flow/stress` | Figure-match presets: white background, printed field + cut + camera. |
| FIG 4a | `m-screening` | The **admissibility plane**. Every iso-retention level is exactly a straight line (Fo = α·t·a²/4 ⇒ log Fo affine in log a, log t), so the whole field is one SVG linear gradient. Draggable puck = your mine; a tab moves the acceptance target. |
| FIG 4b | `m-grade` | **The pipe and the bill.** x = net heat delivered, y = outlet temperature, so pipe length is quantity and height is grade. The compressor bill is the *area* between your pipe and the free (undisturbed-rock) pipe. |
| FIG 5 (one hotspot, was 5a+5b) | `m-decade` | **The store and the ledger.** A vessel (rock, water, tap) beside ten strata, one per cycle: height = heat injected, width = share returned ⇒ **area is energy**. Ground heat grows *leftward out of the rock*. |
| §07 A/B/C | `m-num` | Three **general theorems**, each ONE free-running 12 s loop in the DrSimulate-gallery style (dark ground, red = wrong, green = right, yellow = the quantity, no interface — no sliders, no beats, no play button). Drag-to-orbit stays live while the loop plays. Below each canvas: a static equation strip and a 3-line "where this project meets it" note. A: the mesh refines 2-4-8-16 forever — the slope-flux arrow moves every rung (real P1 solver output: 50→6.25 % overshoot), the reaction arrow never moves. B: heat glides along a blank sealed wall, then `T = T₀` types itself onto the wall and it bleeds; erasing it reseals. C: nudges on a bowl both return; the constraint line draws itself, the bowl folds into a saddle, the same nudges repeat and one runs away; λmin slides across zero. One shared RAF clock drives only the visible pane and stops itself when the modal closes; `prefers-reduced-motion` gets a single representative frame at t = 7.9 s. |

---

## 2 · Verified identities and constants

These were each checked against the project's own outputs; do not re-derive by hand.

- **θ ≡ RF_abs.** The dimensionless water temperature (T_w−T₀)/(T_hot−T₀) is *identical* to
  cumulative retention, to 9 decimals, for every configuration and cycle. FIG 4a and 4b
  therefore read one table.
- **Retention is exactly independent of T₀ and T_hot** (< 2×10⁻¹⁴ over T₀ = 0…40 °C). The
  problem is linear; quantity and grade are orthogonal.
- **Scale invariance is exact**: L_c×λ with t×λ² gives bit-identical RF (λ = 1, 3, 10).
- **κ matters at matched Fo** — up to 64 % spread; χ adds 10–23 %. A one-parameter collapse
  genuinely fails, which is why the criterion needs all three groups.
- **The criterion is a formula**: a_max = 2√(Fo*/(α·t_store)), so a_max ∝ t^(−1/2) — a straight
  line of slope −½ on log–log axes. Reproduces L_c,min = 3.405 m for gneiss.
- **α_rock = 2.8129395218e-7 × κ** exactly (ρc held fixed), so no α table is needed.
- **FIG 4b: 1 px² = 27.17 kWh·K**, i.e. 179 Wh of compressor work at a 30 °C header.
  Integrating the drawn pixels reproduces the step-by-step COP integral to <1 kWh.
- **FIG 5: 38.48 px² per MWh**, identical across all five scenarios.
- **Discharge energy is NET**, −(Ein+Eout): outflow minus the enthalpy the 10 °C injection
  carries in. Gross |Eout| overstates the 30 °C run by **52.6 %**. The net matches
  `recovered_kWh` in `decadal_*.json` exactly and is monotone.

## 2b · Where the geometry came from

The drift is not drawn — it is **surveyed**, and every figure in this poster inherits that.
Recorded from `GrazPaper/sections/02_methodology_compact.tex` (a separate paper on the same
scan), because the provenance is not written down anywhere in this repo.

**Site.** "Reiche Zeche" research and education mine, Freiberg — TU Bergakademie Freiberg since
1919, ~19 km of drifts to 230 m depth. The region of interest is on **Sohle 1, 147 m depth**:
irregular walls typical of historical mining, which is exactly why the wetted area is what it is
and why a smooth cylinder would be the wrong idealisation.

**Acquisition.** A **Z+F FlexScan 22** mobile mapping platform running as an extension unit on a
**Z+F IMAGER 5016A** laser scanner with SLAM. Two overlapping clouds, processed in Z+F
LaserControl (preprocessing → trajectory optimisation → 3-D filtering), registered by **ICP**
(Besl & McKay 1992) minimising Σ‖R·p_i + t − q_i‖², then subsampled to **1 cm**.

**Surface.** Screened Poisson reconstruction (Kazhdan & Hoppe 2013) in MeshLab at **octree depth
10**, then isotropic remeshing. The Graz paper remeshes at four edge lengths — 5, 9, 20 and 50 cm
— because resolution is *its* subject. **This project uses the 20 cm surface only**; the other
three are that study's convergence ladder and appear nowhere here. The structured hexahedral mesh
is likewise theirs alone, used only for round-trip transfer-error analysis, and is a
geometrically distinct mesh rather than a coarser variant.

**Volume.** Gmsh, each surface embedded in a cuboidal host-rock domain **expanded by 100 m**,
constrained Delaunay tetrahedralisation with Netgen optimisation. That 100 m is the same
far-field buffer the poster's KEY QUANTITIES card quotes.

The Graz volumetric counts, for the record — again, only the 20 cm row is this project's lineage:

| edge length | nodes | elements | |
|---|---|---|---|
| 5 cm | 296,019 | 1,471,842 | Graz only |
| 9 cm | 75,171 | 379,254 | Graz only |
| **20 cm** | **20,307** | **103,489** | **the surface this project uses** |
| 50 cm | 3,664 | 19,320 | Graz only |

This project's own mesh, `volume_mesh_with_mountain_retagged_named.msh`, reads **40,679 nodes /
273,794 elements** — larger than the 20 cm row above, which is what you would expect once the
mirrored air and concrete regions are carried alongside the surveyed water body.

**The one caveat that matters for the figures.** In the Graz work the *original* mesh is used —
water region only. In this project's mesh the **air and concrete regions are produced by
mirroring the surveyed geometry**, not scanned. So the water body and the rock wall are survey;
the air-filled ends and the plugs are construction. Worth remembering before describing any part
of FIG 2 as "measured".

## 3 · Data generation

- `poster_ALERT2026/make_rf_table.py` → `data/rf_field.json`. **Two** tables, deliberately:
  A = first-cycle RF over (Fo, κ) 64×24 dense (n_phases=1 is ~50 ms, so density is cheap);
  B = cumulative θ over (Fo, R_far/L_c, cycle) 44×16×10 at κ=5 only.
  A first attempt used one coarse 4-D grid and was **48 % wrong** on the 10 m-pitch decade,
  because R_far/L_c was interpolated across the saturation knee. Refine that axis, and store
  θ (bounded) rather than the marginal ratio (unbounded — it exceeds 1 once the cell saturates).
- Discharge curves: `run_decade_<scenario>/yNN_p2_discharge/metrics.csv`, 186 steps.
- Geothermal split: `scenario_comparison.json → decomposition` (exact by linearity; its own
  published residual drifts 1.6 % → 11 % by year 10, so quote it to a few percent).

---

## 4 · Traps that have actually bitten

**Balance is not parseability.** Two separate whole-script killers shipped past a green
bracket/quote check:
- `*/` inside a block comment (in the text `run_decade_*/…`) closed the comment early;
- `''` inside a single-quoted string (`solver''s`) ended the literal and left two adjacent
  literals — a SyntaxError.
A SyntaxError anywhere in an inline `<script>` means **the whole block never runs**, so every
figure dies at once. Use a real parser: `pip install esprima`, then `esprima.parseScript`.
It is ES2017, so `??` and `?.` are false positives — check those by eye.

**Parseability is not runnability either.** `const NC` in §07 collided with an existing `NC`
bound as a *second declarator* of a multi-name const in FIG 4 (`const NF=…, NR=…, NC=RFB.nc;`)
— the browser threw `Identifier 'NC' has already been declared` and the whole block died.
esprima accepts this (redeclaration is a binder early-error, not a parse error), and a
line-anchored `^const NAME` dup scan misses names on continuation lines. Before adding a
top-level name, grep for `\bNAME\b` across the file and for the comma form `, NAME=`.

**A missing definition looks like several unrelated faults.** Removing `FEM_A` made `updA()`
throw, the exception escaped to top level, and every later statement — the whole of tabs B
and C — never executed. Tab A's canvas still drew, because it was built before the throw.
When replacing a region of the file, list what definitions lived inside it.

**Diagnostics are in the page and should stay.** `mini3d.draw()` wraps `build()` in try/catch
and paints the exception on the canvas; a `window.error` handler shows any script error in a
bar at the foot of the page. That bar turned three rounds of guessing into a one-line fix.

**TDZ:** `typeof X` does *not* protect a `const` in the temporal dead zone — it throws. Hoist
to `let X=null` if a function that runs earlier references it.

**Splices:** assert `a < b` before `s[:a] + new + s[b:]`. Getting that backwards once
duplicated 36 kB including a second `const DIS`, a redeclaration that would have killed the
script. Also scan for duplicate top-level `const`s afterwards.

**Deploys — use the Actions API, not `/pages/builds`.**
`gh api repos/OWNER/REPO/actions/runs` tells the truth; `/pages/builds` reported `building`
against a stale commit for 30 minutes while the run had already **failed**. Builds can fail on
a transient artifact-storage **403 at finalize**; re-running failed jobs only re-queues and can
stall indefinitely — **push an empty commit** to get a fresh run instead.
Verify a deploy by grepping the *served* page for a string unique to the new build, or by
comparing served bytes to committed bytes. Never by commit SHA.

**Cache:** Pages sends `max-age=600`. `poster/index.html` holds `const LABV` and static
`?b=` tags on every lab link — **bump them whenever the lab is redeployed**, or a return visit
serves the previous build.

**FIG 2 colour matching:** the printed figure is PyVista PBR + cubemap + a four-light rig, so
`config.PV_MATERIALS` are *base* colours that render far lighter. Sample the rendered PNG
instead (water `#73b5d3`, slab `#bec0c4`) and solve for the base through this renderer's
shading and the slab's alpha. Never call `setAmbientColor(1,1,1)` — `setColor()` already sets
it, and forcing white makes `ambient` a white-light term that washes the material out.
