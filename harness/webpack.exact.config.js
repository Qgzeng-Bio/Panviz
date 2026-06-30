const path = require("path");

module.exports = {
  mode: "production",
  entry: path.resolve(__dirname, "tubemap_exact_entry.js"),
  output: {
    filename: "sequencetubemap_exact_bundle.js",
    path: path.resolve(__dirname, "dist"),
    library: {
      name: "SequenceTubeMapExactHarness",
      type: "window",
    },
    clean: true,
  },
  resolve: {
    extensions: [".js", ".mjs"],
    fallback: {
      fs: false,
      path: false,
    },
  },
};
