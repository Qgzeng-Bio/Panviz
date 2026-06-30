# Panviz Source Layout

This directory is reserved for the Panviz-owned implementation.

Initial planned modules:

```text
src/model/       # normalized nodes/tracks/region data model
src/layout/      # node order, x/y placement, lane assignment
src/geometry/    # node hulls, tube rectangles, Bezier connectors
src/style/       # colors, strokes, fonts, node-outline rules
src/axis/        # chromosome axis and scale-bar generation
src/render_svg/  # SVG drawing backend
src/export/      # SVG/PNG/PDF export logic
```

The current working renderer still lives in `harness/export_mainfig_natural.js`.
Move behavior into `src/` incrementally while keeping visual output comparable
to the accepted baseline.

