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
  const panelHeight = Number(panel.panelHeight || 1500);
  const padX = Number(panel.padX || 35);
  const padY = Number(panel.padY || 180);
  const deviceScaleFactor = Number(panel.deviceScaleFactor || 2);
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

    const svgText = await page.$eval("#svg", (svg, settings) => {
      const bbox = svg.getBBox();
      const viewX = Math.floor(bbox.x - settings.padX);
      const viewY = Math.floor(bbox.y - settings.padY);
      const viewW = Math.ceil(bbox.width + 2 * settings.padX);
      const viewH = Math.ceil(bbox.height + 2 * settings.padY);
      svg.setAttribute("xmlns", "http://www.w3.org/2000/svg");
      svg.setAttribute("width", String(settings.panelWidth));
      svg.setAttribute("height", String(settings.panelHeight));
      svg.setAttribute("viewBox", `${viewX} ${viewY} ${viewW} ${viewH}`);
      svg.setAttribute("preserveAspectRatio", "none");
      svg.style.width = `${settings.panelWidth}px`;
      svg.style.height = `${settings.panelHeight}px`;
      return new XMLSerializer().serializeToString(svg);
    }, { panelWidth, panelHeight, padX, padY });
    fs.writeFileSync(svgOut, svgText);

    await page.$eval("#svg", (svg, settings) => {
      svg.setAttribute("width", String(settings.panelWidth));
      svg.setAttribute("height", String(settings.panelHeight));
      svg.setAttribute("preserveAspectRatio", "none");
      svg.style.width = `${settings.panelWidth}px`;
      svg.style.height = `${settings.panelHeight}px`;
    }, { panelWidth, panelHeight });
    const svgHandle = await page.$("#svg");
    await svgHandle.screenshot({ path: pngOut, omitBackground: false });
    await page.pdf({
      path: pdfOut,
      printBackground: true,
      width: `${panelWidth}px`,
      height: `${panelHeight}px`,
      margin: { top: "0px", right: "0px", bottom: "0px", left: "0px" },
    });

    const counts = await page.evaluate(() => ({
      tracks: document.querySelectorAll("g.track").length,
      nodes: document.querySelectorAll("g.node").length,
      trackChildren: document.querySelectorAll("g.track > *").length,
      nodeChildren: document.querySelectorAll("g.node > *").length,
    }));
    process.stdout.write(`${JSON.stringify(counts)}\n`);
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  console.error(err && err.stack ? err.stack : err);
  process.exit(1);
});
