# -*- coding: utf-8 -*-
"""统一路径与项目参数 —— 包内不含任何本机绝对路径 / 内网 IP / 项目专名。

必填环境变量：
  SHOTLIST_WORK   本地工作目录（放 _shot_dry 与中间产物）
  SHOTLIST_OUT    交付 outputs 目录（本地盘或 UNC 均可，由使用者自行提供）
可选：
  SHOTLIST_EPISODES          集数，默认 40
  SHOTLIST_TITLE             作品名，默认「本剧」
  SHOTLIST_COMPARE_PREFIX    台词中英对照文件名前缀，默认「台词中英对照」
  SHOTLIST_ROLE_MAP          角色中英映射 JSON 路径（换项目时覆盖脚本内置字典）

未设置必填项时明确报错退出，**绝不回落到任何内置项目路径**。
"""
import json
import os

REQUIRED = {
    "SHOTLIST_WORK": "本地工作目录（放 _shot_dry / 中间产物）",
    "SHOTLIST_OUT": "交付 outputs 目录",
}


def _required(name):
    v = os.environ.get(name, "").strip().strip('"').strip("'")
    if not v:
        raise SystemExit(
            "[配置缺失] 请先设置环境变量 %s（%s）\n"
            "  Bash:  export %s='/path/to/dir'\n"
            "  PowerShell: $env:%s='C:\\path\\to\\dir'\n"
            "本技能包不含任何默认项目路径，避免误连旧项目 / 内网地址。" % (name, REQUIRED[name], name, name)
        )
    return v


WORK = _required("SHOTLIST_WORK")
OUT = _required("SHOTLIST_OUT")
OUTDIR = OUT
DRY = os.path.join(WORK, "_shot_dry")
EP_MAX = int(os.environ.get("SHOTLIST_EPISODES", "40"))
TITLE = os.environ.get("SHOTLIST_TITLE", "本剧")
COMPARE_PREFIX = os.environ.get("SHOTLIST_COMPARE_PREFIX", "台词中英对照")


def load_role_map():
    """换项目时提供 JSON（中文名→英文标签），覆盖脚本内置字典。"""
    p = os.environ.get("SHOTLIST_ROLE_MAP", "").strip()
    if not p:
        return {}
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise SystemExit("[配置错误] SHOTLIST_ROLE_MAP 必须是 {中文名: 英文名} 的 JSON 对象")
    return data


def compare_file(ep):
    return "%s-第%d集.txt" % (COMPARE_PREFIX, ep)


def compare_bundle():
    return "%s-全%d集整合.txt" % (COMPARE_PREFIX, EP_MAX)


def compare_legacy():
    return "%s.txt" % COMPARE_PREFIX


def bundle_file():
    return "全剧%d集_整合文档_全段提示词.md" % EP_MAX
