#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
analyze_script.py — 短剧剧本结构量化体检（映射规则 SC-*，见 rules/structure.md）

为什么要有脚本：竞争力诊断里有一半结论是**可数的事实**——多少集、
哪几集同一场景连拍、字数集中在哪几集、最强爆点埋在第几集、两个版本
差在哪几集。这些让 AI 口头估，必然出错且不可复核。本脚本出数，AI 只
负责解释这些数意味着什么。

用法：
    python analyze_script.py <剧本.txt> [-o 输出目录]
    python analyze_script.py 新版.txt --vs 旧版.txt        # 增量灌水鉴定

产出（写入输出目录）：
    01_结构体检.json     全部指标（机器读）
    01_结构体检.md       可读体检表（直接贴进报告）
    02_版本差异.md       仅 --vs 模式：逐集同一性矩阵

依赖：仅标准库。
"""

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict

CN_NUM = {
    "零": 0, "〇": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6,
    "七": 7, "八": 8, "九": 9, "十": 10, "百": 100,
}


def cn2int(s):
    """中文数字转 int。够用于集号（0–999）。

    不走通用大数算法——集号场景简单，但真实投稿稿里会出现错字（如
    '第五十六四集'），所以额外做两件事：① 逐字容错，非数字字符跳过；
    ② 支持 '五十六' / '一百零八' / '23' / '１０'（全角）。
    """
    s = s.strip().translate(str.maketrans("０１２３４５６７８９", "0123456789"))
    if s.isdigit():
        return int(s)
    total, cur = 0, 0
    for ch in s:
        if ch not in CN_NUM:
            continue  # 容错：跳过 '第'、空白、错字
        v = CN_NUM[ch]
        if v == 10:
            cur = (cur if cur else 1) * 10
        elif v == 100:
            cur = (cur if cur else 1) * 100
        else:
            if cur >= 10 and cur % 10 == 0:
                cur += v           # '二十三'：20 已成立 → +3
            else:
                cur = v            # '二十' 之后的单位或个位
    total += cur
    return total or None


EP_RE = re.compile(r"^第\s*([一二三四五六七八九十百零〇\d]{1,6}?)\s*集")
# 场景头：'1-1夜 内 宋知节家' / '1-1 内 客厅' / '12-3 日外 医院走廊'
SCENE_RE = re.compile(r"^(\d{1,3})\s*[-–—]\s*(\d{1,3})\s*(.*)$")
SCENE_KW_RE = re.compile(r"[日天晚夜晨昏]\s*(内|外|内景|外景)")

# 钩子候选来源：VO / 音画同步 / 旁白（SC-04）。真实剧本的开场钩子几乎总在
# 第一集的 VO 或【音画同步】行里，纯按句号切正文会切到人物小传上。
VO_RE = re.compile(r"(VO|OS|画外音|旁白|音画同步)")

# 套路/降智信号词——命中不等于有问题，但必须在报告里点名讨论（SC-05）
CLICHE_KW = [
    "分家", "各过各的", "净身出户", "后悔", "全家后悔", "她却疯了", "当场",
    "打脸", "啪啪", "下跪", "破防", "崩溃", "反转", "打脸现场", "hidden",
    "装穷", "白月光", "绿茶", "舔狗", "战神", "首富", "隐藏身份", "战神归来",
    "离婚", "净身", "悔婚", "抢孩子", "保姆", "保姆工资", "工资卡", "记账",
    "账本", "朋友圈", "直播", "热搜", "律师函", "起诉", "报警", "监控",
    "嫁给", "我未婚夫", "八年", "三年", "资助", "认亲", "抱错", "错换",
]

# 降智冲突信号：成年人做出无常识决策（SC-06）
DEROUND_KW = ["发电机", "分期付款给", "月收入", "月薪", "班上", "补习班", "乐高", "报名费"]

# 付费卡点/集数声明（SC-07）
PAYWALL_KW = ["免费", "付费", "第11集", "第10集", "解锁", "广告", "卡点", "充值"]


def read_text(p):
    for enc in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return open(p, encoding=enc).read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    return open(p, encoding="utf-8", errors="ignore").read()


def parse_episodes(text):
    """切分为 [{no, head, start, lines}]，start 为在原文中的行号。

    **单调性校正（真实投稿稿必需）**：编剧手打稿会出现错字集号，如
    '第五十六四集'。逐字容错会把 '五十六四' 算成 4，污染后续全部编号。
    判定口径：真实剧本集号严格递增，因此当解析值 ≤ 上一集号时，改为
    在该串上取「能解析出 > 上一集号 的最长前缀」，仍失败则跳过该行。
    """
    lines = text.split("\n")
    eps = []
    prev_no = 0
    for i, l in enumerate(lines):
        m = EP_RE.match(l.strip())
        if not m:
            continue
        raw = m.group(1)
        no = cn2int(raw)
        if no is None or no <= prev_no:
            fixed = None
            for cut in range(len(raw) - 1, 0, -1):
                cand = cn2int(raw[:cut])
                if cand is not None and cand > prev_no:
                    fixed = cand
                    break
            no = fixed
        if no is None:
            continue
        eps.append({"no": no, "head": l.strip(), "start": i, "lines": []})
        prev_no = no
    for idx, e in enumerate(eps):
        end = eps[idx + 1]["start"] if idx + 1 < len(eps) else len(lines)
        e["lines"] = lines[e["start"]:end]
        e["body"] = "\n".join(e["lines"])
        e["chars"] = len(re.sub(r"\s", "", e["body"]))
    return eps


def scene_spots(body):
    """返回本集所有场景头的地点名列表，如 ['宋知节家', '民政局门口']。

    关键：**不能**用 '集-场' 编号做同一场景判定——每集的场景编号都从
    1-1 重新起算，编号相同但地点不同。必须取编号后面的地点名。
    """
    spots = []
    for l in body.split("\n"):
        s = l.strip()
        if not s or len(s) > 40:
            continue
        m = SCENE_RE.match(s)
        if m:
            tail = m.group(3)
            tail = SCENE_KW_RE.sub("", tail)
            tail = re.sub(r"[\s，,。.、·\-—:：]", "", tail)
            if tail:
                spots.append(tail)
                continue
        if SCENE_KW_RE.search(s) and len(s) <= 30:
            t = SCENE_KW_RE.sub("", s)
            t = re.sub(r"[\s，,。.、·\-—:：]", "", t)
            if t and not re.match(r"^人物", t):
                spots.append(t)
    return spots


def scene_label(body):
    sp = scene_spots(body)
    return sp[0] if sp else ""


def longest_same_scene_run(eps):
    """SC-03：找出连续多集锁在同一场景的最长串——'一场戏拖 N 集'的硬证据。

    判定口径：相邻两集的**首个场景地点名相同**，即视为同场景连拍。
    跨集场景名写法差异（'宋知节家' vs '宋家客厅'）由 AI 在报告里补充
    人工合并，脚本只负责给出可复核的原始串。
    """
    best, cur = [], []
    for e in eps:
        sp = scene_spots(e["body"])
        k = sp[0] if sp else None
        if k and cur and cur[-1]["key"] == k:
            cur.append({"no": e["no"], "key": k, "label": k})
        else:
            if len(cur) > len(best):
                best = cur
            cur = [{"no": e["no"], "key": k, "label": k}] if k else []
    if len(cur) > len(best):
        best = cur
    return best


def gini(xs):
    """基尼系数——衡量字数是否集中在少数集（灌水的量化信号）。"""
    xs = sorted(xs)
    n = len(xs)
    if n == 0 or sum(xs) == 0:
        return 0.0
    cum, s = 0, 0
    for i, x in enumerate(xs, 1):
        cum += i * x
        s += x
    return round((2 * cum) / (n * s) - (n + 1) / n, 4)


def top_share(eps, k):
    """前 k 集占全剧字数比例——'铺垫占多少'的直接答案。"""
    total = sum(e["chars"] for e in eps) or 1
    return round(sum(e["chars"] for e in eps[:k]) * 100.0 / total, 1)


def hook_sentences(text, n=3):
    """SC-04：抓开篇钩子句。

    三级降级（真实投稿稿三种写法都见过）：
      ① 第一集内 VO/音画同步/旁白 行里的【画面N】内容 —— 命中率最高
      ② 第一集正文前若干句按句末标点切
      ③ 全文前若干句（最后兜底）
    绝不从人物小传/剧名/简介里切——那些不是钩子。

    ⚠️ 实测踩过的坑：切句前必须剔除 ① 集号行（「第1集」）② 出场人物行
    ③ 场景头行，否则「第一集」会被当成钩子句，还会被数字锚点规则误判为
    「含数字」。这类稿（农村写实向）常常完全没有 VO 行，只能走 ② 号降级。
    """
    eps = parse_episodes(text)
    first = eps[0]["body"] if eps else text[:4000]

    vo = []
    for l in first.split("\n"):
        s = l.strip()
        if VO_RE.search(s):
            # '【画面一】xxx【画面二】yyy' → 拆成独立画面句
            for seg in re.split(r"【画面[^】]*】", s):
                seg = seg.strip()
                # 只剥掉行首的「角色名VO：」这类说话人标签。
                # 注意 [^…] 类贪婪匹配会吃掉正文汉字，必须锚定到冒号。
                seg = re.sub(r"^[^：:\n]{0,12}?(?:VO|OS|v\.o\.)[：:]\s*", "", seg, flags=re.I)
                seg = re.sub(r"^\s*(?:VO|OS)\s*[：:]\s*", "", seg, flags=re.I)
                seg = re.sub(r"【[^】]*】|\[[^\]]*\]", "", seg).strip()
                if len(seg) >= 4 and re.search(r"[一-鿿]", seg):
                    vo.append(seg)
    if vo:
        return vo[:n + 2], "VO/音画同步"

    # 降级 ②：剥掉非叙事行后按句末标点切。△ 是分镜动作标记，属画面描述，
    # 保留内容但去掉符号（它是可拍的画面，不是废话）。
    noise = re.compile(r"^(第\s*[零一二三四五六七八九十百\d]+\s*集|出场人物|人物|"
                       r"[画面重点]*[日夜晨昏][内外景]?|\d+-\d+|△\s*$|【?字幕)")
    cleaned = []
    for l in first.split("\n"):
        s = l.strip()
        if not s or noise.match(s):
            continue
        s = re.sub(r"^[△▲▽]\s*", "", s)
        cleaned.append(s)
    parts = [p.strip() for p in re.split(r"[。！？!?]+", chr(10).join(cleaned)) if p.strip()]
    parts = [p for p in parts if len(re.findall(r"[一-鿿]", p)) >= 4]
    if parts:
        return parts[:n], "第一集正文（无 VO）"

    parts = [p.strip() for p in re.split(r"[。！？!?\n]+", text) if p.strip()]
    return parts[:n], "全文开头（未定位到正文，请人工核对）"


def hook_audit(sents):
    """对开头三句做可判定的结构打标（SC-04）。"""
    audit = {"has_number": False, "numbers": [], "has_damage": False,
             "has_counter": False, "has_preview_only": False, "visualizable": 0}
    dmg = ["她却", "却穿", "抢走", "背叛", "抛弃", "羞辱", "跪", "骂", "打", "抢",
           "换了", "当众", "婚礼", "医院", "中毒", "离婚", "疯了", "扒", "扇",
           "踹", "掀", "悔婚", "和别人", "逼我", "气急", "撕"]
    ctr = ["我笑", "递给", "甩", "反手", "当场", "让他", "转身", "掏出", "打开",
           "报警", "起诉", "律师", "证据", "录像", "账单", "反问", "我说",
           "我掏", "我把", "递上", "冷笑", "打断", "拒绝", "撕"]
    prev = ["他说", "她说", "他们说", "预告", "日后", "没想到", "后来才",
            "我要让", "发誓", "决心", "从今以后", "势必要", "绝不让"]
    for s in sents:
        for n in re.findall(r"\d+", s):
            audit["numbers"].append(n)
        if re.search(r"[一二三四五六七八九十百千万两]+(?=[年月日集人岁块元万次])", s):
            audit["has_number"] = True
        if any(k in s for k in dmg):
            audit["has_damage"] = True
        if any(k in s for k in ctr):
            audit["has_counter"] = True
        if any(k in s for k in prev) and not any(k in s for k in ctr):
            audit["has_preview_only"] = True
        # 可视化：含具体手部/身体动作 → 能拍成画面（SC-04 可视化判据）
        if re.search(r"(递|甩|掏|摔|撕|拽|抓|举|拍|拉|推|端|掀|扇|踹|捧)", s):
            audit["visualizable"] += 1
    if audit["numbers"]:
        audit["has_number"] = True
    return audit


def find_buried_peak(eps, kw=None):
    """SC-08：找出「最强爆点词」首次出现的集号——判断王牌是否被埋在后面。"""
    kw = kw or ["疯了", "当场", "打脸", "反转", "撕", "跪", "真相", "原来"]
    res = []
    for k in kw:
        hit = None
        for e in eps:
            if k in e["body"]:
                hit = e["no"]
                break
        if hit:
            res.append({"kw": k, "ep": hit})
    res.sort(key=lambda x: -x["ep"])
    return res


def compare_versions(new_eps, old_eps):
    """SC-09：逐集文本同一性 → 证明「新版 = 旧版 + N 集灌水」。"""
    import difflib
    old_by_no = {e["no"]: e["body"] for e in old_eps}
    rows = []
    for e in new_eps:
        ob = old_by_no.get(e["no"])
        if ob is None:
            rows.append((e["no"], "新增", 0.0))
            continue
        r = difflib.SequenceMatcher(None, re.sub(r"\s", "", e["body"]),
                                    re.sub(r"\s", "", ob)).ratio()
        rows.append((e["no"], "同一" if r > 0.97 else ("小改" if r > 0.8 else "重写"), round(r, 3)))
    old_nos = set(old_by_no) - {e["no"] for e in new_eps}
    return rows, sorted(old_nos)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("--vs", default=None, help="对比版本（用于鉴定增量灌水）")
    ap.add_argument("-o", "--outdir", default=None)
    a = ap.parse_args()

    if not os.path.isfile(a.script):
        print("[FAIL] 文件不存在: %s" % a.script)
        return 1
    outdir = a.outdir or os.path.dirname(os.path.abspath(a.script)) or "."
    os.makedirs(outdir, exist_ok=True)

    text = read_text(a.script)
    eps = parse_episodes(text)
    if not eps:
        print("[FAIL] 未识别到任何「第N集」标记，确认文件是剧本正文")
        return 1

    chars = [e["chars"] for e in eps]
    run = longest_same_scene_run(eps)
    sents, hook_src = hook_sentences(text)
    kw_hits = {k: text.count(k) for k in CLICHE_KW if text.count(k) > 0}
    round_hits = {k: text.count(k) for k in DEROUND_KW if text.count(k) > 0}
    wall = {k: text.count(k) for k in PAYWALL_KW if text.count(k) > 0}

    data = {
        "file": os.path.basename(a.script),
        "episodes": len(eps),
        "total_chars": sum(chars),
        "avg_chars_per_ep": round(sum(chars) / len(chars), 1),
        "gini": gini(chars),                                   # SC-01 灌水信号
        "top3_share_pct": top_share(eps, 3),                   # SC-04 铺垫占比
        "top10_share_pct": top_share(eps, 10),
        "longest_ep": max(eps, key=lambda e: e["chars"])["no"],
        "shortest_ep": min(eps, key=lambda e: e["chars"])["no"],
        "same_scene_run": {"len": len(run),
                           "episodes": [x["no"] for x in run],
                           "scene": run[0]["label"] if run else ""},   # SC-03
        "hook_sentences": sents,
        "hook_source": hook_src,
        "hook_audit": hook_audit(sents),                       # SC-04
        "buried_peaks": find_buried_peak(eps),                 # SC-08
        "cliche_hits": kw_hits,
        "derounding_hits": round_hits,
        "paywall_signals": wall,
        "ep_chars": {str(e["no"]): e["chars"] for e in eps},
    }

    if a.vs:
        old = parse_episodes(read_text(a.vs))
        rows, deleted = compare_versions(eps, old)
        data["version_compare"] = {"vs": os.path.basename(a.vs),
                                   "new_eps": len(eps), "old_eps": len(old),
                                   "identical": sum(1 for r in rows if r[1] == "同一"),
                                   "minor": sum(1 for r in rows if r[1] == "小改"),
                                   "rewritten": sum(1 for r in rows if r[1] == "重写"),
                                   "added": [r[0] for r in rows if r[1] == "新增"],
                                   "deleted_old": deleted}
        data["version_rows"] = rows

    with open(os.path.join(outdir, "01_结构体检.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    L = []
    L.append("# 剧本结构体检表（自动生成，禁止手工编辑）\n")
    L.append("> 数据源：%s ｜ 规则映射 SC-01/03/04/05/06/07/08\n" % data["file"])
    L.append("## 一、体量与集中度\n")
    L.append("| 指标 | 数值 | 读法 |\n|---|---|---|")
    L.append("| 集数 | %d | |" % data["episodes"])
    L.append("| 总字数 | %d | |" % data["total_chars"])
    L.append("| 单集均字数 | %s | |" % data["avg_chars_per_ep"])
    L.append("| 字数基尼系数 | %s | >0.45 说明字数高度集中于少数集；<0.2 说明各集篇幅均匀（正常） |" % data["gini"])
    L.append("| 前3集字数占比 | %s%% | 铺垫占比，>20%% 需警惕 |" % data["top3_share_pct"])
    L.append("| 前10集字数占比 | %s%% | |" % data["top10_share_pct"])
    L.append("| 最长集 | 第%s集 | |" % data["longest_ep"])
    L.append("\n## 二、同场景连拍（SC-03）\n")
    if data["same_scene_run"]["len"] >= 2:
        L.append("**连续 %d 集锁在同一场景：第 %s 集**（%s）\n"
                 % (data["same_scene_run"]["len"],
                    "、".join(map(str, data["same_scene_run"]["episodes"])),
                    data["same_scene_run"]["scene"] or "场景名未标注"))
    else:
        L.append("未发现连续 2 集以上同场景。")
    L.append("\n## 三、开头三句体检（SC-04）\n")
    L.append("> 取句来源：%s\n" % data["hook_source"])
    for i, s in enumerate(data["hook_sentences"], 1):
        L.append("%d. %s" % (i, s))
    h = data["hook_audit"]
    L.append("\n| 打标 | 结果 |\n|---|---|")
    L.append("| 含数字锚点 | %s %s |" % ("是" if h["has_number"] else "**否**", h["numbers"] or ""))
    L.append("| 含伤害/冲突动作 | %s |" % ("是" if h["has_damage"] else "**否**"))
    L.append("| 含反击动作 | %s |" % ("是" if h["has_counter"] else "**否**"))
    L.append("| 仅为预告（无画面） | %s |" % ("**是**" if h["has_preview_only"] else "否"))
    L.append("| 可视化动作句数 | %d / %d |" % (h["visualizable"], len(data["hook_sentences"])))
    L.append("\n## 四、爆点埋深（SC-08）\n")
    L.append("| 关键词 | 首次出现 |\n|---|---|")
    for b in data["buried_peaks"]:
        L.append("| %s | 第%s集 |" % (b["kw"], b["ep"]))
    L.append("\n## 五、套路词频（SC-05，讨论清单非定罪）\n")
    L.append("、".join("%s×%d" % (k, v) for k, v in
                 sorted(data["cliche_hits"].items(), key=lambda x: -x[1])))
    L.append("\n## 六、降智冲突信号（SC-06）\n")
    L.append("、".join("%s×%d" % (k, v) for k, v in data["derounding_hits"].items())
             or "未命中预设信号词（不等于无降智，仍需人工读冲突合理性）")
    L.append("\n## 七、卡点/付费声明（SC-07）\n")
    L.append("、".join("%s×%d" % (k, v) for k, v in data["paywall_signals"].items()) or "无")

    if a.vs:
        vc = data["version_compare"]
        L.append("\n## 八、版本对比（SC-09）\n")
        L.append("新版 %d 集 / 旧版 %d 集：完全相同 **%d** 集，小改 %d 集，重写 %d 集，新增 %d 集\n"
                 % (vc["new_eps"], vc["old_eps"], vc["identical"], vc["minor"],
                    vc["rewritten"], len(vc["added"])))
        L.append("| 集 | 判定 | 相似度 |\n|---|---|---|")
        for no, kind, r in data["version_rows"]:
            L.append("| 第%s集 | %s | %s |" % (no, kind, r))
        if vc["added"]:
            L.append("\n**新增集：%s** —— 若新增集平均字数与旧版持平，即为增量灌水。"
                     % "、".join("第%s集" % x for x in vc["added"]))

    with open(os.path.join(outdir, "01_结构体检.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    print("[OK] 集数=%d 总字数=%d 基尼=%s 同场景最长=%d集(%s) 前3集占比=%s%%"
          % (data["episodes"], data["total_chars"], data["gini"],
             data["same_scene_run"]["len"],
             "、".join(map(str, data["same_scene_run"]["episodes"])) or "无",
             data["top3_share_pct"]))
    if a.vs:
        vc = data["version_compare"]
        print("[OK] 版本对比：相同%d集/新增%d集 → 新增 %s"
              % (vc["identical"], len(vc["added"]),
                 "、".join("第%s集" % x for x in vc["added"]) or "无"))
    print("[OUT] %s" % os.path.join(outdir, "01_结构体检.md"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
