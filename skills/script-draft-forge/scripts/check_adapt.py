# -*- coding: utf-8 -*-
"""一键验收入口：机械项 + 语义门禁 G1–G9 合并成一份结论。

用法：
  python scripts/check_adapt.py --files outputs/ep001_A_v1_dlg.md outputs/ep001_B_v1_dlg.md \
      --source pipeline/source/ep001.txt --config pipeline/adapt_gate_config.json \
      --out outputs/01_验收.json

与 `check_gate_a.py` 的关系：两边都跑，结论才成立。
  - check_gate_a.py：轮次/字数/人名/术语/系统条款/单句 8-15 字占比（GA-01~12）
  - check_adapt.py：语义形态 G1~G9（含叙述腔直搬、A/B 同旁白）
本入口的机械项**只报数不作硬判杀**，避免与闸门A 的判据重复且口径打架。

例外是**稿件形态门（GA-12）**：2026-11-06 第10-12集回归实测 12 份 DRY 占位稿
（0 场、0 句对白）被两个入口全判「验收通过」。形态门只查「有没有戏」——
演练占位标记／人物对白句为 0／场次标记为 0 任一命中即「不予验收」，
不设字数下限、不判语义、不判质量，与内容违规分开陈述。口径共用
`_text_util.draft_shape()`；`--skip-shape` 只关判杀、不关报数。

退出码：0=全部验收通过；1=存在「未通过」或「不予验收」（含 GA-12 形态不达标），
与 `check_gate_a.py` 一致，供命令链/CI 判读，避免结论文案改了但退出码仍给假绿。

纯标准库，无第三方依赖。
"""
import argparse
import io
import json
import os
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import adapt_gate as AG
from _text_util import (body_lines, cjk_only, cross_file_narration,
                        dialogue_sentences, draft_shape, is_draft_candidate,
                        scene_count, sentence_len)

SPEAKER = re.compile(r"^\s*[^：:「」\"'（）]{1,16}：")
HOOK = re.compile(r"^【卡点】", re.M)


def one(path, cfg, src_text, cross, dmin, dmax, dratio, skip_shape=False):
    raw = io.open(path, encoding="utf-8").read()
    lines = body_lines(raw)
    body = "\n".join(lines)
    turns = [l.strip() for l in lines if SPEAKER.match(l)]
    sents = dialogue_sentences(lines)
    lens = [sentence_len(s) for _, _, s in sents]
    n_short = sum(1 for n in lens if n < dmin)
    n_long = sum(1 for n in lens if n > dmax)
    # 与 GA-09 同口径：短节奏句登记例外，只有超长句占比进门
    long_ratio = n_long / len(lens) if lens else 0.0
    mech = {
        "正文汉字数": len(cjk_only(body)),
        "台词轮次": len(turns),
        "场数": scene_count(lines),
        "旁白轮次": sum(1 for l in lines if l.strip().startswith("旁白：")),
        "完全重复台词行": len(turns) - len(set(turns)),
        "对白句数": len(lens),
        "短节奏句（登记例外）": n_short,
        "超长句数": n_long,
        "超长句占比": round(long_ratio, 3),
        "区间外合计": n_short + n_long,
        "最长单句汉字数": max(lens) if lens else 0,
        "卡点存在": bool(HOOK.search(raw)),
    }
    gate = AG.check(path, cfg, src_text, cross)
    ratio_fail = long_ratio > dratio
    # GA-12：形态门与内容违规分开陈述，不混写成「判杀」
    shape = draft_shape(raw)
    shape_fail = (not skip_shape) and (not shape["ok"])
    shape_gate = {
        "判定": "达标" if shape["ok"] else "不达标（不予验收）",
        "判杀": shape_fail,
        "原因": shape["issues"],
        "场次标记数（宽松识别）": shape["scenes"],
        "人物对白句": shape["dialogue_sentences"],
        "演练占位标记": shape["dry_mark"],
        "口径": "只量形态：不设字数下限、不判语义、不判质量；--skip-shape 只关判杀不关报数",
    }
    ok = not (gate["hard_fail"] or gate["fail_gates"] or ratio_fail or shape_fail)
    if shape_fail:
        verdict = "不予验收：稿件形态不达标（%s）；不是内容违规，补正文后复跑" % \
                  "；".join(shape["issues"])
    elif not ok:
        verdict = "未通过，见命中门与占比门"
    else:
        verdict = "验收通过（G8 逐句溯源 / DP-04 朗读仍需人工）"
    return {
        "file": os.path.basename(path),
        "机械项（只报数，不判杀）": mech,
        "稿件形态门（GA-12）": shape_gate,
        "语义门禁": {"命中门": gate["fail_gates"], "硬伤": gate["hard_fail"],
                     "判定": gate["verdict"], "提示": gate["notes"]},
        "单句占比门": {"口径": ">15 字超长句占比（短句登记例外）",
                     "阈值": dratio, "实测": round(long_ratio, 3),
                     "判定": "超阈值" if ratio_fail else "通过"},
        "结论": verdict,
    }


def exit_code(rows):
    """0=全部验收通过；1=存在未通过／不予验收（与闸门A 退出码口径一致）。"""
    return 0 if all(r["结论"].startswith("验收通过") for r in rows) else 1


