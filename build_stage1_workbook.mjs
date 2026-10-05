import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const projectRoot = path.dirname(new URL(import.meta.url).pathname.replace(/^\/(.:)/, "$1"));
const outputDir = path.resolve(projectRoot, "..", "outputs", "customer-churn-stage1");
const previewDir = path.resolve(projectRoot, "..", "tmp", "customer-churn-previews");
const customerCsv = path.join(projectRoot, "data", "processed", "customer_churn_analysis.csv");
const monthlyCsv = path.join(projectRoot, "data", "processed", "monthly_churn_kpis.csv");

function parseCsv(text) {
  const lines = text.trim().split(/\r?\n/);
  const headers = lines[0].split(",");
  return {
    headers,
    rows: lines.slice(1).map((line) => {
      const values = line.split(",");
      return Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""]));
    }),
  };
}

function asDate(value) {
  return value ? new Date(`${value}T00:00:00`) : null;
}

function asNumber(value) {
  return value === "" ? null : Number(value);
}

function summarize(rows, field) {
  const map = new Map();
  for (const row of rows) {
    const key = row[field];
    const current = map.get(key) ?? { customers: 0, churned: 0, clv: 0, lost: 0 };
    current.customers += 1;
    current.churned += Number(row.churn_flag);
    current.clv += Number(row.clv_realized_usd);
    current.lost += Number(row.annualized_revenue_lost_usd);
    map.set(key, current);
  }
  return [...map.entries()]
    .map(([key, value]) => [
      key,
      value.customers,
      value.churned,
      value.churned / value.customers,
      value.clv / value.customers,
      value.lost,
    ])
    .sort((a, b) => b[3] - a[3]);
}

const customerParsed = parseCsv(await fs.readFile(customerCsv, "utf8"));
const monthlyParsed = parseCsv(await fs.readFile(monthlyCsv, "utf8"));

const customerRows = customerParsed.rows;
const customerMatrix = customerRows.map((row) => [
  row.customer_id,
  asDate(row.signup_date),
  asDate(row.churn_date),
  asDate(row.snapshot_date),
  asNumber(row.churn_flag),
  row.status,
  asNumber(row.tenure_months),
  row.tenure_band,
  row.contract_type,
  row.payment_method,
  row.service_category,
  row.region,
  row.customer_segment,
  asNumber(row.monthly_charge_usd),
  asNumber(row.avg_discount_pct),
  asNumber(row.support_tickets_90d),
  asNumber(row.late_payments_12m),
  row.auto_pay,
  asNumber(row.satisfaction_score),
  asNumber(row.clv_realized_usd),
  asNumber(row.annualized_revenue_lost_usd),
]);

const monthlyMatrix = monthlyParsed.rows.map((row) => [
  asDate(row.month),
  asNumber(row.active_start),
  asNumber(row.new_customers),
  asNumber(row.churned_customers),
  asNumber(row.active_end),
  asNumber(row.churn_rate),
  asNumber(row.monthly_recurring_revenue_lost_usd),
  asNumber(row.annualized_revenue_lost_usd),
]);

const contractSummary = summarize(customerRows, "contract_type");
const paymentSummary = summarize(customerRows, "payment_method");
const serviceSummary = summarize(customerRows, "service_category");
const tenureSummary = summarize(customerRows, "tenure_band");

const wb = Workbook.create();
const summary = wb.worksheets.add("Resumen");
const monthly = wb.worksheets.add("Evolución mensual");
const segments = wb.worksheets.add("Segmentos");
const customers = wb.worksheets.add("Clientes");
const dictionary = wb.worksheets.add("Diccionario");

const font = "Arial";
const purple = "#8F6AA8";
const dark = "#2F2436";
const light = "#F6F1F8";
const border = "#DED6E2";
const green = "#2F855A";
const red = "#C2415B";

for (const sheet of [summary, monthly, segments, customers, dictionary]) {
  sheet.showGridLines = false;
  sheet.getRange("A1:U200").format.font = { name: font, size: 10, color: dark };
}

summary.getRange("A1:L1").merge();
summary.getRange("A1").values = [["Customer churn: retención y valor económico"]];
summary.getRange("A1").format.font = { name: font, size: 18, bold: true, color: purple };
summary.getRange("A2:L2").merge();
summary.getRange("A2").values = [["Datos simulados · Enero 2023 a diciembre 2025 · Fecha de corte 2025-12-31"]];
summary.getRange("A2").format.font = { name: font, size: 10, italic: true, color: "#6B6570" };
summary.getRange("A3:L3").format.borders = { bottom: { style: "thin", color: border } };

