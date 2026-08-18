import { jsPDF } from "jspdf";
import { qrToDataUrl } from "../src/lib/qr";
import { computeLayout, DEFAULT_CONFIG } from "../src/lib/types";

const measure = (t: string, f: number) => ({ width: t.length * f * 0.55, height: f, ascent: f * 0.8 });

const doc = new jsPDF({ unit: "mm", format: [DEFAULT_CONFIG.widthMm, DEFAULT_CONFIG.heightMm], orientation: "portrait" });
const layout = computeLayout(DEFAULT_CONFIG, "AMB-H09F3", 1, measure);
doc.setDrawColor(0);
doc.setLineWidth(0.2);
doc.rect(0, 0, layout.width, layout.height);
const url = await qrToDataUrl("AMB-H09F3", 200, "M");
for (let i = 0; i < layout.qrCount; i++) {
  doc.addImage(url, "PNG", layout.qrX[i], layout.qrY, layout.qrSize, layout.qrSize);
}
doc.setFontSize((DEFAULT_CONFIG.fontMm * 72) / 25.4);
doc.text("AMB-H09F3", layout.textX, layout.textY);

const buf = Buffer.from(doc.output("arraybuffer"));
console.log("PDF bytes:", buf.length, "header:", buf.slice(0, 5).toString());
process.exit(buf.length > 100 && buf.slice(0, 5).toString() === "%PDF-" ? 0 : 1);
