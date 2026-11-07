#!/usr/bin/env node
/** build_split.mjs — 用 DP（非 BFS）在 [12,15]s 硬约束下求解切分并写出 03_拆段表.json */
import { readFileSync, writeFileSync } from "node:fs";
const r1 = (x) => Math.round(x * 10) / 10;
const cnt = (s) => { const m = String(s ?? "").match(/\p{Script=Han}/gu); return m ? m.length : 0; };

const args = process.argv.slice(2);
const inp = args[0] ?? "pipeline/01_拍点表.json";
const out = args[1] ?? "pipeline/03_拆段表.json";
const j = JSON.parse(readFileSync(inp, "utf8").replace(/^\uFEFF/, ""));
const cps = (j.defaults?.speechRateCps) ?? 4.0;

const S = j.beats.map((b) => {
  const dlg = cnt(b.dialogueZh) / cps;
  let act = 0;
  for (const x of b.actions ?? []) act += typeof x === "number" ? x : (x.seconds ?? 1.5);
  for (const x of b.moves ?? []) act += typeof x === "number" ? x : (x.seconds ?? 1);
  for (const x of b.pauses ?? []) act += typeof x === "number" ? x : (x.seconds ?? 0.5);
  return Math.max(dlg, act);
});
const N = S.length;
const pre = [0];
S.forEach((s) => pre.push(pre[pre.length - 1] + s));

const LO = 12, HI = 15;
const IDX = (v) => Math.round(v * 1000);

// 场景切换点：10-1 场(索引 0..12) 与 10-2 场(索引 12..N) 不可跨段并（RT-07-3 跨空间禁并段）
const SCENE_BREAK = 12;

// DP 正向：f[k] = 到达索引 k 的段数（取最少），from[k] = 前驱索引
const f = new Array(N + 1).fill(Infinity), from = new Array(N + 1).fill(-1);
f[0] = 0;
for (let i = 0; i <= N; i++) {
  if (f[i] === Infinity) continue;
  for (let k = i + 1; k <= N; k++) {
    // 禁止跨越场次边界
    if (i < SCENE_BREAK && k > SCENE_BREAK) continue;
    const s = pre[k] - pre[i];
    if (IDX(s) > IDX(HI)) break;
    if (IDX(s) < IDX(LO)) continue;
    if (f[i] + 1 < f[k]) { f[k] = f[i] + 1; from[k] = i; }
  }
}
if (f[N] === Infinity) {
  console.error(`无解：内容量 ${r1(pre[N])}s 无法切成每段 [${LO},${HI}]s`);
  process.exit(2);
}
const cuts = [];
let cc = N;
while (cc > 0) { const i = from[cc]; cuts.unshift([i, cc]); cc = i; }

const segs = cuts.map(([i, k], n) => {
  const slice = j.beats.slice(i, k);
  const scene = i < 12 ? "10-1" : "10-2";
  const ord = cuts.filter(([a], m) => m <= n && (a < 12 ? "10-1" : "10-2") === scene).length;
  return {
    segId: `seg_${String(n + 1).padStart(2, "0")}`,
    index: n + 1,
    scene,
    promptFile: `${scene}-${ord}`,   // outputs/<此名>.txt —— 供门2 精确绑定
    beatIds: slice.map((b) => b.id),
    estimatedSeconds: r1(pre[k] - pre[i]),
    dialogueCount: slice.filter((b) => cnt(b.dialogueZh) > 0).length,
    panelCount: slice.reduce((s, b) => s + (b.panel ? b.panel.length : 0), 0),
    endsWithDialogue: cnt(j.beats[k - 1].dialogueZh) > 0,
    // 门1 校验用：每拍一行「台词」文本（有台词则原样，无台词则该拍的面板/动作摘要）
    beats: slice.map((b, m) => {
      const dlg = String(b.dialogueZh ?? "").trim();
      if (dlg) return dlg;
      const panels = (b.panel ?? []).join("");
      const acts = (b.actions ?? []).map((a) => a.desc).join("；");
      return panels ? `${panels}｜${acts}` : acts;
    }),
    // 结构化明细（供 S4 编译提示词使用）
    detail: slice.map((b, m) => ({
      id: b.id, speaker: b.speaker ?? "", dialogueZh: b.dialogueZh ?? "",
      panel: b.panel ?? [], actions: (b.actions ?? []).map((a) => a.desc),
      seconds: r1(S[i + m]), emotion: b.emotion ?? ""
    }))
  };
});

const result = {
  tool: "build_split.mjs",
  generatedAt: new Date().toISOString(),
  constraint: { lo: LO, hi: HI, model: "2.0", pipeline: "P3", aspect: "16:9" },
  totals: {
    beats: N, contentSeconds: r1(pre[N]),
    segments: segs.length, billedSeconds: r1(segs.reduce((s, x) => s + x.estimatedSeconds, 0))
  },
  segments: segs
};
writeFileSync(out, JSON.stringify(result, null, 2), "utf8");

console.log(`written: ${out}`);
console.log(`=== ${segs.length} 段 / ${result.totals.billedSeconds}s ===`);
let allOk = true;
for (const s of segs) {
  const bad = s.estimatedSeconds < LO - 1e-9 || s.estimatedSeconds > HI + 1e-9;
  if (bad) allOk = false;
  console.log(` ${s.segId}  ${String(s.estimatedSeconds).padStart(5)}s [${s.scene}] 台词${s.dialogueCount} 面板${s.panelCount}  ${s.beatIds[0]}~${s.beatIds[s.beatIds.length - 1]}${bad ? "  ← 越界!" : ""}`);
}
console.log(allOk ? "\n✅ 全部段落落在 [12,15] 秒内" : "\n⚠️ 仍有段落越界");
process.exit(allOk ? 0 : 3);