const lastCustomerRow = customerMatrix.length + 1;
const cardSpecs = [
  ["A5:B5", "A6:B6", "Clientes", `=COUNTA(Clientes!A2:A${lastCustomerRow})`, "#,##0"],
  ["C5:D5", "C6:D6", "Bajas", `=SUM(Clientes!E2:E${lastCustomerRow})`, "#,##0"],
  ["E5:F5", "E6:F6", "Churn global", "=C6/A6", "0.0%"],
  ["G5:H5", "G6:H6", "Ingreso anualizado perdido", `=SUM(Clientes!U2:U${lastCustomerRow})`, '"USD "#,##0'],
  ["I5:J5", "I6:J6", "CLV promedio bajas", `=SUMIF(Clientes!E2:E${lastCustomerRow},1,Clientes!T2:T${lastCustomerRow})/COUNTIF(Clientes!E2:E${lastCustomerRow},1)`, '"USD "#,##0'],
  ["K5:L5", "K6:L6", "CLV promedio activos", `=SUMIF(Clientes!E2:E${lastCustomerRow},0,Clientes!T2:T${lastCustomerRow})/COUNTIF(Clientes!E2:E${lastCustomerRow},0)`, '"USD "#,##0'],
];
for (const [labelRange, valueRange, label, formula, numberFormat] of cardSpecs) {
  summary.getRange(labelRange).merge();
  summary.getRange(valueRange).merge();
  summary.getRange(labelRange.split(":")[0]).values = [[label]];
  summary.getRange(valueRange.split(":")[0]).formulas = [[formula]];
  summary.getRange(valueRange).format.numberFormat = numberFormat;
}

for (const card of ["A5:B6", "C5:D6", "E5:F6", "G5:H6", "I5:J6", "K5:L6"]) {
  summary.getRange(card).format.fill = light;
  summary.getRange(card).format.borders = { preset: "outside", style: "thin", color: border };
}
summary.getRange("A5:L5").format.font = { name: font, size: 9, bold: true, color: "#6B6570" };
summary.getRange("A6:L6").format.font = { name: font, size: 13, bold: true, color: dark };

summary.getRange("A9:F9").values = [["Contrato", "Clientes", "Bajas", "Churn", "CLV promedio", "Ingreso perdido anualizado"]];
summary.getRange(`A10:F${9 + contractSummary.length}`).values = contractSummary;
summary.getRange("H9:M9").values = [["Método de pago", "Clientes", "Bajas", "Churn", "CLV promedio", "Ingreso perdido anualizado"]];
summary.getRange(`H10:M${9 + paymentSummary.length}`).values = paymentSummary;
summary.getRange("A9:F9").format = { fill: dark, font: { name: font, size: 10, bold: true, color: "#FFFFFF" } };
summary.getRange("H9:M9").format = { fill: dark, font: { name: font, size: 10, bold: true, color: "#FFFFFF" } };
summary.getRange(`D10:D${9 + contractSummary.length}`).format.numberFormat = "0.0%";
summary.getRange(`E10:F${9 + contractSummary.length}`).format.numberFormat = '"USD "#,##0';
summary.getRange(`K10:K${9 + paymentSummary.length}`).format.numberFormat = "0.0%";
summary.getRange(`L10:M${9 + paymentSummary.length}`).format.numberFormat = '"USD "#,##0';

const monthlyHeaders = ["Mes", "Activos iniciales", "Altas", "Bajas", "Activos finales", "Churn", "MRR perdido", "Ingreso perdido anualizado"];
monthly.getRange("A1:H1").merge();
monthly.getRange("A1").values = [["Evolución mensual"]];
monthly.getRange("A1").format.font = { name: font, size: 16, bold: true, color: purple };
monthly.getRange("A3:H3").values = [monthlyHeaders];
monthly.getRange(`A4:H${3 + monthlyMatrix.length}`).values = monthlyMatrix;
monthly.getRange("A3:H3").format = { fill: dark, font: { name: font, size: 10, bold: true, color: "#FFFFFF" } };
monthly.getRange(`A4:A${3 + monthlyMatrix.length}`).format.numberFormat = "mmm yyyy";
monthly.getRange(`B4:E${3 + monthlyMatrix.length}`).format.numberFormat = "#,##0";
monthly.getRange(`F4:F${3 + monthlyMatrix.length}`).format.numberFormat = "0.0%";
monthly.getRange(`G4:H${3 + monthlyMatrix.length}`).format.numberFormat = '"USD "#,##0';
monthly.freezePanes.freezeRows(3);
monthly.tables.add(`A3:H${3 + monthlyMatrix.length}`, true, "MonthlyKPI").style = "TableStyleMedium4";

