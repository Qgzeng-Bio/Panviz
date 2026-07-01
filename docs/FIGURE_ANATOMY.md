# Panviz figure anatomy

Panviz renders a static, publication-oriented **sequence tube map**: a reference
genomic axis on top, with haplotype paths drawn as colored ribbons weaving
through shared nodes. The figure below is the bundled toy locus (reproducible
with `examples/generate_toy.py`).

![Panviz toy locus tube map](../examples/toy_locus.png)

## Anatomy

| Element | SVG class / cue | Description |
| --- | --- | --- |
| **Title** | text | `chrom:start-end` in Mb (e.g. `chrTOY:1.23-1.26 Mb`). |
| **Genomic axis** | `genomic-axis` | Top ruler with short upward ticks and endpoint coordinate labels (e.g. `1.234 Mb` … `1.260 Mb`). |
| **Reference ribbon** | first track (`Ref`) | The reference path, drawn first (blue) along the top. |
| **Haplotype ribbons** | `track` | One colored ribbon per collapsed path; weight reflects `n_members`. |
| **Nodes** | `node` | White rounded rectangles; width is proportional to node length, horizontally compressed by `x_compression`; stroke width `1.5`. |
| **Scale bar** | `genomic-scale-bar` | Lower-left physical scale (e.g. `5 kb`). |

## Reading structural variants

- **Deletion** — a ribbon dips down and **bypasses** a node that the reference
  passes through (here `delX`).
- **Insertion** — an extra node that only some ribbons enter, while others skip
  it (here `insY`).
- **Substitution / alternate allele** — ribbons **cross** to an alternate node at
  the same position (here `subR` ↔ `subA`).

The toy locus contains one of each, plus a haplotype combining all three.

## Annotating variant nodes (optional)

Pass `--annotate-sv` (or set `annotate_sv: true` in a config file) to label each
variant node with its type and size, e.g. `INS +10.8 kb`, `DEL -3.0 kb`,
`SNP 1.8 kb`:

```bash
panviz render --config config/mainfig_baseline.json --annotate-sv \
  --input-root /path/to/loci --only my_locus --out-root results/my_locus
```

- Only non-reference nodes (those with a `TYPE` other than `REF`) are labelled.
- The label is `TYPE ±size`; the size is the signed `SVLEN` (falling back to the
  segment length), formatted as `kb`/`bp`.
- Each label sits one ribbon-height above its node box (a white halo keeps it
  legible where it overlaps the ribbon band). The label is real SVG text —
  selectable and searchable in the vector output.

This is off by default, so the accepted baseline rendering is unchanged.

## Output files

Each render writes, per locus, into `<out_root>/<locus>/`:

| File | Format | Notes |
| --- | --- | --- |
| `*_natural.svg` | SVG | Vector master; text and strokes are **not** non-uniformly scaled (no `preserveAspectRatio="none"`). |
| `*_natural.pdf` | PDF | Vector, for manuscripts. |
| `*_natural.png` | PNG | Raster at `device_scale_factor` (default 2×): a 1800-px panel exports at 3600 px wide. |
| `*_input.json` | JSON | The render payload (graph + tracks + parameters). |
| `*_render_metadata.json` | JSON | Counts, coordinates, and parameters used. |
| `*_path_group_key.tsv` | TSV | Haplotype → member mapping. |

## Visual parameters (baseline)

Defaults in `config/mainfig_baseline.json` reproduce the accepted baseline:

| Parameter | Default | Effect |
| --- | --- | --- |
| `panel_width` | `1800` | Final CSS-pixel width of the panel. |
| `x_compression` | `0.32` | Horizontal compaction of node widths. |
| `pad_x` / `pad_y` | `35` / `170` | Padding around the panel (viewBox margins). |
| `node_stroke_width` | `1.5` | Node outline thickness. |
| `device_scale_factor` | `2.0` | PNG raster multiplier. |

Changing any of these alters the figure; update `tests/baseline/` and
`CHANGELOG.md` if a change is intended (see the regression check in
[`tests/`](../tests)).
