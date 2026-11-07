#!/usr/bin/env node
/**
 * estimate_timeline.mjs — 台词/表演估时 + 30s 拆段计算（确定性计算，AI 只复核创意合理性）
 *
 * 用法:
 *   node estimate_timeline.mjs <input.json> [--model 2.5|2.0] [--out <result.json>]
 *
 * 段上限由 --model 决定（2.0=15s / 2.5=30s），不接受 --max-seconds。
 *
 * 输入 JSON 结构:
 * {
 *   "defaults": { "speechRateWps": 2.5, "speechRateCps": 4.0, "actionSeconds": 1.5 },
 *   "beats": [
 *     { "id": "b01", "speaker": "塞拉",
 *       "dialogueEn": "...", "dialogueZh": "...",
 *       "actions": [{"desc":"撑地起身","seconds":1.5}],
 *       "moves":   [{"seconds":3}],
 *       "pauses":  [{"seconds":1}] }
 *   ],
 *   "hardBreakAfter": ["b03"]
 * }
 *
 * 估时口径（按台词语言二选一，看哪个字段有内容）:
 *   - 英文管线: 有 dialogueEn → 词数 ÷ defaults.speechRateWps（默认 2.5 词/秒）
 *   - 中文管线: 只有 dialogueZh → 字数 ÷ defaults.speechRateCps（P1 3.5 / P2-P3 4.0 字/秒）
 *   两者都有时以 dialogueEn 为准（英文优先）。
 *
 * 规则映射: TIME-01 台词口径估时; TIME-02 段上限(2.5=30s,30-31可压缩; 2.0=15s);
 *          CLOSE-01 以台词结尾的段自动标记 needsClosingShot 并预留 0.75s。
 */
import { readFileSync, writeFileSync } from "node:fs";

const CAP = { "2.5": 30, "2.0": 15 };
const CLOSE_RESERVE = 0.75;
const COMPRESS_TOL = 1; // TIME-02: 30-31s 可压缩进 30s

function fail(msg) { console.error("ERROR:", msg); process.exit(1); }

function parseArgs(argv) {
  const args = { model: "2.5", out: null, input: null };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--model") { args.model = argv[++i]; }
    else if (a === "--out") { args.out = argv[++i]; }
    else if (!args.input) { args.input = a; }
    else { fail(`unexpected argument: ${a}`); }
  }
  if (!args.input) fail("usage: node estimate_timeline.mjs <input.json> [--model 2.5|2.0] [--out result.json]");
  if (!(args.model in CAP)) fail(`--model must be 2.5 or 2.0, got: ${args.model}`);
  return args;
}

