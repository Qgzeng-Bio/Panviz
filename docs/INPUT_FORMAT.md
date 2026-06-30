# Panviz input format

Panviz renders one **locus package** per figure. An *input root* is a directory
that holds one sub-directory per locus:

```text
<input_root>/
└── <locus_id>/
    ├── <locus_id>_pathcollapsed_SV1kb.gfa
    ├── <locus_id>_pathcollapsed_SV1kb.path_groups.tsv
    └── region.txt
```

Discovery requires **exactly one** `*_pathcollapsed_SV1kb.gfa`, **one**
`*_pathcollapsed_SV1kb.path_groups.tsv`, and a `region.txt` in each locus
directory. A complete, runnable example lives in
[`examples/toy_data/toy_locus/`](../examples/toy_data/toy_locus).

Validate any input root with:

```bash
panviz validate --input-root <input_root>
```

---

## 1. `*_pathcollapsed_SV1kb.gfa` — graph (GFA 1.0)

Panviz reads **segment (`S`)** and **path (`P`)** lines; header (`H`) and link
(`L`) lines are ignored.

### Segment lines

```text
S	<name>	<sequence|*>	[tags...]
```

- `<name>` — node id (string).
- `<sequence>` — may be `*`; the node width comes from `LN` (below), not the
  literal sequence.
- Tags (tab-separated `KEY:TYPE:VALUE`) read into node metadata:
  - `LN:i:<int>` — node length (bp). Falls back to `len(sequence)` if absent.
  - `TYPE:Z:<str>` — variant type label (e.g. `DEL`, `INS`, `SNP`, `REF`).
  - `SVLEN:i:<int>` — signed SV length.
  - `CO:Z:<str>` — coordinate annotation.

### Path lines

```text
P	<path_name>	<seg1±,seg2±,...>	<overlaps>	[tags...]
```

- `<path_name>` — haplotype / collapsed-path name. A path named **`Ref`** is the
  reference: it is sorted first, gets `indexOfFirstBase = 1`, and anchors the top
  genomic axis.
- segment list — comma-separated tokens, each a segment name plus orientation
  `+` (forward) or `-` (reverse), e.g. `bb00+,bb01+,delX+`.
- `<overlaps>` — standard GFA overlaps field (usually `*`); not used by Panviz.
- `CN:i:<int>` — fallback collapsed member count if the path is absent from the
  path-groups table.

## 2. `*_pathcollapsed_SV1kb.path_groups.tsv` — haplotype frequencies

Tab-separated, with a header row. Columns:

| Column | Required | Meaning |
| --- | --- | --- |
| `locus` | no | locus id (informational) |
| `collapsed_path` | **yes** | matches a `P` path name in the GFA |
| `n_members` | no (default 1) | number of accessions collapsed into this path; sets the haplotype's frequency/weight |
| `representative_member` | no | a representative sample id |
| `members` | no | comma-separated sample ids |

`n_members` drives each haplotype ribbon's weight in the figure.

## 3. `region.txt` — genomic coordinates

`key=value` lines. Two keys are required:

```text
reference_coordinate=<chrom>:<start>-<end>
recommended_SequenceTubeMap_region=<chrom>:<start>-<end>
```

- `reference_coordinate` — 1-based genomic span of the reference path; drives the
  top axis endpoint labels (e.g. `1.234 Mb` … `1.260 Mb`).
- `recommended_SequenceTubeMap_region` — the rendered window `[start, end]`.

Other lines are ignored.

---

## Minimal example

See [`examples/`](../examples). Regenerate the toy package with:

```bash
python3 examples/generate_toy.py
```

Then render it (see [FIGURE_ANATOMY.md](FIGURE_ANATOMY.md) for the result):

```bash
panviz render --config config/mainfig_baseline.json \
  --input-root examples/toy_data --only toy_locus --out-root results/toy
```
