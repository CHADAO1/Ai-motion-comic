# -*- coding: utf-8 -*-
"""把分镜里每条台词/旁白行 对齐到 剧本标准条目（顺序单调 DP），输出报告+json。"""
import re, json, io, os

from paths import WORK, OUT, OUTDIR, DRY, EP_MAX, TITLE, COMPARE_PREFIX, load_role_map, compare_file, compare_bundle, compare_legacy, bundle_file

STOP = {"the","a","an","and","to","of","in","it","is","was","that","her","she","he","his","at","on",
        "for","with","as","my","me","we","i","you","they","them","their","but","not","no","do","did",
        "had","has","have","be","been","out","up","down","when","then","so","if","just","here","there"}

def norm(s):
    return re.sub(r"[\s\"'“”‘’，。！？、…—\-–/／,.!?;:：（）()【】]+", "", s or "")

def words(s):
    return set(w for w in re.findall(r"[A-Za-z']{2,}", (s or "").lower()) if w not in STOP)

def sim(a, b):
    A, B = words(a), words(b)
    if not A or not B:
        return 0.0
    base = 2.0 * len(A & B) / (len(A) + len(B))
    na, nb = norm(a), norm(b)
    if na and nb and (na in nb or nb in na):
        base = max(base, 0.85)
    if na == nb:
        base = 1.0
    return base

# ---------- 1. 对照文件条目 ----------
entries = {}
for ep in range(1, EP_MAX + 1):
    fp = os.path.join(OUTDIR, compare_file(ep))
    lst, scene, speaker, cn = [], "?", None, None
    if os.path.exists(fp):
        for l in io.open(fp, encoding="utf-8").read().splitlines():
            l = l.strip()
            m = re.match(r"^【(.+?)】$", l)
            if m:
                scene = m.group(1); continue
            if l.startswith("中文："):
                cn = l[3:].strip(); continue
            if l.startswith("英文："):
                if speaker:
                    lst.append({"scene": scene, "speaker": speaker, "cn": cn,
                                "en": l[3:].strip().strip('"')})
                speaker, cn = None, None; continue
            if l and l.endswith("：") and not l.startswith(("《", "（", "中文", "英文")):
                speaker = l[:-1].strip()
    # 给每条加全局序号
    for k, e in enumerate(lst):
        e["gi"] = k
    entries[ep] = lst

# ---------- 2. 分镜行 ----------
def extract_en(kind, body):
    """从行体里抽英文"""
    if kind == "old":
        m = re.search(r'"(.*?)"\s*(?:——|--|$)', body)
        if not m:
            m = re.search(r'"([^"]+)"', body)
        return (m.group(1) if m else "").strip(), None
    else:
        # v2: 角色——"中文" English   或  "中文" English
        if body.strip() in ("（无）", "(无)", "无", "—"):
            return "", None
        m = re.match(r'^(?P<speaker>[^—\-]{0,12})[—\-]{1,2}\s*"(?P<cn>[^"]*)"\s*(?P<en>.*)$', body)
        if m:
            return m.group("en").strip(), m.group("cn").strip()
        m = re.match(r'^"(?P<cn>[^"]*)"\s*(?P<en>.*)$', body)
        if m:
            return m.group("en").strip(), m.group("cn").strip()
        return body.strip(), None

def parse_shots(ep):
    d = os.path.join(OUTDIR, "第%d集" % ep)
    res = []
    if not os.path.isdir(d):
        return res
    files = [f for f in os.listdir(d) if f.endswith(".txt") and not f.endswith("英文台词.txt")]
    files.sort(key=lambda x: (len(x), x))
    for fn in files:
        tag = fn[:-4]
        scene = re.sub(r"[a-z]+$", "", tag)
        lines = io.open(os.path.join(d, fn), encoding="utf-8").read().splitlines()
        for i, raw in enumerate(lines):
            s = raw.strip()
            m = re.match(r"^(?P<label>[^：]{1,24})[：:](?P<body>.+)$", s)
            if not m:
                continue
            label, body = m.group("label").strip(), m.group("body").strip()
            label = re.sub(r"^[-•*#\s]+", "", label).strip()
            if not re.search(r"(台词|旁白|OS|VO|屏幕文字|内心)", label):
                continue
            if label.startswith(("说话语气",)):
                continue
            kind = "v2" if label.startswith(("中英台词", "中英旁白", "中英OS")) else "old"
            en, cn = extract_en(kind, body)
            kind2 = "v2" if kind == "v2" else ("os" if "OS" in label else
                                              ("vo" if "VO" in label or "屏幕文字" in label else
                                               ("nar" if "旁白" in label else "dlg")))
            res.append({"file": tag, "scene": scene, "line": i, "raw": raw, "label": label,
                        "body": body, "kind": kind2, "en": en, "cn_v2": cn})
    return res

