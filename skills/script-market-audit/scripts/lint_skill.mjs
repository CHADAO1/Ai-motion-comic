#!/usr/bin/env node
/**
 * lint_skill.mjs — 技能包一致性自检（通用版，由 skill-forge 提供）
 *
 * 用法: 复制本文件到目标技能包 scripts/ 后运行: node scripts/lint_skill.mjs
 *   （或任意位置: node lint_skill.mjs <技能根目录>）
 *
 * 检查项:
 *   C1 FAIL 悬空引用：SKILL.md/workflows/rules/review/reference/scripts/README/MAINTENANCE
 *      中引用的规则编号（形如「前缀-数字」）必须在 rules/*.md 或 review/*.md 中有定义。
 *      （无 rules/ 与 review/ 目录的技能自动跳过编号检查；CHANGELOG.md 不参与）
 *   C2 INFO 孤儿规则：定义文件之外从未被引用的编号——可能漏登记清单项，人工确认。
 *   C3 FAIL 路径腐烂：md 反引号内的包内相对路径、SKILL.md File Map 列出的文件必须真实存在。
 */
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const root = process.argv[2] ?? join(dirname(fileURLToPath(import.meta.url)), "..");
const ID_RE = /\b([A-Z]{2,6}-\d{2})\b/g;
const REF_DIRS = ["workflows", "rules", "review", "reference", "standards", "knowledge"];

function md(dir) {
  try { return readdirSync(dir).filter((f) => f.endsWith(".md")).map((f) => join(dir, f)); }
  catch { return []; }
}
function read(p) { return readFileSync(p, "utf8").replace(/^\uFEFF/, ""); }
function rel(p) { return p.slice(root.length + 1); }
function ids(text) { return [...text.matchAll(ID_RE)].map((m) => m[1]); }
function scripts() {
  try { return readdirSync(join(root, "scripts")).filter((f) => f.endsWith(".mjs") || f.endsWith(".js")).map((f) => join(root, "scripts", f)); }
  catch { return []; }
}

// ---- 定义区与引用区 ----
let defFiles = [...md(join(root, "rules")), ...md(join(root, "review"))];
defFiles = defFiles.filter((f) => existsSync(f));
const idCheckApplies = md(join(root, "rules")).length > 0 || defFiles.length > 0;

const defined = new Set();
for (const f of defFiles) for (const id of ids(read(f))) defined.add(id);

const refFiles = [
  join(root, "SKILL.md"), join(root, "README.md"), join(root, "MAINTENANCE.md"),
  ...REF_DIRS.flatMap((d) => md(join(root, d))),
  ...scripts()
].filter(existsSync);

let fails = 0, infos = 0;

// ---- C1 悬空引用 ----
if (!idCheckApplies) {
  console.log("[SKIP] C1/C2: 无 rules|review 定义目录，跳过规则编号检查");
} else {
  const defFileOf = new Map();
  for (const f of defFiles) for (const id of new Set(ids(read(f)))) if (!defFileOf.has(id)) defFileOf.set(id, rel(f));

  for (const f of refFiles) {
    const bad = [...new Set(ids(read(f)))].filter((id) => !defined.has(id));
    if (bad.length) { fails += bad.length; console.log(`[FAIL] C1 ${rel(f)}: 悬空引用 ${bad.join(", ")}`); }
  }

  // ---- C2 孤儿规则（INFO）----
  const orphans = new Map();
  for (const [id, defFile] of defFileOf) {
    const usedOutside = refFiles.some((f) => rel(f) !== defFile && ids(read(f)).includes(id));
    if (!usedOutside) orphans.set(defFile, [...(orphans.get(defFile) ?? []), id]);
  }
  if (orphans.size) {
    for (const [df, list] of orphans) {
      infos += list.length;
      console.log(`[INFO] C2 ${df}: 定义但未被外部引用 ×${list.length} -> ${list.join(", ")}`);
    }
    console.log("       （速查表类可忽略；核心规则请登记到审查清单项）");
  }
}

// ---- C3 路径检查：反引号内相对路径 ----
const DIR_RE = "(?:workflows|rules|review|reference|references|scripts|standards|templates|knowledge)";
const ROOT_MD_RE = /^(?:SKILL|README|MAINTENANCE|CHANGELOG)\.md$/;
const btFiles = [...refFiles.filter((f) => f.endsWith(".md")), join(root, "CHANGELOG.md")].filter(existsSync);
const badPaths = new Set();
for (const f of btFiles) {
  for (const m of read(f).matchAll(/`([^`\n]+)`/g)) {
    let t = m[1].trim().replace(/^node\s+/, "");
    if (/^(?:workflows|rules|review|reference|references|scripts|standards|templates|knowledge)[\\/][\w.\-\\/-]+$/.test(t)) {
      if (!existsSync(join(root, ...t.split(/[\\/]/)))) badPaths.add(`${rel(f)} -> ${t}`);
    } else if (ROOT_MD_RE.test(t)) {
      if (!existsSync(join(root, t))) badPaths.add(`${rel(f)} -> ${t}`);
    }
  }
}

// ---- C3 路径检查：SKILL.md File Map 围栏 ----
const skillText = existsSync(join(root, "SKILL.md")) ? read(join(root, "SKILL.md")) : "";
const fmMatch = skillText.match(/File Map[\s\S]*?```[\s\S]*?```/);
if (fmMatch) {
  let curDir = "";
  for (const line of fmMatch[0].split(/\r?\n/)) {
    const t = line.trim().split(/\s+/)[0] ?? "";
    if (!t || t.startsWith("```") || t.startsWith("#")) continue;
    if (t.endsWith("/")) { curDir = t.slice(0, -1); continue; }
    if (/\.(md|mjs|js)$/.test(t)) {
      const p = curDir ? join(root, curDir, t) : join(root, t);
      if (!existsSync(p)) badPaths.add(`SKILL.md FileMap -> ${curDir ? curDir + "/" : ""}${t}`);
    }
  }
}
for (const b of badPaths) { fails++; console.log(`[FAIL] C3 路径不存在: ${b}`); }

console.log(`\nroot=${root}`);
console.log(idCheckApplies ? `规则编号定义数=${defined.size}  ` : "") + `fail=${fails}  info(孤儿)=${infos}`;
process.exitCode = fails > 0 ? 1 : 0;
