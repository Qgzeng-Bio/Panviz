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
  const annotateSv = Boolean(panel.annotateSv);
  const svAnnotations = payload.svAnnotations || {};
  const trackCount = (payload.tracks || []).length;
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

    // Inject Panviz-owned post-processing (axis/style/compaction/viewport) and
    // apply it to the laid-out SVG. See harness/lib/postprocess.js.
    const postProcessSource = fs.readFileSync(path.resolve(__dirname, "lib/postprocess.js"), "utf8");
    await page.addScriptTag({ content: postProcessSource });
    const layout = await page.$eval(
      "#svg",
      (svg, settings) => window.__panvizPostProcess(svg, settings),
      { panelWidth, xCompression, padX, padY, nodeStrokeWidth, referenceCoordinate, annotateSv, svAnnotations, trackCount }
    );

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
