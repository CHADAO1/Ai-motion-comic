#!/usr/bin/env node
/**
 * build_xlsx.mjs — 把 assets.json 生成《资产总表.xlsx》
 * 用法:   node build_xlsx.mjs <assets.json> [output.xlsx]
 * 映射:   rules/table.md TBL-02(13列) / TBL-06(schema) / TBL-08(说明sheet)
 * 依赖:   无第三方包 —— 内置最小 xlsx(OOXML+ZIP deflate) 写入器
 * 输出:   Sheet1《资产总表》= 全部资产行; Sheet2《说明》= 字段释义+统计+使用建议
 *         stdout 打印统计行(各类型行数/高风险数/需参考图数) 作为 S3 通过证据
 */
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { deflateRawSync } from "node:zlib";
import { dirname, join } from "node:path";

/* ---------- ZIP 写入器 ---------- */
const CRC_TABLE = (() => {
  const t = new Int32Array(256);
  for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; t[n] = c; }
  return t;
})();
const crc32 = (buf) => { let c = -1; for (let i = 0; i < buf.length; i++) c = CRC_TABLE[(c ^ buf[i]) & 0xff] ^ (c >>> 8); return (c ^ -1) >>> 0; };
const u16w = (b, o, v) => b.writeUInt16LE(v & 0xffff, o);
const u32w = (b, o, v) => b.writeUInt32LE(v >>> 0, o);

function makeZip(files) {
  const parts = [], centrals = [];
  let offset = 0;
  for (const f of files) {
    const nameBuf = Buffer.from(f.name, "utf8");
    const comp = deflateRawSync(f.data);
    const crc = crc32(f.data);
    const lh = Buffer.alloc(30);
    u32w(lh, 0, 0x04034b50); u16w(lh, 4, 20); u16w(lh, 6, 0); u16w(lh, 8, 8);
    u16w(lh, 10, 0); u16w(lh, 12, 0);
    u32w(lh, 14, crc); u32w(lh, 18, comp.length); u32w(lh, 22, f.data.length);
    u16w(lh, 26, nameBuf.length); u16w(lh, 28, 0);
    parts.push(lh, nameBuf, comp);
    const ch = Buffer.alloc(46);
    u32w(ch, 0, 0x02014b50); u16w(ch, 4, 20); u16w(ch, 6, 20); u16w(ch, 8, 0); u16w(ch, 10, 8);
    u16w(ch, 12, 0); u16w(ch, 14, 0);
    u32w(ch, 16, crc); u32w(ch, 20, comp.length); u32w(ch, 24, f.data.length);
    u16w(ch, 28, nameBuf.length); u16w(ch, 30, 0); u16w(ch, 32, 0); u16w(ch, 34, 0); u16w(ch, 36, 0);
    u32w(ch, 38, 0); u32w(ch, 42, offset);
    centrals.push(ch, nameBuf);
    offset += 30 + nameBuf.length + comp.length;
  }
  const cdStart = offset;
  let cdSize = 0; for (const b of centrals) cdSize += b.length;
  const eocd = Buffer.alloc(22);
  u32w(eocd, 0, 0x06054b50); u16w(eocd, 8, files.length); u16w(eocd, 10, files.length);
  u32w(eocd, 12, cdSize); u32w(eocd, 16, cdStart);
  return Buffer.concat([...parts, ...centrals, eocd]);
}

