# -*- coding: utf-8 -*-
"""分镜台词行改造：台词纯英文 + 总旁白第三人称 + 按剧本补齐。
dry-run 输出到 _shot_dry/第N集/xxx.txt
"""
import re, io, os, sys, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import match_shotlist as M

from paths import WORK, OUT, OUTDIR, DRY, EP_MAX, TITLE, COMPARE_PREFIX, load_role_map, compare_file, compare_bundle, compare_legacy, bundle_file

# 剧本中文说话人 -> 分镜角色标签
ROLE = {
    "玛莎": "Martha", "艾瑞丝": "Iris", "布莱克": "Black", "波特": "Porter", "伊森": "Ethan",
    "格林": "Grimm", "沙文": "Shaven", "多米尼克": "Dominic", "男人A": "Man A", "男人B": "Man B",
    "前台": "Receptionist", "接线员": "Operator", "银行柜员": "Bank Teller", "司机": "Driver",
    "祖母": "Grandmother", "泽维尔老师": "Ms. Xavier", "屏幕文字VO": "Screen text",
    "屏幕文字": "Screen text", "住户A": "Resident A", "住户B": "Resident B",
    "住户C": "Resident C", "住户D": "Resident D", "便衣": "Plainclothes Officer",
    "女警": "Female Detective", "伪装老人": "Fake Old Man", "布莱克妻子": "Black's Wife",
}
# 换项目时用 SHOTLIST_ROLE_MAP 覆盖内置角色映射
ROLE.update(load_role_map())

# 分镜孤立行里可能出现的中文说话人 -> 英文名（含剧本用字差异，如 伊森/伊桑）
SPEAKER_CN2EN = {
    "伊桑": "Ethan", "伊森": "Ethan", "便衣警探": "Plainclothes Officer", "便衣": "Plainclothes Officer",
    "女警探": "Female Detective", "女警": "Female Detective", "假老人": "Fake Old Man",
    "伪装老人": "Fake Old Man", "玛莎": "Martha", "艾瑞丝": "Iris", "布莱克": "Black",
    "格林": "Grimm", "沙文": "Shaven", "波特": "Porter", "多米尼克": "Dominic",
    "男人A": "Man A", "男人B": "Man B", "银行柜员": "Bank Teller", "前台": "Receptionist",
    "接线员": "Operator", "祖母": "Grandmother", "泽维尔老师": "Ms. Xavier",
    "布莱克妻子": "Black's Wife", "住户A": "Resident A", "住户B": "Resident B",
    "司机": "Driver",
}

def map_speaker(txt):
    """把文本里的中文说话人替换成英文名（长的优先，避免部分覆盖）。"""
    for cn in sorted(SPEAKER_CN2EN, key=len, reverse=True):
        if cn in txt:
            txt = txt.replace(cn, SPEAKER_CN2EN[cn])
    return txt


def role_label(speaker):
    """剧本说话人 -> 插入行用的标签（先内部生成，再统一把中文说话人换成英文名）"""
    return map_speaker(_role_label(speaker))


def _role_label(speaker):
    """剧本说话人 -> 插入行用的标签"""
    s = speaker.strip()
    base = re.sub(r"[（(].*?[)）]", "", s).strip()
    if base.startswith("玛莎OS") or "OS" in base:
        who = base.replace("OS", "").strip() or "玛莎"
        return "OS：%s——" % ROLE.get(who, who)
    if base in ("旁白", "旁白VO"):
        return "旁白："
    if re.search(r"(VO|屏幕文字|音效)", s):
        who = re.sub(r"(VO|屏幕文字|音效)", "", base).strip("（）() 　")
        if who in ("接线员",):
            return "VO：Operator——"
        if who in ("男人A", "男人 A"):
            return "VO：Man A——"
        if who in ("男人B",):
            return "VO：Man B——"
        if who in ("祖母",):
            return "VO：Grandmother——"
        if who in ("屏幕文字", ""):
            return "VO：Screen text——"
        if who in ("布莱克妻子",):
            return "VO：Black's Wife——"
        if who in ("格林",):
            return "VO：Grimm——"
        if who in ("布莱克",):
            return "VO：Black——"
        if who in ("玛莎",):
            return "VO：Martha——"
        if who in ("艾瑞丝",):
            return "VO：Iris——"
        if who in ("波特",):
            return "VO：Porter——"
        if who in ("伊森",):
            return "VO：Ethan——"
        if who in ("沙文",):
            return "VO：Shaven——"
        return "VO：%s——" % (ROLE.get(who, who) or "VO")
    return "台词：%s——" % ROLE.get(base, base)

# ---------- 加载人工兜底 ----------
def load_json(name):
    p = os.path.join(WORK, name)
    if os.path.exists(p):
        return json.load(io.open(p, encoding="utf-8"))
    return {}

ORPHAN_CN = load_json("_orphan_cn.json")     # "第N集|file|line" -> {"label":..., "cn":..., "en":...}
SPLIT_CN = load_json("_split_cn.json")       # "第N集|gi|行序" -> cn

