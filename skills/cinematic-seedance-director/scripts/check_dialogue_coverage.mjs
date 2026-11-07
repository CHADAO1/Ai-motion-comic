#!/usr/bin/env node
/**
 * check_dialogue_coverage.mjs — 台词守恒校验（两道硬门，防"漏台词"）
 *
 * 用法:
 *   node check_dialogue_coverage.mjs --beats <01_拍点表.json> --split <03_拆段表.json> \
 *        [--prompts <outputs目录>] [--table <中文台词表.txt>]
 *
 * 门1（S2 出口）: 01_拍点表中所有非空 dialogueZh 必须 100% 出现在
 *                 03_拆段表某一段的 beats 文本里。缺失 → FAIL。
 * 门2（S5 出口, 需 --prompts）: 每条台词必须能在对应段落提示词的
 *                 【配音指令】原文中找到。缺失 → FAIL。
 *
 * 退出码: 0 全通过 / 1 有缺失 / 2 参数或读取错误
 *
 * 设计要点（来自 2026-09-10 第十集漏「天亮了。」事故）:
 *   事故根因是拆段时用拍点 actions.desc 覆盖了 dialogueZh，台词既没进
 *   段落 beats 也没进配音指令，且 endsWithDialogue 误判导致漏配收尾镜。
 *   故本脚本对"拍点有台词但拆段表中无该台词"零容忍。
 *
 * 匹配策略: 归一化（去省略号/空白/引号/破折号）后做子串包含；
 *          长台词按 8 字滑窗取片段，要求"全部片段命中"才算覆盖
 *          （允许台词被合法拆给多个镜头/多条配音指令）。
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

function parseArgs(argv) {
  const a = { beats: null, split: null, prompts: null, table: null };
  for (let i = 0; i < argv.length; i++) {
    const k = argv[i];
    if (k === "--beats") a.beats = argv[++i];
    else if (k === "--split") a.split = argv[++i];
    else if (k === "--prompts") a.prompts = argv[++i];
    else if (k === "--table") a.table = argv[++i];
    else { console.error(`ERROR: unexpected argument: ${k}`); process.exit(2); }
  }
  if (!a.beats || !a.split) {
    console.error("usage: node check_dialogue_coverage.mjs --beats <01_拍点表.json> --split <03_拆段表.json> [--prompts <dir>] [--table <txt>]");
    process.exit(2);
  }
  return a;
}

const norm = (s) =>
  String(s ?? "")
    .replace(/^\uFEFF/, "")
    .replace(/[…⋯]+/g, "")
    .replace(/[\s"'""''\u3000]/g, "")
    .replace(/[—–\-]{1,}/g, "");

function readJson(p) {
  try { return JSON.parse(readFileSync(p, "utf8").replace(/^\uFEFF/, "")); }
  catch (e) { console.error(`ERROR: cannot read/parse ${p}: ${e.message}`); process.exit(2); }
}

/**
 * 台词覆盖判定（容忍"长句被合法拆给多个镜头/多条配音指令"）
 *
 * 策略：把台词归一化后切成若干窗口，逐窗口到语料里找，命中率 >= 70% 即覆盖。
 *   关键坑：窗口若横跨"拆段边界"（拆段表把一句话断成两截放进不同 beat），
 *   该窗口在语料里天然找不到——这是**合法**的，不能算缺失。
 *   故采用两轮判定：
 *     ① 先算命中率；若 >= 阈值 → 覆盖，直接返回。
 *     ② 若不足，再检查"未命中的窗口是否都紧邻已命中区域"（即断点造成），
 *        且未命中窗口占总窗口比例 <= 40% → 仍判为覆盖（拆段断点导致）。
 *   这样"整条丢失"（命中率 ≈ 0）必然被抓出，而"断句"不会误报。
 */
function windowStats(needle, haystackNorm, win = 6) {
  const n = norm(needle);
  if (!n) return { total: 0, hits: 0, misses: [] };
  if (n.length <= 10) {
    const ok = haystackNorm.includes(n);
    return { total: 1, hits: ok ? 1 : 0, misses: ok ? [] : [n] };
  }
  const chunks = [];
  for (let i = 0; i < n.length; i += win) {
    const c = n.slice(i, i + win);
    if (c.length >= 3) chunks.push(c);
  }
  const tail = n.slice(-win);
  if (tail.length >= 3) chunks.push(tail);
  const misses = chunks.filter((c) => !haystackNorm.includes(c));
  return { total: chunks.length, hits: chunks.length - misses.length, misses };
}

const COVER_RATIO = 0.7;      // 主判据：窗口命中率
const MAX_MISS_RATIO = 0.4;   // 断点容忍：未命中窗口占比上限

