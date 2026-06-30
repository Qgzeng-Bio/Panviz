const fs = require("fs");
const path = require("path");
const { chromium } = require("../node_modules/playwright-core");

function parseArgs(argv) {
  const out = {};
  for (let i = 2; i < argv.length; i += 2) {
    const key = argv[i];
    const value = argv[i + 1];
    if (!key || !key.startsWith("--") || value === undefined) {
      throw new Error(`invalid argument near ${key || "<end>"}`);
    }
    out[key.slice(2)] = value;
  }
  return out;
}

async function main() {
  const args = parseArgs(process.argv);
  const inputJson = args.input;
  const svgOut = args.svg;
  const pngOut = args.png;
  const pdfOut = args.pdf;
  const browserExecutable = args.browser;
  if (!inputJson || !svgOut || !pngOut || !pdfOut || !browserExecutable) {
    throw new Error("required: --input --svg --png --pdf --browser");
  }

  const payload = JSON.parse(fs.readFileSync(inputJson, "utf8"));
  const panel = payload.mainFigure || {};
  const panelWidth = Number(panel.panelWidth || 1800);
  const xCompression = Number(panel.xCompression || 0.45);
  const padX = Number(panel.padX || 35);
  const padY = Number(panel.padY || 170);
  const nodeStrokeWidth = Number(panel.nodeStrokeWidth || 1.5);
  const deviceScaleFactor = Number(panel.deviceScaleFactor || 2);
  const referenceCoordinate = payload.referenceCoordinate || null;
  const pagePath = path.resolve(__dirname, "render_page.html");

  const browser = await chromium.launch({
    executablePath: browserExecutable,
    headless: true,
    args: ["--no-sandbox", "--disable-dev-shm-usage"],
  });
  try {
    const page = await browser.newPage({
      viewport: { width: payload.viewport.width, height: payload.viewport.height },
      deviceScaleFactor,
    });
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        console.error(`[browser:${msg.type()}] ${msg.text()}`);
      }
    });
    await page.goto(`file://${pagePath}`, { waitUntil: "load" });
    await page.evaluate((data) => window.renderSequenceTubeMapExact(data), payload);
    await page.waitForSelector("g.track", { timeout: 30000 });
    await page.waitForSelector("g.node", { timeout: 30000 });
    await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => resolve())));

    const layout = await page.$eval("#svg", (svg, settings) => {
      const initial = svg.getBBox();
      const originX = initial.x;
      const scaleX = (value) => originX + (Number(value) - originX) * settings.xCompression;
      const scaleLength = (value) => Number(value) * settings.xCompression;
      const format = (value) => Number(value.toFixed(3));

      function scalePathDataX(d) {
        const tokens = String(d).match(/[A-Za-z]|[-+]?(?:\d*\.)?\d+(?:[eE][-+]?\d+)?/g);
        if (!tokens) return d;
        const out = [];
        let cmd = null;
        let paramIndex = 0;
        const xPositions = {
          M: [0], L: [0], T: [0],
          H: [0],
          V: [],
          C: [0, 2, 4],
          S: [0, 2],
          Q: [0, 2],
          A: [5],
        };
        const paramCounts = { M: 2, L: 2, T: 2, H: 1, V: 1, C: 6, S: 4, Q: 4, A: 7, Z: 0 };
        for (const token of tokens) {
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
          const upper = cmd.toUpperCase();
          const shouldScale = (xPositions[upper] || []).includes(paramIndex);
          const scaled = shouldScale ? format(scaleX(token)) : token;
          out.push(String(scaled));
          paramIndex += 1;
          if (paramIndex >= (paramCounts[upper] || 2)) {
            paramIndex = 0;
          }
        }
        return out.join(" ");
      }

      svg.querySelectorAll("path").forEach((el) => {
        if (el.closest("defs")) return;
        if (el.hasAttribute("d")) el.setAttribute("d", scalePathDataX(el.getAttribute("d")));
      });
      svg.querySelectorAll("rect").forEach((el) => {
        if (el.closest("defs")) return;
        if (el.hasAttribute("x")) el.setAttribute("x", String(format(scaleX(el.getAttribute("x")))));
        if (el.hasAttribute("width")) el.setAttribute("width", String(format(scaleLength(el.getAttribute("width")))));
      });
      svg.querySelectorAll("line").forEach((el) => {
        if (el.closest("defs")) return;
        if (el.hasAttribute("x1")) el.setAttribute("x1", String(format(scaleX(el.getAttribute("x1")))));
        if (el.hasAttribute("x2")) el.setAttribute("x2", String(format(scaleX(el.getAttribute("x2")))));
      });
      svg.querySelectorAll("text").forEach((el) => {
        if (el.closest("defs")) return;
        if (el.hasAttribute("x")) el.setAttribute("x", String(format(scaleX(el.getAttribute("x")))));
      });

      function roundedRectPath(x, y, width, height, radius) {
        const x2 = x + width;
        const y2 = y + height;
        const r = Math.max(0, Math.min(radius, width / 2, height / 2));
        return [
          `M ${format(x + r)} ${format(y)}`,
          `L ${format(x2 - r)} ${format(y)}`,
          `Q ${format(x2)} ${format(y)} ${format(x2)} ${format(y + r)}`,
          `L ${format(x2)} ${format(y2 - r)}`,
          `Q ${format(x2)} ${format(y2)} ${format(x2 - r)} ${format(y2)}`,
          `L ${format(x + r)} ${format(y2)}`,
          `Q ${format(x)} ${format(y2)} ${format(x)} ${format(y2 - r)}`,
          `L ${format(x)} ${format(y + r)}`,
          `Q ${format(x)} ${format(y)} ${format(x + r)} ${format(y)}`,
          "Z",
        ].join(" ");
      }

      svg.querySelectorAll("g.node path").forEach((el) => {
        const box = el.getBBox();
        const minWidth = 8;
        const width = Math.max(box.width, minWidth);
        const x = box.x - (width - box.width) / 2;
        el.setAttribute("d", roundedRectPath(x, box.y, width, box.height, 3.2));
        el.style.strokeWidth = `${settings.nodeStrokeWidth}px`;
        el.setAttribute("stroke-width", String(settings.nodeStrokeWidth));
        el.setAttribute("stroke-linejoin", "round");
        el.setAttribute("stroke-linecap", "round");
        el.setAttribute("vector-effect", "non-scaling-stroke");
      });

      const innerGroup = svg.querySelector("#svg > g");
      if (innerGroup) {
        Array.from(innerGroup.children).forEach((child) => {
          if (child.tagName === "defs") return;
          if (child.classList && (child.classList.contains("track") || child.classList.contains("node"))) return;
          child.remove();
        });
      }

      function addSvg(tag, attrs) {
        const el = document.createElementNS("http://www.w3.org/2000/svg", tag);
        Object.entries(attrs).forEach(([key, value]) => el.setAttribute(key, String(value)));
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

      const contentBox = svg.getBBox();
      if (settings.referenceCoordinate) {
        const ref = settings.referenceCoordinate;
        const x1 = contentBox.x;
        const x2 = contentBox.x + contentBox.width;
        const axisY = contentBox.y - 52;
        const labelY = contentBox.y - 76;
        const span = Math.max(1, ref.end - ref.start + 1);
        const tickSpec = chooseTickBp(span);
        const coordToX = (coord) => x1 + ((coord - ref.start) / Math.max(1, ref.end - ref.start)) * (x2 - x1);
        const axisGroup = addSvg("g", { class: "genomic-axis" });
        const axis = document.createElementNS("http://www.w3.org/2000/svg", "line");
        axis.setAttribute("x1", x1);
        axis.setAttribute("x2", x2);
        axis.setAttribute("y1", axisY);
        axis.setAttribute("y2", axisY);
        axis.setAttribute("stroke", "#000000");
        axis.setAttribute("stroke-width", "1.2");
        axisGroup.appendChild(axis);

        const startTick = Math.ceil(ref.start / tickSpec.tickBp) * tickSpec.tickBp;
        for (let coord = startTick; coord <= ref.end; coord += tickSpec.tickBp) {
          const x = coordToX(coord);
          const isLabeled = coord % tickSpec.labelBp === 0;
          const tickLength = isLabeled ? 7 : 4;
          const t = document.createElementNS("http://www.w3.org/2000/svg", "line");
          t.setAttribute("x1", x);
          t.setAttribute("x2", x);
          t.setAttribute("y1", axisY - tickLength);
          t.setAttribute("y2", axisY);
          t.setAttribute("stroke", "#000000");
          t.setAttribute("stroke-width", isLabeled ? "1.2" : "0.9");
          axisGroup.appendChild(t);
          if (isLabeled) {
            const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
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
        ].forEach((endpoint) => {
          const t = document.createElementNS("http://www.w3.org/2000/svg", "line");
          t.setAttribute("x1", endpoint.x);
          t.setAttribute("x2", endpoint.x);
          t.setAttribute("y1", axisY - 9);
          t.setAttribute("y2", axisY);
          t.setAttribute("stroke", "#000000");
          t.setAttribute("stroke-width", "1.3");
          axisGroup.appendChild(t);
          const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
          text.setAttribute("x", endpoint.x);
          text.setAttribute("y", axisY + 21);
          text.setAttribute("text-anchor", endpoint.anchor);
          text.setAttribute("font-family", "Arial, sans-serif");
          text.setAttribute("font-size", "10");
          text.textContent = `${formatEndpointMb(endpoint.coord)} Mb`;
          axisGroup.appendChild(text);
        });
        const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
        label.setAttribute("x", (x1 + x2) / 2);
        label.setAttribute("y", labelY);
        label.setAttribute("text-anchor", "middle");
        label.setAttribute("font-family", "Arial, sans-serif");
        label.setAttribute("font-size", "17");
        label.setAttribute("font-weight", "600");
        label.textContent = `${ref.chrom}:${formatMb(ref.start)}-${formatMb(ref.end)} Mb`;
        axisGroup.appendChild(label);

        const scaleBp = tickSpec.scaleBp;
        const scaleWidth = contentBox.width * (scaleBp / span);
        const scaleX1 = x1 + contentBox.width / 2 - scaleWidth / 2;
        const scaleX2 = scaleX1 + scaleWidth;
        const scaleY = contentBox.y + contentBox.height + 40;
        const scaleGroup = addSvg("g", { class: "genomic-scale-bar" });
        const bar = document.createElementNS("http://www.w3.org/2000/svg", "line");
        bar.setAttribute("x1", scaleX1);
        bar.setAttribute("x2", scaleX2);
        bar.setAttribute("y1", scaleY);
        bar.setAttribute("y2", scaleY);
        bar.setAttribute("stroke", "#000000");
        bar.setAttribute("stroke-width", "1.6");
        scaleGroup.appendChild(bar);
        [scaleX1, scaleX2].forEach((x) => {
          const t = document.createElementNS("http://www.w3.org/2000/svg", "line");
          t.setAttribute("x1", x);
          t.setAttribute("x2", x);
          t.setAttribute("y1", scaleY - 7);
          t.setAttribute("y2", scaleY + 7);
          t.setAttribute("stroke", "#000000");
          t.setAttribute("stroke-width", "1.6");
          scaleGroup.appendChild(t);
        });
        const scaleText = document.createElementNS("http://www.w3.org/2000/svg", "text");
        scaleText.setAttribute("x", (scaleX1 + scaleX2) / 2);
        scaleText.setAttribute("y", scaleY + 22);
        scaleText.setAttribute("text-anchor", "middle");
        scaleText.setAttribute("font-family", "Arial, sans-serif");
        scaleText.setAttribute("font-size", "12");
        scaleText.textContent = scaleBp >= 1000 ? `${scaleBp / 1000} kb` : `${scaleBp} bp`;
        scaleGroup.appendChild(scaleText);
      }

      const bbox = svg.getBBox();
      const viewX = Math.floor(bbox.x - settings.padX);
      const viewY = Math.floor(bbox.y - settings.padY);
      const viewW = Math.ceil(bbox.width + 2 * settings.padX);
      const viewH = Math.ceil(bbox.height + 2 * settings.padY);
      const panelHeight = Math.ceil(settings.panelWidth * viewH / viewW);
      svg.setAttribute("xmlns", "http://www.w3.org/2000/svg");
      svg.setAttribute("width", String(settings.panelWidth));
      svg.setAttribute("height", String(panelHeight));
      svg.setAttribute("viewBox", `${viewX} ${viewY} ${viewW} ${viewH}`);
      svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
      svg.style.width = `${settings.panelWidth}px`;
      svg.style.height = `${panelHeight}px`;
      return { viewX, viewY, viewW, viewH, panelWidth: settings.panelWidth, panelHeight };
    }, { panelWidth, xCompression, padX, padY, nodeStrokeWidth, referenceCoordinate });

    const svgText = await page.$eval("#svg", (svg) => new XMLSerializer().serializeToString(svg));
    fs.writeFileSync(svgOut, svgText);

    const svgHandle = await page.$("#svg");
    await svgHandle.screenshot({ path: pngOut, omitBackground: false });
    await page.pdf({
      path: pdfOut,
      printBackground: true,
      width: `${layout.panelWidth}px`,
      height: `${layout.panelHeight}px`,
      margin: { top: "0px", right: "0px", bottom: "0px", left: "0px" },
    });

    const counts = await page.evaluate((layoutInfo) => ({
      tracks: document.querySelectorAll("g.track").length,
      nodes: document.querySelectorAll("g.node").length,
      trackChildren: document.querySelectorAll("g.track > *").length,
      nodeChildren: document.querySelectorAll("g.node > *").length,
      panelWidth: layoutInfo.panelWidth,
      panelHeight: layoutInfo.panelHeight,
      viewBoxWidth: layoutInfo.viewW,
      viewBoxHeight: layoutInfo.viewH,
    }), layout);
    process.stdout.write(`${JSON.stringify(counts)}\n`);
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  console.error(err && err.stack ? err.stack : err);
  process.exit(1);
});
