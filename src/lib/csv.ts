import Papa from "papaparse";

/**
 * Parse CSV text and return the first column of each non-empty row.
 * When `hasHeader` is true the first row is skipped.
 */
export function parseCsv(text: string, hasHeader: boolean): string[] {
  const result = Papa.parse<string[]>(text, { skipEmptyLines: true });
  let rows = result.data as unknown as string[][];
  if (!Array.isArray(rows)) rows = [];
  if (hasHeader && rows.length) rows = rows.slice(1);
  return rows
    .map((r) => (Array.isArray(r) ? r[0] : r))
    .map((v) => String(v ?? "").trim())
    .filter((v) => v.length > 0);
}
