/*
 * Panviz static-figure post-processing (runs in the browser via Playwright).
 *
 * This is Panviz-owned code (not from SequenceTubeMap). It takes the laid-out
 * tube-map SVG produced by the core renderer and applies the publication style:
 *
 *   1. applyXCompression     - coordinate-level horizontal compaction
 *   2. regularizeNodeOutlines - uniform rounded node rectangles + stroke
 *   3. pruneExtraChildren    - drop everything except tracks and nodes
 *   4. drawAnnotations       - genomic axis (ticks/labels/title) + scale bar
 *   5. finalizeViewport      - panel width/height and viewBox
 *
 * The operations are intentionally identical to the previous inline adapter so
 * the rendered SVG stays byte-for-byte unchanged; tests/check_svg_structure.py
 * enforces this. Entry point: window.__panvizPostProcess(svg, settings).
 */
(function () {
  "use strict";

  var SVG_NS = "http://www.w3.org/2000/svg";

  function makeContext(svg, settings) {
    var initial = svg.getBBox();
    var originX = initial.x;
    var scaleX = function (value) {
      return originX + (Number(value) - originX) * settings.xCompression;
    };
    var scaleLength = function (value) {
      return Number(value) * settings.xCompression;
    };
    var format = function (value) {
      return Number(value.toFixed(3));
    };
    return { settings: settings, originX: originX, scaleX: scaleX, scaleLength: scaleLength, format: format };
  }

  // --- 1. horizontal compression ------------------------------------------
  function scalePathDataX(d, ctx) {
    var tokens = String(d).match(/[A-Za-z]|[-+]?(?:\d*\.)?\d+(?:[eE][-+]?\d+)?/g);
    if (!tokens) return d;
    var out = [];
    var cmd = null;
    var paramIndex = 0;
    var xPositions = {
      M: [0], L: [0], T: [0],
      H: [0],
      V: [],
      C: [0, 2, 4],
      S: [0, 2],
      Q: [0, 2],
      A: [5],
    };
    var paramCounts = { M: 2, L: 2, T: 2, H: 1, V: 1, C: 6, S: 4, Q: 4, A: 7, Z: 0 };
    for (var i = 0; i < tokens.length; i += 1) {
      var token = tokens[i];
      if (/^[A-Za-z]$/.test(token)) {
        cmd = token;
        paramIndex = 0;
        out.push(token);
        continue;
      }
      if (!cmd) {
        out.push(token);
        continue;
      }
      var upper = cmd.toUpperCase();
      var shouldScale = (xPositions[upper] || []).includes(paramIndex);
      var scaled = shouldScale ? ctx.format(ctx.scaleX(token)) : token;
      out.push(String(scaled));
      paramIndex += 1;
      if (paramIndex >= (paramCounts[upper] || 2)) {
        paramIndex = 0;
      }
    }
    return out.join(" ");
  }

  function applyXCompression(svg, ctx) {
    var scaleX = ctx.scaleX;
    var scaleLength = ctx.scaleLength;
    var format = ctx.format;
    svg.querySelectorAll("path").forEach(function (el) {
      if (el.closest("defs")) return;
      if (el.hasAttribute("d")) el.setAttribute("d", scalePathDataX(el.getAttribute("d"), ctx));
    });
    svg.querySelectorAll("rect").forEach(function (el) {
      if (el.closest("defs")) return;
      if (el.hasAttribute("x")) el.setAttribute("x", String(format(scaleX(el.getAttribute("x")))));
      if (el.hasAttribute("width")) el.setAttribute("width", String(format(scaleLength(el.getAttribute("width")))));
    });
    svg.querySelectorAll("line").forEach(function (el) {
      if (el.closest("defs")) return;
      if (el.hasAttribute("x1")) el.setAttribute("x1", String(format(scaleX(el.getAttribute("x1")))));
      if (el.hasAttribute("x2")) el.setAttribute("x2", String(format(scaleX(el.getAttribute("x2")))));
    });
    svg.querySelectorAll("text").forEach(function (el) {
      if (el.closest("defs")) return;
      if (el.hasAttribute("x")) el.setAttribute("x", String(format(scaleX(el.getAttribute("x")))));
    });
  }

  // --- 2. node outline regularization -------------------------------------
  function roundedRectPath(x, y, width, height, radius, format) {
    var x2 = x + width;
    var y2 = y + height;
    var r = Math.max(0, Math.min(radius, width / 2, height / 2));
    return [
      "M " + format(x + r) + " " + format(y),
      "L " + format(x2 - r) + " " + format(y),
      "Q " + format(x2) + " " + format(y) + " " + format(x2) + " " + format(y + r),
      "L " + format(x2) + " " + format(y2 - r),
      "Q " + format(x2) + " " + format(y2) + " " + format(x2 - r) + " " + format(y2),
      "L " + format(x + r) + " " + format(y2),
      "Q " + format(x) + " " + format(y2) + " " + format(x) + " " + format(y2 - r),
      "L " + format(x) + " " + format(y + r),
      "Q " + format(x) + " " + format(y) + " " + format(x + r) + " " + format(y),
      "Z",
    ].join(" ");
  }

  function regularizeNodeOutlines(svg, ctx) {
    var format = ctx.format;
    var settings = ctx.settings;
    svg.querySelectorAll("g.node path").forEach(function (el) {
      var box = el.getBBox();
      var minWidth = 8;
      var width = Math.max(box.width, minWidth);
      var x = box.x - (width - box.width) / 2;
      el.setAttribute("d", roundedRectPath(x, box.y, width, box.height, 3.2, format));
      el.style.strokeWidth = settings.nodeStrokeWidth + "px";
      el.setAttribute("stroke-width", String(settings.nodeStrokeWidth));
      el.setAttribute("stroke-linejoin", "round");
      el.setAttribute("stroke-linecap", "round");
      el.setAttribute("vector-effect", "non-scaling-stroke");
    });
  }

  // --- 3. keep only tracks and nodes --------------------------------------
  function pruneExtraChildren(svg) {
    var innerGroup = svg.querySelector("#svg > g");
    if (innerGroup) {
      Array.from(innerGroup.children).forEach(function (child) {
        if (child.tagName === "defs") return;
        if (child.classList && (child.classList.contains("track") || child.classList.contains("node"))) return;
        child.remove();
      });
    }
  }

  // --- 4. genomic axis + scale bar ----------------------------------------
  function drawAnnotations(svg, ctx) {
    var settings = ctx.settings;

    function addSvg(tag, attrs) {
      var el = document.createElementNS(SVG_NS, tag);
      Object.entries(attrs).forEach(function (entry) {
        el.setAttribute(entry[0], String(entry[1]));
      });
      svg.appendChild(el);
      return el;
    }

    function formatMb(value) {
      return (value / 1000000).toFixed(2);
    }

    function formatEndpointMb(value) {
      return (value / 1000000).toFixed(3);
    }

    function chooseTickBp(span) {
      if (span <= 80000) return { tickBp: 5000, labelBp: 10000, scaleBp: 5000 };
      if (span <= 160000) return { tickBp: 10000, labelBp: 20000, scaleBp: 10000 };
      if (span <= 400000) return { tickBp: 20000, labelBp: 40000, scaleBp: 20000 };
      return { tickBp: 50000, labelBp: 100000, scaleBp: 50000 };
    }

    var contentBox = svg.getBBox();
    if (!settings.referenceCoordinate) return;

    var ref = settings.referenceCoordinate;
    var x1 = contentBox.x;
    var x2 = contentBox.x + contentBox.width;
    var axisY = contentBox.y - 52;
    var labelY = contentBox.y - 76;
    var span = Math.max(1, ref.end - ref.start + 1);
    var tickSpec = chooseTickBp(span);
    var coordToX = function (coord) {
      return x1 + ((coord - ref.start) / Math.max(1, ref.end - ref.start)) * (x2 - x1);
    };
    var axisGroup = addSvg("g", { class: "genomic-axis" });
    var axis = document.createElementNS(SVG_NS, "line");
    axis.setAttribute("x1", x1);
    axis.setAttribute("x2", x2);
    axis.setAttribute("y1", axisY);
    axis.setAttribute("y2", axisY);
    axis.setAttribute("stroke", "#000000");
    axis.setAttribute("stroke-width", "1.2");
    axisGroup.appendChild(axis);

    var startTick = Math.ceil(ref.start / tickSpec.tickBp) * tickSpec.tickBp;
    for (var coord = startTick; coord <= ref.end; coord += tickSpec.tickBp) {
      var x = coordToX(coord);
      var isLabeled = coord % tickSpec.labelBp === 0;
      var tickLength = isLabeled ? 7 : 4;
      var t = document.createElementNS(SVG_NS, "line");
      t.setAttribute("x1", x);
      t.setAttribute("x2", x);
      t.setAttribute("y1", axisY - tickLength);
      t.setAttribute("y2", axisY);
      t.setAttribute("stroke", "#000000");
      t.setAttribute("stroke-width", isLabeled ? "1.2" : "0.9");
      axisGroup.appendChild(t);
      if (isLabeled) {
        var text = document.createElementNS(SVG_NS, "text");
        text.setAttribute("x", x);
        text.setAttribute("y", axisY + 21);
        text.setAttribute("text-anchor", "middle");
        text.setAttribute("font-family", "Arial, sans-serif");
        text.setAttribute("font-size", "10");
        text.textContent = formatMb(coord);
        axisGroup.appendChild(text);
      }
    }
    [
      { x: x1, coord: ref.start, anchor: "start" },
      { x: x2, coord: ref.end, anchor: "end" },
    ].forEach(function (endpoint) {
      var t = document.createElementNS(SVG_NS, "line");
      t.setAttribute("x1", endpoint.x);
      t.setAttribute("x2", endpoint.x);
      t.setAttribute("y1", axisY - 9);
      t.setAttribute("y2", axisY);
      t.setAttribute("stroke", "#000000");
      t.setAttribute("stroke-width", "1.3");
      axisGroup.appendChild(t);
      var text = document.createElementNS(SVG_NS, "text");
      text.setAttribute("x", endpoint.x);
      text.setAttribute("y", axisY + 21);
      text.setAttribute("text-anchor", endpoint.anchor);
      text.setAttribute("font-family", "Arial, sans-serif");
      text.setAttribute("font-size", "10");
      text.textContent = formatEndpointMb(endpoint.coord) + " Mb";
      axisGroup.appendChild(text);
    });
    var label = document.createElementNS(SVG_NS, "text");
    label.setAttribute("x", (x1 + x2) / 2);
    label.setAttribute("y", labelY);
    label.setAttribute("text-anchor", "middle");
    label.setAttribute("font-family", "Arial, sans-serif");
    label.setAttribute("font-size", "17");
    label.setAttribute("font-weight", "600");
    label.textContent = ref.chrom + ":" + formatMb(ref.start) + "-" + formatMb(ref.end) + " Mb";
    axisGroup.appendChild(label);

    var scaleBp = tickSpec.scaleBp;
    var scaleWidth = contentBox.width * (scaleBp / span);
    var scaleX1 = x1 + contentBox.width / 2 - scaleWidth / 2;
    var scaleX2 = scaleX1 + scaleWidth;
    var scaleY = contentBox.y + contentBox.height + 40;
    var scaleGroup = addSvg("g", { class: "genomic-scale-bar" });
    var bar = document.createElementNS(SVG_NS, "line");
    bar.setAttribute("x1", scaleX1);
    bar.setAttribute("x2", scaleX2);
    bar.setAttribute("y1", scaleY);
    bar.setAttribute("y2", scaleY);
    bar.setAttribute("stroke", "#000000");
    bar.setAttribute("stroke-width", "1.6");
    scaleGroup.appendChild(bar);
    [scaleX1, scaleX2].forEach(function (sx) {
      var tk = document.createElementNS(SVG_NS, "line");
      tk.setAttribute("x1", sx);
      tk.setAttribute("x2", sx);
      tk.setAttribute("y1", scaleY - 7);
      tk.setAttribute("y2", scaleY + 7);
      tk.setAttribute("stroke", "#000000");
      tk.setAttribute("stroke-width", "1.6");
      scaleGroup.appendChild(tk);
    });
    var scaleText = document.createElementNS(SVG_NS, "text");
    scaleText.setAttribute("x", (scaleX1 + scaleX2) / 2);
    scaleText.setAttribute("y", scaleY + 22);
    scaleText.setAttribute("text-anchor", "middle");
    scaleText.setAttribute("font-family", "Arial, sans-serif");
    scaleText.setAttribute("font-size", "12");
    scaleText.textContent = scaleBp >= 1000 ? scaleBp / 1000 + " kb" : scaleBp + " bp";
    scaleGroup.appendChild(scaleText);
  }

  // --- 5. panel + viewBox -------------------------------------------------
  function finalizeViewport(svg, ctx) {
    var settings = ctx.settings;
    var bbox = svg.getBBox();
    var viewX = Math.floor(bbox.x - settings.padX);
    var viewY = Math.floor(bbox.y - settings.padY);
    var viewW = Math.ceil(bbox.width + 2 * settings.padX);
    var viewH = Math.ceil(bbox.height + 2 * settings.padY);
    var panelHeight = Math.ceil(settings.panelWidth * viewH / viewW);
    svg.setAttribute("xmlns", SVG_NS);
    svg.setAttribute("width", String(settings.panelWidth));
    svg.setAttribute("height", String(panelHeight));
    svg.setAttribute("viewBox", viewX + " " + viewY + " " + viewW + " " + viewH);
    svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
    svg.style.width = settings.panelWidth + "px";
    svg.style.height = panelHeight + "px";
    return { viewX: viewX, viewY: viewY, viewW: viewW, viewH: viewH, panelWidth: settings.panelWidth, panelHeight: panelHeight };
  }

  window.__panvizPostProcess = function (svg, settings) {
    var ctx = makeContext(svg, settings);
    applyXCompression(svg, ctx);
    regularizeNodeOutlines(svg, ctx);
    pruneExtraChildren(svg);
    drawAnnotations(svg, ctx);
    return finalizeViewport(svg, ctx);
  };
})();
