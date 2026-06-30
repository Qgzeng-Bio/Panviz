# Third-party notices

Panviz bundles and depends on third-party software. The prebuilt browser bundle
`harness/dist/sequencetubemap_exact_bundle.js` is generated from the
SequenceTubeMap-derived core plus the JavaScript libraries below.

## SequenceTubeMap (layout/drawing core)

- Source: vgteam/sequenceTubeMap, upstream commit
  `33b7a7e5df9f8052974ef8e6c689a031dac6e2c9`.
- License: MIT — see [SequenceTubeMap_LICENSE.txt](SequenceTubeMap_LICENSE.txt).
- Derived files carry provenance headers (currently `src/panviz_core/`).

## Bundled JavaScript libraries

These are compiled into `harness/dist/` by webpack (see `package.json`):

| Library | License | Project |
| --- | --- | --- |
| d3 (v5 line) | ISC | https://github.com/d3/d3 |
| d3-selection-multi | BSD-3-Clause | https://github.com/d3/d3-selection-multi |
| deep-equal | MIT | https://github.com/inspect-js/node-deep-equal |

## Runtime / build tooling (not bundled)

| Tool | License | Project |
| --- | --- | --- |
| playwright-core | Apache-2.0 | https://github.com/microsoft/playwright |
| webpack, webpack-cli | MIT | https://github.com/webpack/webpack |

Each library remains under its own license; the full texts are available in the
respective upstream projects and in `node_modules/<pkg>/LICENSE` after
`npm install`. When publishing a Panviz release that includes the bundle, retain
these notices.