const monthLabelMatrix = monthlyParsed.rows.map((row) => {
  const date = asDate(row.month);
  return [date.toLocaleDateString("en-US", { month: "short", year: "numeric" }), asNumber(row.churn_rate)];
});
monthly.getRange("S3:T3").values = [["Mes", "Churn"]];
monthly.getRange(`S4:T${3 + monthLabelMatrix.length}`).values = monthLabelMatrix;
const lineChart = monthly.charts.add("line", monthly.getRange(`S3:T${3 + monthLabelMatrix.length}`));
lineChart.title = "Tasa de churn mensual";
lineChart.titleTextStyle.typeface = font;
lineChart.hasLegend = false;
lineChart.xAxis = { axisType: "textAxis", textStyle: { typeface: font, fontSize: 9 } };
lineChart.yAxis = { numberFormatCode: "0.0%", numberFormatSourceLinked: false, textStyle: { typeface: font } };
lineChart.series.items[0].line = { color: purple, width: 2 };
lineChart.setPosition("J3", "Q18");

segments.getRange("A1:F1").merge();
segments.getRange("A1").values = [["Segmentación de churn"]];
segments.getRange("A1").format.font = { name: font, size: 16, bold: true, color: purple };

function writeSegmentTable(startRow, title, rows) {
  segments.getRange(`A${startRow}:F${startRow}`).merge();
  segments.getRange(`A${startRow}`).values = [[title]];
  segments.getRange(`A${startRow}`).format.font = { name: font, size: 12, bold: true, color: purple };
  segments.getRange(`A${startRow + 1}:F${startRow + 1}`).values = [["Segmento", "Clientes", "Bajas", "Churn", "CLV promedio", "Ingreso perdido anualizado"]];
  segments.getRange(`A${startRow + 2}:F${startRow + 1 + rows.length}`).values = rows;
  segments.getRange(`A${startRow + 1}:F${startRow + 1}`).format = { fill: dark, font: { name: font, size: 10, bold: true, color: "#FFFFFF" } };
  segments.getRange(`D${startRow + 2}:D${startRow + 1 + rows.length}`).format.numberFormat = "0.0%";
  segments.getRange(`E${startRow + 2}:F${startRow + 1 + rows.length}`).format.numberFormat = '"USD "#,##0';
}

writeSegmentTable(3, "Por categoría de servicio", serviceSummary);
writeSegmentTable(12, "Por antigüedad", tenureSummary);
writeSegmentTable(22, "Por método de pago", paymentSummary);

const segmentChart = segments.charts.add("bar", [segments.getRange(`A5:A${4 + serviceSummary.length}`), segments.getRange(`F5:F${4 + serviceSummary.length}`)]);
segmentChart.title = "Ingreso anualizado perdido por servicio";
segmentChart.titleTextStyle.typeface = font;
segmentChart.hasLegend = false;
segmentChart.xAxis = { axisType: "textAxis", textStyle: { typeface: font } };
segmentChart.yAxis = { numberFormatCode: '"USD "#,##0', numberFormatSourceLinked: false, textStyle: { typeface: font } };
segmentChart.series.items[0].fill = purple;
segmentChart.setPosition("H3", "N17");

const customerHeaders = [
  "customer_id", "signup_date", "churn_date", "snapshot_date", "churn_flag", "status", "tenure_months", "tenure_band", "contract_type", "payment_method", "service_category", "region", "customer_segment", "monthly_charge_usd", "avg_discount_pct", "support_tickets_90d", "late_payments_12m", "auto_pay", "satisfaction_score", "clv_realized_usd", "annualized_revenue_lost_usd",
];
customers.getRange("A1:U1").values = [customerHeaders];
customers.getRange(`A2:U${lastCustomerRow}`).values = customerMatrix;
customers.getRange("A1:U1").format = { fill: dark, font: { name: font, size: 9, bold: true, color: "#FFFFFF" }, wrapText: true };
customers.getRange(`B2:D${lastCustomerRow}`).format.numberFormat = "yyyy-mm-dd";
customers.getRange(`N2:N${lastCustomerRow}`).format.numberFormat = '"USD "#,##0.00';
customers.getRange(`O2:O${lastCustomerRow}`).format.numberFormat = "0.0%";
customers.getRange(`T2:U${lastCustomerRow}`).format.numberFormat = '"USD "#,##0.00';
customers.freezePanes.freezeRows(1);
customers.freezePanes.freezeColumns(1);
customers.tables.add(`A1:U${lastCustomerRow}`, true, "Customers").style = "TableStyleMedium4";
customers.getRange(`E2:E${lastCustomerRow}`).conditionalFormats.add("cellIs", { operator: "equal", formula: 1, format: { fill: "#FDE8EC", font: { color: red, bold: true } } });

