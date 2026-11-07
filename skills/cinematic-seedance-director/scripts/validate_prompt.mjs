#!/usr/bin/env node
/**
 * validate_prompt.mjs — Seedance 提示词交付格式自动校验（保守检查，避免误报）
 *
 * 用法:
 *   node validate_prompt.mjs <file.txt|dir> [more paths...] [--max 30]
 *
 * 校验项（对应规则）:
 *   P1 代码块第一行以【风格参考：开头            (FMT-01)
 *   P2 最后一行非空行匹配 [N]秒。W:H。           (FMT-02)
 *   P3 时长 ≤ 上限（超 0~1s 给 WARN 可压缩；>1s FAIL）(TIME-02)
 *   P4 提示词内无 ════/---- 分隔线行             (FMT-01)
 *   P5 无 "场景X｜"/"段X｜" 题头行               (FMT-01)
 *   P6 参考镜头数声明与【镜头n】块数一致（不一致仅 WARN）；旧"严格包含/禁止增减"死锁措辞告警 (NEG-03)
 *
 * 已知不检查: 中文反馈否定标注（PUR-04，误报率高，需人工按 PUR-05 自检）。
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, extname } from "node:path";

function parseArgs(argv) {
  const args = { max: 30, paths: [] };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--max") args.max = Number(argv[++i]);
    else args.paths.push(argv[i]);
  }
  if (args.paths.length === 0 || !Number.isFinite(args.max)) {
    console.error("usage: node validate_prompt.mjs <file.txt|dir> [...] [--max 30]");
    process.exit(1);
  }
  return args;
}

function listFiles(p) {
  const st = statSync(p);
  if (st.isFile()) return [p];
  const out = [];
  for (const name of readdirSync(p)) {
    const full = join(p, name);
    if (statSync(full).isFile() && extname(name).toLowerCase() === ".txt") out.push(full);
  }
  return out.sort();
}

function extractFencedBlocks(text) {
  const blocks = [];
  const re = /```[^\n]*\n([\s\S]*?)```/g;
  let m;
  while ((m = re.exec(text)) !== null) blocks.push(m[1]);
  return blocks.length ? blocks : [text]; // 纯文本无围栏时按整文件处理
}

function validateBlock(file, idx, block, max) {
  const lines = block.split(/\r?\n/);
  const nonEmpty = lines.map((l, i) => ({ l: l.trim(), n: i + 1 })).filter((x) => x.l.length > 0);
  const issues = [];
  const tag = `${file}#block${idx}`;

  // P1 首行风格参考
  if (!nonEmpty[0]?.l.startsWith("【风格参考：")) {
    issues.push({ p: "P1", level: "FAIL", msg: `first line must start with 【风格参考： got: "${(nonEmpty[0]?.l ?? "").slice(0, 40)}"` });
  }
  // P2 尾行时长+画幅
  const last = nonEmpty[nonEmpty.length - 1];
  const m = last?.l.match(/^\[(\d+(?:\.\d+)?)\]秒。\s*(\d+)\s*:\s*(\d+)\s*。?$/u);
  let dur = null;
  if (!m) {
    issues.push({ p: "P2", level: "FAIL", msg: `last non-empty line must match "[N]秒。H:H。" got: "${(last?.l ?? "").slice(0, 40)}"` });
  } else {
    dur = parseFloat(m[1]);
    // P3 时长上限（30-31 视为可压缩 WARN）
    if (dur > max && dur <= max + 1) issues.push({ p: "P3", level: "WARN", msg: `duration ${dur}s within compressible tolerance (${max}, ${max + 1}] — confirm it fits ${max}s` });
    else if (dur > max + 1) issues.push({ p: "P3", level: "FAIL", msg: `duration ${dur}s exceeds cap+tolerance ${max + 1}s` });
  }
  // P4 分隔线
  for (const { l } of nonEmpty) {
    if (/^[═=\-＿—─]{4,}$/u.test(l)) { issues.push({ p: "P4", level: "FAIL", msg: `separator line inside prompt: "${l.slice(0, 20)}"` }); break; }
  }
  // P5 题头行
  for (const { l } of nonEmpty) {
    if (/^(场景|段)\s*\S*\s*[｜|]/u.test(l)) { issues.push({ p: "P5", level: "FAIL", msg: `header line inside prompt: "${l.slice(0, 30)}"` }); break; }
  }
  // P6 镜头数量表述一致性（参考节奏，非硬约束）
  // 兼容新旧两种写法：
  //   新: "本段共N个镜头（参考节奏，非强制）"
  //   旧: "严格包含N个镜头——禁止增加或减少"
  // 旧写法的"严格/禁止增加或减少"已废弃（死锁），命中即 WARN 提示改写。
  const declared = [...block.matchAll(/(?:本段共|本提示词严格包含)(\d+)个镜头/gu)].map((x) => parseInt(x[1], 10));
  if (/严格包含\d+个镜头|禁止增加或减少/gu.test(block)) {
    issues.push({ p: "P6", level: "WARN", msg: "发现已废弃的镜头死锁措辞「严格包含N个镜头——禁止增加或减少」，请改用「本段共N个镜头（参考节奏，非强制）」" });
  }
  if (declared.length > 0) {
    const actual = new Set([...block.matchAll(/【镜头(\d+)】/gu)].map((x) => parseInt(x[1], 10))).size;
    for (const n of declared) {
      if (n !== actual) issues.push({ p: "P6", level: "WARN", msg: `declared reference shot count ${n} != actual 【镜头N】 blocks ${actual}（自由增删镜后需同步该数字）` });
      else issues.push({ p: "P6", level: "PASS", msg: `shot count ${n} == declared (reference)` });
    }
  }
  return { tag, issues };
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  let files = [];
  try { files = args.paths.flatMap(listFiles); }
  catch (e) { console.error("ERROR:", e.message); process.exit(1); }

  let failCount = 0, warnCount = 0, checked = 0;
  for (const f of files) {
    const text = readFileSync(f, "utf8").replace(/^\uFEFF/, "");
    const blocks = extractFencedBlocks(text);
    blocks.forEach((b, i) => {
      const r = validateBlock(f, i + 1, b, args.max);
      const fails = r.issues.filter((x) => x.level === "FAIL");
      const warns = r.issues.filter((x) => x.level === "WARN");
      failCount += fails.length; warnCount += warns.length; checked += 1;
      const status = fails.length ? "FAIL" : warns.length ? "WARN" : "PASS";
      console.log(`[${status}] ${r.tag}`);
      for (const x of r.issues) console.log(`   ${x.level} ${x.p}: ${x.msg}`);
    });
  }
  console.log(`\nchecked=${checked} fail=${failCount} warn=${warnCount}`);
  process.exitCode = failCount > 0 ? 1 : 0;
}

main();