/* ---------- XML 工具 ---------- */
const esc = (v) => String(v ?? "")
  .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
  .replace(/"/g, "&quot;").replace(/\r?\n/g, "&#10;");
function colLetter(i) { let s = ""; i++; while (i > 0) { s = String.fromCharCode(65 + (i - 1) % 26) + s; i = Math.floor((i - 1) / 26); } return s; }

/** rows: string|number[][]; widths: number[]; 返回 worksheet xml */
function sheetXml(rows, widths) {
  const lastCol = colLetter(Math.max(...rows.map((r) => r.length)) - 1);
  const lastRow = rows.length;
  let xml = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>
<cols>${widths.map((w, i) => `<col min="${i + 1}" max="${i + 1}" width="${w}" customWidth="1"/>`).join("")}</cols>
<sheetData>`;
  rows.forEach((row, ri) => {
    const style = ri === 0 ? ' s="1"' : ' s="2"';
    xml += `<row r="${ri + 1}">`;
    row.forEach((cell, ci) => {
      const ref = `${colLetter(ci)}${ri + 1}`;
      if (typeof cell === "number" && Number.isFinite(cell)) {
        xml += `<c r="${ref}"${ri === 0 ? ' s="1"' : ""}><v>${cell}</v></c>`;
      } else {
        xml += `<c r="${ref}"${style} t="inlineStr"><is><t xml:space="preserve">${esc(cell)}</t></is></c>`;
      }
    });
    xml += `</row>`;
  });
  xml += `</sheetData><autoFilter ref="A1:${lastCol}${lastRow}"/></worksheet>`;
  return xml;
}

function workbookXml(sheetNames) {
  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>${sheetNames
    .map((n, i) => `<sheet name="${esc(n)}" sheetId="${i + 1}" r:id="rId${i + 1}"/>`).join("")}</sheets></workbook>`;
}
function wbRels(n) {
  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">${Array.from({ length: n }, (_, i) => `<Relationship Id="rId${i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet${i + 1}.xml"/>`).join("")}<Relationship Id="rId${n + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>`;
}
function contentTypes(n) {
  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>${Array.from({ length: n }, (_, i) => `<Override PartName="/xl/worksheets/sheet${i + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>`).join("")}</Types>`;
}
const STYLES_XML = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><fonts count="2"><font><sz val="11"/><name val="微软雅黑"/></font><font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="微软雅黑"/></font></fonts><fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF305496"/><bgColor indexed="64"/></patternFill></fill></fills><borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="3"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1" applyAlignment="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf></cellXfs></styleSheet>`;

/* ---------- 主流程: schema(TBL-06) -> 13列行(TBL-02) ---------- */
const [, , jsonPath, outArg] = process.argv;
if (!jsonPath) { console.error("用法: node build_xlsx.mjs <assets.json> [output.xlsx]"); process.exit(2); }
const data = JSON.parse(readFileSync(jsonPath, "utf8").replace(/^\uFEFF/, ""));
const outPath = outArg ?? join(dirname(jsonPath), "..", "outputs", "资产总表.xlsx");

const HEADERS = ["资产ID", "类型", "名称", "状态/视角", "外观描述", "与基础态差异点", "出现场次", "出现次数", "时段氛围", "连镜风险", "需独立参考图", "音色关联", "备注"];
const WIDTHS = [15, 10, 16, 18, 58, 26, 34, 9, 11, 10, 13, 18, 42];
const rows = [HEADERS];
const stats = { 角色: 0, 道具: 0, 场景: 0, 特效: 0, 状态视角行: 0, 高风险: 0, 需参考图: 0 };

const push = (id, type, name, sub, look, diff, eps, count, time, risk, ref, voice, note) => {
  rows.push([id ?? "", type, name ?? "", sub ?? "", look ?? "", diff ?? "", Array.isArray(eps) ? eps.join("、") : eps ?? "", typeof count === "number" ? count : (count || ""), time ?? "", risk ?? "", ref ?? "", voice ?? "", note ?? ""]);
  if (type === "角色") stats.角色++; else if (type === "道具") stats.道具++; else if (type === "场景") stats.场景++; else if (type === "特效") stats.特效++; else stats.状态视角行++;
  if (risk === "高") stats.高风险++;
  if (ref === "是") stats.需参考图++;
};

for (const c of data.characters ?? []) {
  push(c.id, "角色", c.name, "基础形象", c.baseLook, "—（本行即基础态）", c.eps, c.count, c.time, c.risk, c.needRef ?? "是", c.voiceRef, c.note);
  for (const s of c.states ?? [])
    push(s.sid, "角色状态", c.name, s.state, s.look, s.diff, s.eps, s.count, s.time, s.risk, s.needRef, c.voiceRef, s.note);
}
for (const p of data.props ?? []) {
  push(p.id, "道具", p.name, "完整形象", p.baseLook, "—（本行即基础态）", p.eps, p.count, p.time, p.risk, p.needRef, "", [p.owner ? `持有：${p.owner}` : "", p.note].filter(Boolean).join("；"));
  for (const s of p.states ?? [])
    push(s.sid, "道具状态", p.name, s.state, s.look, s.diff, s.eps, s.count, s.time, s.risk, s.needRef, "", s.note);
}
for (const sc of data.scenes ?? []) {
  push(sc.id, "场景", sc.name, "整体空间", sc.baseLook, "—（本行即基础态）", sc.eps, sc.count, sc.time, sc.risk, sc.needRef, "", sc.note);
  for (const v of sc.views ?? [])
    push(v.vid, "场景视角", sc.name, v.view, v.look, v.diff ?? "局部区域/阶段状态", v.eps, v.count, v.time, v.risk, v.needRef, "", v.note);
}
for (const f of data.fx ?? [])
  push(f.id, "特效", f.name, f.carrier ? `载体：${f.carrier}` : "", f.look, "—", f.eps, f.count, f.time, f.risk, f.needRef, "", f.note);

/* ---------- 说明 sheet (TBL-08) ---------- */
const fieldDocs = [
  ["资产ID", "唯一编号：CHAR-nn 角色 / PROP-nn 道具 / SCENE-nn 场景 / FX-nn 特效；-Sk 状态、-Vk 视角为派生行"],
  ["类型", "角色 / 角色状态 / 道具 / 道具状态 / 场景 / 场景视角 / 特效"],
  ["名称", "主体名称（角色名、道具名、场景名）"],
  ["状态/视角", "该行的具体外观状态或空间视角；基础行为『基础形象』"],
  ["外观描述", "可直接喂给文生图的中文外观参考描述"],
  ["与基础态差异点", "只写与基础形象的差异，便于换装/换状态时改提示词"],
  ["出现场次", "集-场 格式，如 2-1、2-3；闪回标注 (闪回)"],
  ["出现次数", "出现的场次数量（同场多镜头算 1 次）"],
  ["时段氛围", "日/夜/黄昏等，影响灯光方案"],
  ["连镜风险", "高=跨集或连续动作段复用，必须锁定；中=同集多场；低=单场可现场生成"],
  ["需独立参考图", "是=必须先生成参考图给视频AI；建议=有余力再做；否=交给视频AI自由发挥"],
  ["音色关联", "对应音色设计文档中的角色条目，仅角色行填写"],
  ["备注", "连镜对位关系、豁免理由、剧本未指定项等待美术确认的内容"],
];
const tips = [
  "生成顺序建议：先做所有 needRef=是 的行（主角基础形象 → 高风险状态 → 主场景 → 核心道具/特效），再用『建议』行补齐。",
  "视频 AI 锁定用法：同一角色的所有状态图共用同一张脸的种子/参考；场景 V 行各自出一张机位参考，剪辑到该区域时挂对应图。",
  "needRef=否 的行不必预生成，直接在视频提示词里按『外观描述』文字生成即可。",
  "带文字的道具（信件/手记/树皮留言）先把文字内容排版好再生成，保证字迹前后一致。",
  "双人特效（印记/融合光流）建议生成含双方的构图参考，避免左右两侧不一致。",
];
let infoRows = [["《" + (data.drama ?? "") + "》剧本资产总表 — 字段说明"]];
infoRows.push(["字段", "释义"]);
for (const [a, b] of fieldDocs) infoRows.push([a, b]);
infoRows.push([], [["统计"]]);
infoRows.push(["指标", "数值"]);
infoRows.push(["总集数", data.episodes ?? ""]);
infoRows.push(["角色档（基础）", stats.角色]);
infoRows.push(["道具档（基础）", stats.道具]);
infoRows.push(["场景档（基础）", stats.场景]);
infoRows.push(["特效档", stats.特效]);
infoRows.push(["状态/视角派生行", stats.状态视角行]);
infoRows.push(["总行数（含表头）", rows.length]);
infoRows.push(["高风险行", stats.高风险]);
infoRows.push(["需独立参考图(是)", stats.需参考图]);
infoRows.push([], [["使用建议"]]);
tips.forEach((t, i) => infoRows.push([`${i + 1}.`, t]));

/* ---------- 打包 ---------- */
const sheets = [
  { name: "资产总表", xml: sheetXml(rows, WIDTHS) },
  { name: "说明", xml: sheetXml(infoRows, [22, 110]) },
];
const files = [
  { name: "[Content_Types].xml", data: Buffer.from(contentTypes(sheets.length), "utf8") },
  { name: "_rels/.rels", data: Buffer.from(`<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>`, "utf8") },
  { name: "xl/workbook.xml", data: Buffer.from(workbookXml(sheets.map((s) => s.name)), "utf8") },
  { name: "xl/_rels/workbook.xml.rels", data: Buffer.from(wbRels(sheets.length), "utf8") },
  { name: "xl/styles.xml", data: Buffer.from(STYLES_XML, "utf8") },
  ...sheets.map((s, i) => ({ name: `xl/worksheets/sheet${i + 1}.xml`, data: Buffer.from(s.xml, "utf8") })),
];
mkdirSync(dirname(outPath), { recursive: true });
writeFileSync(outPath, makeZip(files));

console.log(`OK ${outPath}`);
console.log(`总行数=${rows.length - 1} 角色=${stats.角色} 道具=${stats.道具} 场景=${stats.场景} 特效=${stats.特效} 派生行=${stats.状态视角行} 高风险=${stats.高风险} 需参考图=${stats.需参考图}`);
