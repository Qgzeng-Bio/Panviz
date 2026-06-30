# Panviz examples

A self-contained toy locus so anyone can run Panviz end-to-end without any
private data.

```text
examples/
├── generate_toy.py            # regenerates the toy package (deterministic)
├── toy_data/toy_locus/        # the input locus package
│   ├── toy_locus_pathcollapsed_SV1kb.gfa
│   ├── toy_locus_pathcollapsed_SV1kb.path_groups.tsv
│   └── region.txt
└── toy_locus.png              # expected rendered figure (preview)
```

The toy graph is a reference backbone plus three structural variants: a
**deletion** (`delX`), a **substitution** (`subR` ↔ `subA`), and an
**insertion** (`insY`), sampled across a reference and five haplotype paths.

## Run it

```bash
cd /path/to/Panviz

# (optional) regenerate the input package
python3 examples/generate_toy.py

# render
python3 bin/panviz render --config config/mainfig_baseline.json \
  --input-root examples/toy_data --only toy_locus --out-root results/toy

# open results/toy/toy_locus/toy_locus_sequencetubemap_mainfig_natural.svg
```

The expected output is shown in [`toy_locus.png`](toy_locus.png) and explained in
[`../docs/FIGURE_ANATOMY.md`](../docs/FIGURE_ANATOMY.md). Input file formats are
documented in [`../docs/INPUT_FORMAT.md`](../docs/INPUT_FORMAT.md).
