import * as tubeMap from "../src/panviz_core/tubemap.js";

function applyVisOptions(visOptions) {
  const opts = visOptions || {};
  tubeMap.setNodeWidthOption(opts.compressedView ? "compressed" : "normal");
  tubeMap.setMergeNodesFlag(Boolean(opts.removeRedundantNodes));
  tubeMap.setTransparentNodesFlag(Boolean(opts.transparentNodes));
  tubeMap.setShowReadsFlag(Boolean(opts.showReads));
  tubeMap.setSoftClipsFlag(Boolean(opts.showSoftClips));
  tubeMap.setColoredNodes(opts.coloredNodes || []);
  tubeMap.setMappingQualityCutoff(opts.mappingQualityCutoff || 0);
}

window.renderSequenceTubeMapExact = function renderSequenceTubeMapExact(payload) {
  const svg = document.querySelector("#svg");
  if (!svg) {
    throw new Error("missing #svg element");
  }
  svg.innerHTML = "";
  svg.removeAttribute("viewBox");
  svg.removeAttribute("width");
  svg.removeAttribute("height");

  applyVisOptions(payload.visOptions);
  tubeMap.create({
    svgID: "#svg",
    nodes: payload.nodes,
    tracks: payload.tracks,
    reads: payload.reads || [],
    region: payload.region || [],
    visOptions: payload.visOptions || {},
    hideLegend: false,
  });
};