def selftest():
    import tempfile
    d = Path(tempfile.mkdtemp(prefix="check_adapt_st_"))
    try:
        dry = d / "ep010_A_v1.md"
        dry.write_text("> ⚠ DRY-RUN 占位，非真实初稿；删除本行前禁止进入闸门A。\n"
                       "> 版本：ep010_A_v1 · 引擎：glm-5.3-flash（批量档）\n\n"
                       "（演练未调用 API，本文件无正文，不得进入闸门A。）\n", encoding="utf-8")
        real = d / "ep010_B_v1.md"
        real.write_text("【场1｜府衙大堂】\n李承泽：你在教我做事？\n"
                        "（他把工牌往桌上一拍。）\n", encoding="utf-8")
        cfg = AG.GateConfig()
        rd = one(str(dry), cfg, "", {}, 8, 15, 0.20)
        assert rd["稿件形态门（GA-12）"]["判定"].startswith("不达标"), rd
        assert "不予验收" in rd["结论"] and "不是内容违规" in rd["结论"], rd["结论"]
        rr = one(str(real), cfg, "", {}, 8, 15, 0.20)
        assert rr["稿件形态门（GA-12）"]["判定"] == "达标", rr
        assert rr["结论"].startswith("验收通过"), rr["结论"]
        # 异格式场次（六档位真稿）不得误杀
        alt = d / "ep010_C_v1.md"
        alt.write_text("1-1　日　外　国营饭店门口\n青年甲：瞧见没？\n", encoding="utf-8")
        assert one(str(alt), cfg, "", {}, 8, 15, 0.20)["稿件形态门（GA-12）"]["判定"] == "达标"
        # 真稿埋语义违规 → 走「未通过」，形态门不掩盖内容判定
        bad = d / "ep010_D_v1.md"
        bad.write_text("【场1｜府衙大堂】\n旁白：他心里清楚，这下成了死局。\n"
                       "李承泽：滚。\n", encoding="utf-8")
        rb = one(str(bad), cfg, "", {}, 8, 15, 0.20)
        assert rb["结论"] == "未通过，见命中门与占比门", rb["结论"]
        assert rb["稿件形态门（GA-12）"]["判定"] == "达标", rb
        # --skip-shape 只关判杀，数值仍留痕
        rs = one(str(dry), cfg, "", {}, 8, 15, 0.20, skip_shape=True)
        assert rs["稿件形态门（GA-12）"]["判定"].startswith("不达标"), rs
        assert rs["稿件形态门（GA-12）"]["判杀"] is False, rs
        # 退出码不得给假绿：有不予验收/未通过 → 1，全通过 → 0
        assert exit_code([rd, rr]) == 1 and exit_code([rb, rr]) == 1
        assert exit_code([rr]) == 0
        print("[PASS] check_adapt selftest：DRY 占位不予验收 / 真稿与异格式不误杀 / "
              "内容违规不被掩盖 / --skip-shape 只关判杀不关报数 / 退出码不假绿")
        return 0
    finally:
        for f in d.iterdir():
            f.unlink()
        d.rmdir()


def main():
    ap = argparse.ArgumentParser(description="机械项 + 稿件形态门 + 语义门禁 一键验收")
    ap.add_argument("--files", nargs="+")
    ap.add_argument("--source", help="本集原文切片")
    ap.add_argument("--source-dir", help="按 epNNN 命名的原文切片目录")
    ap.add_argument("--config", help="项目判据 JSON")
    ap.add_argument("--dialogue-min", type=int, default=8)
    ap.add_argument("--dialogue-max", type=int, default=15)
    ap.add_argument("--dialogue-max-ratio", type=float, default=0.20)
    ap.add_argument("--skip-shape", action="store_true",
                    help="兼容存量异格式稿：GA-12 只报数不判杀（数值仍留痕）")
    ap.add_argument("--no-filter", action="store_true",
                    help="不排除报告/索引类文件（默认排除，防 --files glob 把报告当稿件）")
    ap.add_argument("--out", help="JSON 报告输出路径")
    ap.add_argument("--selftest", action="store_true", help="内置自检")
    a = ap.parse_args()

    if a.selftest:
        return selftest()
    if not a.files:
        print("[ERROR] 需 --files（或 --selftest）", file=sys.stderr)
        return 2
    files = list(a.files) if a.no_filter else [f for f in a.files
                                               if is_draft_candidate(f)]
    skipped = [f for f in a.files if f not in files]
    if skipped:
        print("[SKIP] 非稿件文件 %d 个，不进入验收：%s" %
              (len(skipped), "、".join(Path(f).name for f in skipped[:8])))
    if not files:
        print("[ERROR] 过滤后没有可验稿件（如需强制验收报告类文件，用 --no-filter）",
              file=sys.stderr)
        return 2
    cfg = AG.GateConfig.load(a.config)
    sources = AG.load_sources(a.source, a.source_dir)
    cross = cross_file_narration(files)
    rows = [one(f, cfg, AG.source_for(f, sources), cross,
                a.dialogue_min, a.dialogue_max, a.dialogue_max_ratio,
                a.skip_shape) for f in files]
    if a.out:
        Path(a.out).write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        print("[OK] 报告：%s" % a.out)
    for r in rows:
        m = r["机械项（只报数，不判杀）"]
        print("%-26s %s｜形态 %s" %
              (r["file"], r["结论"], r["稿件形态门（GA-12）"]["判定"]))
        print("   汉字 %d｜轮次 %d｜场 %d｜旁白 %d｜对白句 %d｜"
              "短句 %d｜超长 %d (%.0f%%)｜最长 %d 字｜语义门 %s" %
              (m["正文汉字数"], m["台词轮次"], m["场数"], m["旁白轮次"],
               m["对白句数"], m["短节奏句（登记例外）"], m["超长句数"],
               m["超长句占比"] * 100, m["最长单句汉字数"],
               r["语义门禁"]["命中门"] or "零命中"))
    return exit_code(rows)


if __name__ == "__main__":
    sys.exit(main())