function countEnglishWords(text) {
  if (!text || typeof text !== "string") return 0;
  const t = text.replace(/^\uFEFF/, "");
  const m = t.match(/[\p{L}\p{N}][\p{L}\p{N}'’-]*/gu);
  return m ? m.length : 0;
}

// 中文字数：只数汉字，忽略标点、空白与英文字母
function countChineseChars(text) {
  if (!text || typeof text !== "string") return 0;
  const m = text.match(/\p{Script=Han}/gu);
  return m ? m.length : 0;
}

const r1 = (n) => Math.round(n * 10) / 10;

// 台词估时：英文优先（词/秒），无英文时回落到中文（字/秒）
function dialogueSeconds(b, d) {
  const en = countEnglishWords(b.dialogueEn);
  if (en > 0) return { seconds: en / (d.speechRateWps ?? 2.5), unit: "words", count: en };
  const zh = countChineseChars(b.dialogueZh ?? b.dialogue);
  if (zh > 0) return { seconds: zh / (d.speechRateCps ?? 3.5), unit: "chars", count: zh };
  return { seconds: 0, unit: "none", count: 0 };
}

// 单拍时长 = max(台词时长, 动作/运镜/停顿总时长)
//   —— 说话的人同时在走位/做动作，二者在画面上**并发**，不是串行相加。
//   早期版本用「台词 + 动作」求和，把"边说边做"的戏重复计时，导致整集虚增
//   （2026-09-10 第10集：35 拍虚增约 45s，被迫砍动作秒数来凑总时长）。
//   若某拍确实是「先说完、再做一个动作」（串行），应拆成两个拍点，而不是靠求和表达。
function beatSeconds(b, d) {
  const actDef = d.actionSeconds ?? 1.5;
  const dlg = dialogueSeconds(b, d).seconds;
  let act = 0;
  for (const a of b.actions ?? []) act += typeof a === "number" ? a : (a.seconds ?? actDef);
  for (const m of b.moves ?? []) act += typeof m === "number" ? m : (m.seconds ?? 1);
  for (const p of b.pauses ?? []) act += typeof p === "number" ? p : (p.seconds ?? 0.5);
  return r1(Math.max(dlg, act));
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const cap = CAP[args.model];
  let input;
  try {
    input = JSON.parse(readFileSync(args.input, "utf8").replace(/^\uFEFF/, ""));
  } catch (e) { fail(`cannot read/parse ${args.input}: ${e.message}`); }
  if (!Array.isArray(input.beats) || input.beats.length === 0) fail("input.beats must be a non-empty array");

  const d = input.defaults ?? {};
  const hardBreaks = new Set(input.hardBreakAfter ?? []);

  // 预计算每拍秒数
  const beats = input.beats.map((b, i) => {
    const id = b.id ?? `b${String(i + 1).padStart(2, "0")}`;
    const dlg = dialogueSeconds(b, d);
    const hasDialogue = dlg.count > 0;
    const sec = beatSeconds(b, d);
    return { id, speaker: b.speaker ?? "", hasDialogue, words: dlg.count, unit: dlg.unit, seconds: sec };
  });

  const warnings = [];
  const segments = [];
  let cur = [], curTotal = 0;

  const closeSeg = () => {
    if (cur.length === 0) return;
    const endsWithDialogue = cur[cur.length - 1].hasDialogue;
    const raw = r1(curTotal);
    let billed = raw, compressed = false, reserve = 0;
    if (raw > cap && raw <= cap + COMPRESS_TOL) { compressed = true; billed = cap; }
    if (endsWithDialogue) {
      reserve = CLOSE_RESERVE;
      const withReserve = r1(raw + reserve);
      if (withReserve > cap + COMPRESS_TOL) {
        warnings.push(`seg over cap after closing-shot reserve: ${withReserve}s > ${cap + COMPRESS_TOL}s — trim dialogue/actions by ~${r1(withReserve - cap)}s`);
      }
      // 收尾镜只在段已接近上限时才"吃掉"预算；低载段（<cap-RESERVE）保留实际估算，
      // 否则 5s 的戏会被记成 5.75s，多段累积后整集被虚增（2026-09-10 第10集压缩事故）。
      billed = withReserve <= cap
        ? withReserve
        : Math.min(cap, Math.max(billed, Math.min(withReserve, cap)));
      if (compressed && withReserve <= cap + COMPRESS_TOL) billed = cap;
    }
    segments.push({
      segId: `seg_${String(segments.length + 1).padStart(2, "0")}`,
      beatIds: cur.map((x) => x.id),
      estimatedSeconds: raw,
      closingShotReserve: endsWithDialogue ? reserve : 0,
      billedSeconds: r1(billed),
      compressed: compressed || undefined,
      needsClosingShot: endsWithDialogue || undefined
    });
    cur = []; curTotal = 0;
  };

  beats.forEach((b, idx) => {
    if (b.seconds > cap + COMPRESS_TOL) {
      warnings.push(`beat ${b.id} alone is ${b.seconds}s > cap+tolerance ${cap + COMPRESS_TOL}s — split the beat manually`);
    }
    if (cur.length > 0 && curTotal + b.seconds > cap + COMPRESS_TOL) closeSeg();
    cur.push(b); curTotal = r1(curTotal + b.seconds);
    if (hardBreaks.has(b.id)) closeSeg();
    if (idx === beats.length - 1) closeSeg();
  });

  const result = {
    tool: "estimate_timeline.mjs",
    generatedAt: new Date().toISOString(),
    model: args.model,
    capSeconds: cap,
    defaultSpeechRate: {
      wps: d.speechRateWps ?? 2.5,
      cps: d.speechRateCps ?? 3.5
    },
    totals: {
      beats: beats.length,
      estimatedSeconds: r1(beats.reduce((s, b) => s + b.seconds, 0)),
      segments: segments.length,
      billedSeconds: r1(segments.reduce((s, x) => s + x.billedSeconds, 0))
    },
    segments,
    perBeat: beats.map((b) => ({ id: b.id, speaker: b.speaker, words: b.words, unit: b.unit, seconds: b.seconds })),
    warnings
  };

  const json = JSON.stringify(result, null, 2);
  if (args.out) { writeFileSync(args.out, json, "utf8"); console.log(`written: ${args.out}`); }
  else console.log(json);

  for (const w of warnings) console.error("WARN:", w);
}

main();