# ---------- 句子切分 ----------
def cn_sents(cn):
    parts = re.split(r"(?<=[。！？…])", cn)
    return [p for p in (x.strip() for x in parts) if p]

def cn_clauses(cn):
    parts = re.split(r"(?<=[。！？…，；])", cn)
    return [p for p in (x.strip() for x in parts) if p]

def en_sents(en):
    parts = re.split(r"(?<=[.!?])\s+", en)
    return [p for p in (x.strip() for x in parts) if p]

def en_clauses(en):
    parts = re.split(r"(?<=[.!?,;—])\s+", en)
    return [p for p in (x.strip() for x in parts) if p]

def tail_of(body):
    """取原行的语气说明（末尾的 ——xxx，且不含引号/角色台词的短说明）"""
    m = re.search(r"(——(?![^—]*\")[^—\"]{1,40})$", body)
    return m.group(1) if m else ""

def assign_sents(rows_en, cn, en):
    """一条目对应多行时，把中文/英文按顺序均分给各行；保证不重复不遗漏。"""
    cs, es = cn_sents(cn), en_sents(en)
    n = len(rows_en)
    if n <= 1 or not cs:
        return [(cn, en)]
    cc = cn_clauses(cn) or cs
    ec = en_clauses(en) or es
    out = []
    for k in range(n):
        a = int(k * len(cc) / n)
        b = max(int((k + 1) * len(cc) / n), a + 1)
        cn_part = "".join(cc[a:min(b, len(cc))]) or cc[min(a, len(cc) - 1)]
        ea = int(k * len(ec) / n)
        eb = max(int((k + 1) * len(ec) / n), ea + 1)
        en_part = " ".join(ec[ea:min(eb, len(ec))]) or ec[min(ea, len(ec) - 1)]
        out.append((cn_part, en_part))
    return out

# ---------- 使用 align 的结果 ----------
def build_episode(ep):
    ents = M.entries[ep]
    slist = M.parse_shots(ep)
    assign_map = {}
    insert_map = {}
    orphans = []
    if not ents:
        return assign_map, insert_map, orphans
    if not slist:
        # 该集没有任何台词行：把全部条目挂到第一个分镜文件
        src_dir = os.path.join(OUTDIR, "第%d集" % ep)
        files = sorted([f for f in os.listdir(src_dir) if f.endswith(".txt")], key=lambda x: (len(x), x))
        for e in ents:
            insert_map.setdefault(files[0][:-4] if files else "", []).append((-1, e, "after"))
        return assign_map, insert_map, orphans
    assign, missing = M.align(slist, ents)
    # 孤立行归并到邻近条目（拆分情形）；被标记 drop 的行不参与归并
    for i in range(len(slist)):
        if assign[i] is not None:
            continue
        kk = "%d|%s|%d" % (ep, slist[i]["file"], slist[i]["line"])
        if ORPHAN_CN.get(kk, {}).get("drop"):
            orphans.append((ep, slist[i]))
            continue
        j = None
        for k in range(i - 1, -1, -1):
            if assign[k] is not None:
                j = assign[k]
                break
        if j is None:
            for k in range(i + 1, len(slist)):
                if assign[k] is not None:
                    j = assign[k]
                    break
        if j is not None and M.sim(slist[i]["en"], ents[j]["en"]) >= 0.30:
            assign[i] = j
        else:
            orphans.append((ep, slist[i]))
    # 同条目多行 -> 句切分
    groups = {}
    for i, s in enumerate(slist):
        if assign[i] is not None:
            groups.setdefault(assign[i], []).append(i)
    sent_cache = {}
    for j, rows in groups.items():
        if len(rows) > 1:
            e = ents[j]
            pairs = assign_sents([slist[i]["en"] for i in rows], e["cn"], e["en"])
            for pos, i in enumerate(rows):
                sent_cache[i] = pairs[pos]
    for i, s in enumerate(slist):
        if assign[i] is not None:
            e = ents[assign[i]]
            if i in sent_cache:
                cn_o, en_o = sent_cache[i]
                assign_map[(s["file"], s["line"])] = (e, cn_o, en_o)
            else:
                assign_map[(s["file"], s["line"])] = (e, None, None)
    # 缺失条目 -> 插入锚点
    for k in missing:
        e = ents[k]
        prev = next((i for i in range(len(slist) - 1, -1, -1)
                     if assign[i] is not None and assign[i] < k), None)
        if prev is not None:
            insert_map.setdefault(slist[prev]["file"], []).append((slist[prev]["line"], e, "after"))
        else:
            nxt = next((i for i in range(len(slist))
                        if assign[i] is not None and assign[i] > k), None)
            if nxt is not None:
                insert_map.setdefault(slist[nxt]["file"], []).append((slist[nxt]["line"], e, "before"))
            else:
                insert_map.setdefault(slist[0]["file"], []).append((-1, e, "after"))
    return assign_map, insert_map, orphans