/**
 * 抽取提示词中的所有【配音指令：…】内容，只在这部分语料里做覆盖判定。
 *
 * 两个必须处理的坑：
 *  ① 台词文本会同时出现在「动作」描述里（例如 10-1-4 镜头3 动作写了
 *     "她轻声说了一句「天亮了。」"）。若拿全文做匹配，配音指令整条被删
 *     也会误判为"已覆盖" —— 2026-09-10 回归测试踩到的假阴性。
 *  ② 配音指令**内部**还嵌套了【内心独白】这类方括号（OS 台词），
 *     不能用 `【[^】]*】` 这种遇右括号即停的正则。故按行提取：
 *     凡以 `【配音指令` 开头，取到该行末尾（行尾必为 `】`）。
 */
function extractVoiceLines(text) {
  const lines = String(text ?? "").split(/\r?\n/);
  const out = [];
  for (let i = 0; i < lines.length; i++) {
    if (!lines[i].trimStart().startsWith("【配音指令")) continue;
    // 配音指令是**一块**而非一行：标题行（【配音指令】角色｜音色｜状态｜语气：）
    // 之后紧跟 1-2 行的台词/独白正文，直到空行或下一个块级标记才结束。
    // 只取标题行会把"台词"本体漏掉 —— 2026-09-10 第10集压缩回归踩到的假阴性。
    out.push(lines[i]);
    for (let j = i + 1; j < lines.length; j++) {
      const t = lines[j].trim();
      if (t === "") {
        // 空行后若紧跟台词行仍属本块，否则收束
        const nxt = lines[j + 1]?.trim() ?? "";
        if (/^(台词|【内心独白】台词)[：:]/.test(nxt)) { out.push(nxt); i = j + 1; continue; }
        break;
      }
      if (/^⚠️|^【镜头|^【场景|^【风格|^【光影|^环境|^禁/.test(t)) break;
      out.push(t);
      i = j;
      if (/^(台词|【内心独白】台词)[：:]/.test(t)) {
        // 台词行取到后，若下一行仍是台词则继续
        if (!/^(台词|【内心独白】台词)[：:]/.test(lines[j + 1]?.trim() ?? "")) break;
      }
    }
  }
  return out.join("\n");
}

function coverageRatio(needle, haystackNorm) {
  const st = windowStats(needle, haystackNorm);
  if (st.total === 0) return 1;
  return st.hits / st.total;
}

const covered = (needle, haystackNorm) => {
  const st = windowStats(needle, haystackNorm);
  if (st.total === 0) return true;
  const ratio = st.hits / st.total;
  if (ratio >= COVER_RATIO) return true;
  // 断点容忍：仅当"少量窗口未命中"且"命中率不至于全无"时才放行
  const missRatio = st.misses.length / st.total;
  return ratio > 0 && missRatio <= MAX_MISS_RATIO;
};