# ---------- 3. scene 内 DP 对齐 ----------
def align(shot_lines, ents):
    """窗口化的顺序贪心 + 夹逼补配。返回 (assign, missing)。"""
    n, m = len(shot_lines), len(ents)
    assign = [None] * n
    if n == 0 or m == 0:
        return assign, list(range(m))
    S = [[sim(shot_lines[i]["en"], ents[j]["en"]) for j in range(m)] for i in range(n)]
    prev = -1
    for i in range(n):
        lo, hi = max(0, prev - 1), min(m, prev + 6)
        best, bj = 0.0, None
        for j in range(lo, hi):
            if S[i][j] > best:
                best, bj = S[i][j], j
        if bj is not None and best >= 0.42:
            assign[i] = bj
            prev = bj
    # 夹逼补配：未分配的连续块，用前后已分配条目之间的候选按序/按相似度填
    i = 0
    while i < n:
        if assign[i] is not None:
            i += 1
            continue
        k = i
        while k < n and assign[k] is None:
            k += 1
        left = assign[i - 1] if i > 0 else -1
        right = assign[k] if k < n else m
        cands = list(range(left + 1, right))
        blk = list(range(i, k))
        if cands and len(cands) == len(blk):
            for a, b in zip(blk, cands):
                assign[a] = b
        elif cands:
            for a in blk:
                best, bj = 0.0, None
                for j in cands:
                    if S[a][j] > best:
                        best, bj = S[a][j], j
                if bj is not None and best >= 0.25:
                    assign[a] = bj
                    cands.remove(bj)
        i = k
    used = set(a for a in assign if a is not None)
    return assign, [k for k in range(m) if k not in used]

# ---------- 4. 汇总 ----------
report, outjson = [], {}
TOT = [0, 0, 0, 0]  # 条目数, 行数, 命中行(>=0.3), 未覆盖条目
for ep in range(1, EP_MAX + 1):
    ents = entries[ep]
    shots = parse_shots(ep)
    by_scene_ents, by_scene_shots = {}, {}
    for e in ents:
        by_scene_ents.setdefault(e["scene"], []).append(e)
    for s in shots:
        by_scene_shots.setdefault(s["scene"], []).append(s)
    ep_res = {"entries": ents, "shots": shots, "pairs": [], "missing": []}
    for sc, elist in by_scene_ents.items():
        slist = by_scene_shots.get(sc, [])
        assign, missing = align(slist, elist)
        lowconf = 0
        # 合并行检测：未被分配的条目若已被某行的英文片段覆盖，不算缺
        covered_by = {}
        still = []
        for k in missing:
            ne = norm(elist[k]["en"])
            hit_by = None
            if len(ne) >= 6:
                for i, s in enumerate(slist):
                    nl = norm(s["en"])
                    if nl and (ne in nl or (len(nl) >= 8 and nl in ne and assign[i] is None)):
                        hit_by = i
                        break
            if hit_by is not None:
                covered_by[k] = hit_by
            else:
                still.append(k)
        missing = still
        for i, s in enumerate(slist):
            ep_res["pairs"].append({"file": s["file"], "line": s["line"], "raw": s["raw"],
                                    "label": s["label"], "kind": s["kind"], "en": s["en"],
                                    "hit": (elist[assign[i]]["gi"] if assign[i] is not None else None),
                                    "score": (round(sim(s["en"], elist[assign[i]]["en"]), 2)
                                              if assign[i] is not None else 0)})
        for k in missing:
            ep_res["missing"].append(elist[k])
        report.append("=== 第%d集 %s | 条目%d 行%d 命中%d 低信%d 合并覆盖%d 缺%d" %
                      (ep, sc, len(elist), len(slist),
                       sum(1 for a in assign if a is not None), lowconf, len(covered_by), len(missing)))
        for k in missing:
            report.append("   [缺] %s %s: %s" % (elist[k]["scene"], elist[k]["speaker"], elist[k]["cn"][:50]))
        for i, s in enumerate(slist):
            if assign[i] is None:
                report.append("   [杂] %s | %s | %s" % (s["file"], s["label"], s["en"][:60]))
    outjson[ep] = ep_res
    TOT[0] += len(ents); TOT[1] += len(shots)
    TOT[2] += sum(1 for p in ep_res["pairs"] if p["hit"] is not None)
    TOT[3] += len(ep_res["missing"])

with io.open(os.path.join(WORK, "_shot_match.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(report) + "\n")
with io.open(os.path.join(WORK, "_shot_match.json"), "w", encoding="utf-8") as f:
    json.dump(outjson, f, ensure_ascii=False, indent=1)
print("TOTAL 条目%d 行%d 命中%d 缺%d" % tuple(TOT))