def clean_stray(pre, raw, s):
    """未匹配到剧本条目的旧格式台词行：剥离行内中文台词，说话人改英文。"""
    m = re.match(r"^(?P<head>[-•*#\s]*[^：]{1,24}[：:])(?P<body>.*)$", s)
    if not m:
        return raw
    head = m.group("head").replace("中英", "")
    body = m.group("body").strip()
    q = re.match(r'^(?P<pb>[^"]*)"(?P<cn>[^"]*)"(?P<rest>.*)$', body)
    if not q:
        return pre + head + map_speaker(body)
    rest = q.group("rest")
    tm = re.search(r"(——[^—]{1,40})$", rest)
    tail = tm.group(1) if tm else ""
    en = (rest[:tm.start()] if tm else rest).strip()
    if not en or not re.search(r"[A-Za-z]", en):
        return pre + head + map_speaker(body)      # 无英文可留，保持原样
    return pre + head + map_speaker(q.group("pb")) + '"%s"' % en + tail


def render_entry(e, indent="", multi_cn=None, multi_en=None):
    """生成一行台词文本（纯英文——中文会被视频模型当台词读出来，必须剥离）"""
    head = role_label(e["speaker"])
    en = (multi_en if multi_en is not None else e["en"]) or ""
    cn = (multi_cn if multi_cn is not None else e["cn"]) or ""
    txt = en.strip() or cn.strip()
    if not txt:
        return None
    return '%s%s"%s"' % (indent, head, txt)

# ---------- 主流程 ----------
os.makedirs(DRY, exist_ok=True)
STAT = []
ALL_ORPHANS = []
for ep in range(1, EP_MAX + 1):
    assign_map, insert_map, orphans = build_episode(ep)
    ALL_ORPHANS += orphans
    src_dir = os.path.join(OUTDIR, "第%d集" % ep)
    dst_dir = os.path.join(DRY, "第%d集" % ep)
    os.makedirs(dst_dir, exist_ok=True)
    files = sorted([f for f in os.listdir(src_dir) if f.endswith(".txt") and "英文台词" not in f],
                   key=lambda x: (len(x), x))
    n_ins = sum(len(v) for v in insert_map.values())
    STAT.append((ep, len(files), n_ins, len(orphans)))
    for fn in files:
        tag = fn[:-4]
        lines = io.open(os.path.join(src_dir, fn), encoding="utf-8").read().splitlines()
        is_md = any(l.strip().startswith("- ") for l in lines[:20])
        pre_ins = "- " if is_md else ""
        out = []
        ins_here = insert_map.get(tag, [])
        for i, raw in enumerate(lines):
            s = raw.strip()
            key = (tag, i)
            # 插到本行之前的条目
            for (al, e, mode) in ins_here:
                if mode == "before" and al == i:
                    r = render_entry(e, "")
                    if r:
                        out.append(pre_ins + r)
            m = re.match(r"^(?P<lab>[^：]{1,24})[：:](?P<body>.+)$", s)
            is_dlg = bool(m and re.search(r"(台词|旁白|OS|VO|屏幕文字|内心)",
                                          re.sub(r"^[-•*#\s]+", "", m.group("lab").strip())))
            if is_dlg:
                indent = raw[:len(raw) - len(raw.lstrip())]
                pre = "- " if raw.lstrip().startswith("-") else ""
                body = m.group("body").strip()
                tail = tail_of(body)
                if key in assign_map:
                    e, cno, eno = assign_map[key]
                    newline = render_entry(e, "", cno, eno)
                    out.append(pre + newline + tail if newline else raw)
                else:
                    ok = ORPHAN_CN.get("%d|%s|%d" % (ep, tag, i))
                    if ok:
                        if ok.get("drop"):
                            pass
                        elif "lines" in ok:
                            out.extend(ok["lines"])
                        else:
                            head = (ok.get("head") or "旁白：").replace("中英", "")
                            txt = (ok.get("en") or "").strip() or ok.get("cn", "")
                            out.append(pre + head + '"%s"' % txt + tail)
                    else:
                        out.append(clean_stray(pre, raw, s))
            else:
                out.append(raw)
            # 插到本行之后的条目
            for (al, e, mode) in ins_here:
                if mode != "before" and (al == i or (al == -1 and i == 0)):
                    r = render_entry(e, "")
                    if r:
                        out.append(pre_ins + r)
        io.open(os.path.join(dst_dir, fn), "w", encoding="utf-8").write("\n".join(out) + "\n")

print("ep files ins orphan")
for r in STAT:
    print("  第%2d集 段%2d 插入%3d 孤立%2d" % r)
print("孤立行合计", sum(r[3] for r in STAT), "| 待人工兜底", len([o for o in ALL_ORPHANS]))
with io.open(os.path.join(WORK, "_orphans2.txt"), "w", encoding="utf-8") as f:
    for ep, s in ALL_ORPHANS:
        f.write("第%d集|%s|%d | %s | %s\n" % (ep, s["file"], s["line"], s["label"], s["en"]))
