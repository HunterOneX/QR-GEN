import { parseCsv } from "../src/lib/csv";
import { buildSingleZpl, buildBulkZpl } from "../src/lib/zpl";
import { computeLayout, DEFAULT_CONFIG } from "../src/lib/types";
import { qrModuleCount } from "../src/lib/qr";

let failures = 0;
function check(name: string, cond: boolean, extra?: unknown) {
  if (cond) {
    console.log(`  ok  - ${name}`);
  } else {
    failures++;
    console.error(`FAIL  - ${name}`, extra ?? "");
  }
}

// --- CSV ---
const csv = "AMB-H09F3\nAMB-H09F4\nAMB-H09F5\n";
const noHeader = parseCsv(csv, false);
check("csv: 3 rows without header", noHeader.length === 3, noHeader);
check("csv: first value", noHeader[0] === "AMB-H09F3", noHeader[0]);

const csvHeader = "CODE\nAMB-1\nAMB-2\n";
const withHeader = parseCsv(csvHeader, true);
check("csv: 2 rows with header skipped", withHeader.length === 2, withHeader);

// --- QR module count ---
const mods = qrModuleCount("AMB-H09F3", "M");
check("qr: module count > 0", mods > 0, mods);

// --- Layout (preview scale = 4 px/mm) ---
const measure = (t: string, f: number) => ({ width: t.length * f * 0.55, height: f, ascent: f * 0.8 });
const layout = computeLayout(DEFAULT_CONFIG, "AMB-H09F3", 4, measure);
check("layout: width = 400px @4px/mm", layout.width === 400, layout.width);
check("layout: qrCount = 3", layout.qrX.length === 3, layout.qrX);
check("layout: qr ascending x", layout.qrX[0] < layout.qrX[1] && layout.qrX[1] < layout.qrX[2]);
check("layout: qr fits height", layout.qrSize <= layout.height - 2 * layout.marginY + 1e-9, {
  qrSize: layout.qrSize,
  height: layout.height,
});

// --- ZPL ---
const single = buildSingleZpl(DEFAULT_CONFIG, "AMB-H09F3");
check("zpl: starts with ^XA", single.startsWith("^XA"), single.slice(0, 10));
check("zpl: ends with ^XZ", single.endsWith("^XZ"));
check("zpl: contains 3 QR fields", (single.match(/\^BQN/g) || []).length === 3, single);
check("zpl: contains text field", single.includes("^FDAMB-H09F3^FS"));

const bulk = buildBulkZpl(DEFAULT_CONFIG, ["A", "B"], 2);
check("zpl: bulk 2 rows x2 qty = 4 labels", (bulk.match(/\^XA/g) || []).length === 4, bulk);

console.log(failures === 0 ? "\nALL PASSED" : `\n${failures} FAILED`);
process.exit(failures === 0 ? 0 : 1);