const dictionaryRows = [
  ["customer_id", "Identificador único del cliente", "Texto"],
  ["signup_date", "Fecha de alta", "Fecha"],
  ["churn_date", "Fecha de baja; vacío si continúa activo", "Fecha"],
  ["snapshot_date", "Fecha de corte del análisis", "Fecha"],
  ["churn_flag", "1 si el cliente se dio de baja; 0 si permanece activo", "Entero"],
  ["tenure_months", "Meses observados desde el alta hasta la baja o fecha de corte", "Entero"],
  ["monthly_charge_usd", "Cargo mensual antes del descuento", "USD"],
  ["avg_discount_pct", "Descuento medio aplicado", "Porcentaje"],
  ["support_tickets_90d", "Tickets de soporte de los últimos 90 días", "Entero"],
  ["clv_realized_usd", "Cargo mensual × meses activos × (1 − descuento)", "USD"],
  ["annualized_revenue_lost_usd", "Cargo mensual × 12 para clientes dados de baja", "USD"],
  ["monthly churn rate", "Bajas del mes / activos al inicio del mes", "Porcentaje"],
];
dictionary.getRange("A1:C1").merge();
dictionary.getRange("A1").values = [["Diccionario y definiciones"]];
dictionary.getRange("A1").format.font = { name: font, size: 16, bold: true, color: purple };
dictionary.getRange("A3:C3").values = [["Campo o KPI", "Definición", "Tipo / unidad"]];
dictionary.getRange(`A4:C${3 + dictionaryRows.length}`).values = dictionaryRows;
dictionary.getRange("A3:C3").format = { fill: dark, font: { name: font, size: 10, bold: true, color: "#FFFFFF" } };
dictionary.getRange(`A4:C${3 + dictionaryRows.length}`).format.wrapText = true;
dictionary.getRange("A18:C18").merge();
dictionary.getRange("A18").values = [["Limitación: el CLV realizado de clientes activos está censurado a la fecha de corte y no representa todo su valor futuro."]];
dictionary.getRange("A18").format = { fill: "#FFF4D6", font: { name: font, size: 10, italic: true, color: "#6B4E00" }, wrapText: true };

for (const sheet of [summary, monthly, segments, customers, dictionary]) {
  const used = sheet.getUsedRange();
  used.format.autofitColumns();
  used.format.autofitRows();
}

summary.getRange("A:M").format.columnWidth = 14;
summary.getRange("A:A").format.columnWidth = 20;
summary.getRange("H:H").format.columnWidth = 22;
summary.getRange("F:F").format.columnWidth = 25;
summary.getRange("M:M").format.columnWidth = 25;
monthly.getRange("A:H").format.columnWidth = 18;
monthly.getRange("H:H").format.columnWidth = 25;
segments.getRange("A:A").format.columnWidth = 23;
segments.getRange("B:F").format.columnWidth = 18;
customers.getRange("A:U").format.columnWidth = 16;
customers.getRange("J:K").format.columnWidth = 23;
customers.getRange("P:Q").format.columnWidth = 21;
customers.getRange("T:U").format.columnWidth = 26;
dictionary.getRange("A:A").format.columnWidth = 27;
dictionary.getRange("B:B").format.columnWidth = 65;
dictionary.getRange("C:C").format.columnWidth = 18;

summary.getRange(`D10:D${9 + contractSummary.length}`).conditionalFormats.add("colorScale", { colors: ["#E6F4EA", "#FFF3CD", "#F8D7DA"], thresholds: ["min", { type: "percentile", value: 50 }, "max"] });
summary.getRange(`K10:K${9 + paymentSummary.length}`).conditionalFormats.add("colorScale", { colors: ["#E6F4EA", "#FFF3CD", "#F8D7DA"], thresholds: ["min", { type: "percentile", value: 50 }, "max"] });

await fs.mkdir(outputDir, { recursive: true });
await fs.mkdir(previewDir, { recursive: true });

const inspectSummary = await wb.inspect({ kind: "table", sheetId: "Resumen", range: "A1:M14", include: "values,formulas", tableMaxRows: 20, tableMaxCols: 14 });
console.log(inspectSummary.ndjson);
const errors = await wb.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 100 }, summary: "final formula error scan" });
console.log(errors.ndjson);

for (const [sheetName, range] of [["Resumen", "A1:M14"], ["Evolución mensual", "A1:Q20"], ["Segmentos", "A1:N33"], ["Clientes", "A1:U18"], ["Diccionario", "A1:C18"]]) {
  const preview = await wb.render({ sheetName, range, scale: 1.3, format: "png" });
  await fs.writeFile(path.join(previewDir, `${sheetName.replaceAll(" ", "_")}.png`), new Uint8Array(await preview.arrayBuffer()));
}

const output = await SpreadsheetFile.exportXlsx(wb);
await output.save(path.join(outputDir, "Customer_Churn_Etapa1.xlsx"));
console.log(path.join(outputDir, "Customer_Churn_Etapa1.xlsx"));