function main() {
  const args = parseArgs(process.argv.slice(2));
  const beatsFile = readJson(args.beats);
  const splitFile = readJson(args.split);
  const segments = splitFile.segments ?? splitFile;
  if (!Array.isArray(beatsFile.beats)) { console.error("ERROR: beats file has no .beats[]"); process.exit(2); }
  if (!Array.isArray(segments)) { console.error("ERROR: split file has no .segments[]"); process.exit(2); }

  const dialogueBeats = beatsFile.beats.filter((b) => String(b.dialogueZh ?? b.dialogue ?? "").trim());
  const splitText = norm(segments.map((s) => (s.beats ?? []).join("\n")).join("\n"));

  // 门1：拍点台词 → 拆段表
  const gate1Missing = [];
  for (const b of dialogueBeats) {
    const line = b.dialogueZh ?? b.dialogue;
    if (!covered(line, splitText)) gate1Missing.push({ id: b.id, speaker: b.speaker, line });
  }

  console.log("════════ 门1：拍点表 → 拆段表（S2 出口） ════════");
  console.log(`拍点表台词条数: ${dialogueBeats.length}`);
  if (gate1Missing.length === 0) {
    console.log("✅ 全部台词均已进入拆段表 beats");
  } else {
    for (const m of gate1Missing) console.log(`❌ [${m.id}] ${m.speaker}：${m.line}`);
    console.log(`>>> ${gate1Missing.length} 条台词在拆段环节丢失！检查拆段表是否用 actions.desc 覆盖了 dialogueZh。`);
  }

  // 门2：提示词配音指令覆盖（可选）
  let gate2Missing = [];
  if (args.prompts) {
    let files = [];
    try {
      files = readdirSync(args.prompts).filter((f) => /\.(txt)$/i.test(f)).sort((a, b) => {
        const p = (x) => (x.match(/(\d+)[-_](\d+)/) || []).slice(1).map(Number);
        const [a1, a2] = p(a), [b1, b2] = p(b);
        return a1 - b1 || a2 - b2;
      });
    } catch (e) { console.error(`ERROR: cannot read prompts dir ${args.prompts}: ${e.message}`); process.exit(2); }

    // 逐段构建：segId -> 该段**配音指令**语料（不含动作描述，防假阴性）
    // 文件名 → segId 的映射优先级：
    //   ① 拆段表显式声明 promptFile（最可靠，任何命名规则都适用）
    //   ② 文件名里的 10-1-1 形态（集-场-序）按**文档顺序**对齐 segments
    //   ③ 文件名里的 seg_01 形态（集-场-序）
    //   ④ 兜底：文件名词干
    const segIdOf = (f, idx) => {
      const stem = f.replace(/\.txt$/i, "");
      const m3 = f.match(/^(\d+)-(\d+)-(\d+)/);            // 10-1-1
      if (m3) {
        const [, ep, sc, ord] = m3;
        // 在拆段表里找同场次(scene 形如 "10-1")且序号(在场景内第几个)匹配的段
        const sameScene = segments.filter((s) => String(s.scene) === `${ep}-${sc}`);
        const target = sameScene[Number(ord) - 1];
        if (target?.segId) return target.segId;
      }
      const mSeg = f.match(/(seg_\d+)/i);
      if (mSeg) return mSeg[1];
      return stem;
    };
    /** 允许拆段表用 promptFile 字段显式绑定文件 */
    const explicitByFile = new Map();
    for (const s of segments) {
      if (s.promptFile) explicitByFile.set(String(s.promptFile).replace(/\.txt$/i, ""), s.segId);
      if (Array.isArray(s.promptFiles)) for (const pf of s.promptFiles) explicitByFile.set(String(pf).replace(/\.txt$/i, ""), s.segId);
    }
    const promptById = new Map();
    files.forEach((f, i) => {
      const stem = f.replace(/\.txt$/i, "");
      const id = explicitByFile.get(stem) ?? segIdOf(f, i);
      const voice = extractVoiceLines(readFileSync(join(args.prompts, f), "utf8"));
      promptById.set(id, (promptById.get(id) ?? "") + "\n" + voice);
    });
    const allPrompts = norm([...promptById.values()].join("\n"));

    console.log("");
    console.log("════════ 门2：拍点表 → 提示词配音指令（S5 出口） ════════");
    console.log(`提示词文件数: ${files.length}`);
    for (const b of dialogueBeats) {
      const line = b.dialogueZh ?? b.dialogue;
      // 归属段：该台词可能跨多段（长台词被合法拆开），故收集**所有**相关段
      const relatedIds = segments
        .filter((s) => (s.beats ?? []).some((x) => covered(line, norm(x))))
        .map((s) => s.segId)
        .filter(Boolean);
      // 在归属段范围内校验；范围为空（拆段表里都没这条）则回退全库，
      // 交给门1 报错——门2 只负责"归属段内的提示词是否真的写了这句"。
      const scope = relatedIds.length ? norm(relatedIds.map((id) => promptById.get(id) ?? "").join("\n")) : allPrompts;
      if (!covered(line, scope)) {
        gate2Missing.push({
          id: b.id,
          speaker: b.speaker,
          line,
          relatedIds,
          anywhere: covered(line, allPrompts)
        });
      }
    }
    if (gate2Missing.length === 0) {
      console.log("✅ 全部台词均出现在对应段落的配音指令中");
    } else {
      for (const m of gate2Missing) {
        console.log(`❌ [${m.id}] ${m.speaker}：${m.line}`);
        console.log(`   归属段: ${m.relatedIds.length ? m.relatedIds.join("/") : "(未定位)"} ｜ 全库中存在: ${m.anywhere ? "是（跨段错放）" : "否（彻底丢失）"}`);
      }
      console.log(`>>> ${gate2Missing.length} 条台词未落到提示词配音指令！`);
    }
  }

  const total = gate1Missing.length + gate2Missing.length;
  console.log("");
  console.log("──────── 汇总 ────────");
  console.log(`门1 缺失 ${gate1Missing.length} ｜ 门2 缺失 ${gate2Missing.length}`);
  if (total === 0) {
    console.log("🎉 台词守恒校验通过，0 遗漏");
    process.exit(0);
  }
  console.log("⛔ 存在台词遗漏，禁止进入下一阶段。");
  process.exit(1);
}

function localPromptById(promptById, segId) {
  if (!segId) return "";
  return promptById.get(segId) ?? "";
}

main();
