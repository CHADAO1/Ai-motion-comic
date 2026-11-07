# HTML 模板 — 一页式分镜看板（单文件自包含）

> 产出永远是**单文件 HTML**，把本页的 house CSS 与 JS 原样内嵌，按占位符填充即可。CSS/JS 全内嵌 → 双击即开、可离线、可投屏、可打印/存 PDF。
> 颜色按用户主题自适应（见 `<html> data-theme`）；分镜表为深底表盘风格，提示词块可一键复制。

## 一、结构（整页骨架）

```html
<!DOCTYPE html>
<html lang="zh-CN" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>分镜看板 — Scenes {SCOPE}（{PIPELINE} · Seedance 提示词）</title>
<style>
/* ================= HOUSE CSS ================= */
:root{
  --bg:#0e0e10; --panel:#18181b; --panel2:#1f1f23; --line:#2d2d33;
  --txt:#e5e5e5; --muted:#a1a1aa; --dim:#71717a;
  --accent:#22c55e; --accent2:#3b82f6;
  --badge-ws:#f59e0b; --badge-ms:#10b981; --badge-cu:#3b82f6;
  --badge-ecu:#8b5cf6; --badge-macro:#ec4899; --badge-pan:#14b8a6;
  --badge-os:#f43f5e; --badge-vo:#eab308; --badge-dis:#6b7280;
}
html[data-theme="light"]{
  --bg:#f5f5f6; --panel:#ffffff; --panel2:#f0f0f2; --line:#dcdcdf;
  --txt:#1a1a1a; --muted:#52525b; --dim:#8a8a93;
  --badge-ws:#b45309; --badge-ms:#047857; --badge-cu:#1d4ed8;
  --badge-ecu:#6d28d9; --badge-macro:#be185d; --badge-pan:#0f766e;
  --badge-os:#be123c; --badge-vo:#a16207; --badge-dis:#4b5563;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--txt);
  font:14px/1.6 -apple-system,"Segoe UI","Microsoft YaHei",Roboto,sans-serif}
.container{max-width:1500px;margin:0 auto;padding:20px 24px 60px}
header.top{border-bottom:1px solid var(--line);padding-bottom:16px;margin-bottom:16px}
header.top h1{font-size:22px;margin:0 0 4px;letter-spacing:.3px}
header.top .sub{color:var(--muted);font-size:12px}
.stats{display:flex;gap:12px;margin-top:14px;flex-wrap:wrap}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:10px;
  padding:10px 18px;min-width:90px;text-align:center}
.stat .v{font-size:24px;font-weight:700;color:var(--accent)}
.stat .l{font-size:11px;color:var(--muted)}
.pipeline{display:inline-block;margin-left:8px;font-size:11px;color:var(--accent2);
  border:1px solid var(--accent2);border-radius:4px;padding:1px 6px;vertical-align:middle}
.toolbar{display:flex;gap:10px;margin:0 0 14px;flex-wrap:wrap}
.toolbar input[type=text],.toolbar select{
  background:var(--panel);border:1px solid var(--line);color:var(--txt);
  border-radius:6px;padding:8px 12px;font-size:13px;flex:1;min-width:200px}
.toolbar select{flex:0 0 auto;min-width:180px}
.toolbar button{background:#27272a;border:1px solid #3f3f46;color:var(--txt);
  border-radius:6px;padding:8px 14px;font-size:13px;cursor:pointer}
html[data-theme="light"] .toolbar button{background:#e4e4e7;border-color:#d4d4d8}
.toolbar button.clear{background:transparent;color:var(--muted)}
.toc{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 16px}
.toc-row{display:flex;flex-wrap:wrap;gap:6px}
.toc-label{color:var(--muted);font-size:12px;line-height:28px;margin-right:4px}
.toc a{background:var(--panel);border:1px solid var(--line);color:var(--txt);
  border-radius:6px;padding:2px 10px;font-size:12px;text-decoration:none}
.toc a:hover{border-color:var(--accent)}
section.scene{background:var(--panel);border:1px solid var(--line);
  border-radius:12px;margin:0 0 18px;overflow:hidden}
section.scene.pal-red{border-left:4px solid var(--accent2)}
.scene-head{padding:14px 18px 10px;border-bottom:1px solid var(--line)}
.scene-num-row{display:flex;align-items:center;gap:8px}
.scene-num{font-size:12px;font-weight:700;color:var(--accent);
  background:rgba(34,197,94,.12);padding:2px 8px;border-radius:4px}
.scene-title{font-size:17px;margin:6px 0 2px}
.scene-meta{display:flex;flex-wrap:wrap;gap:14px;color:var(--muted);font-size:12px}
.scene-meta b{color:var(--txt)}
.shot-count{color:var(--accent2);margin-left:auto}
.table-wrap{padding:0 0 4px;overflow-x:auto}
table.shotlist{width:100%;border-collapse:collapse}
table.shotlist th{background:var(--panel2);color:var(--muted);font-size:11px;
  text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);white-space:nowrap}
table.shotlist td{padding:8px 10px;border-bottom:1px solid var(--line);
  vertical-align:top;font-size:12.5px}
tr:last-child td{border-bottom:none}
td.c-num{color:var(--dim);font-weight:600;white-space:nowrap}
td.c-cam{color:var(--txt);white-space:nowrap}
td.c-act{color:var(--txt)}
td.c-script,td.c-prompt{background:var(--panel2)}
.script-inner{color:var(--muted);white-space:pre-wrap;font-size:12px}
.prompt-block{white-space:pre-wrap;font-family:ui-monospace,Consolas,"Courier New",monospace;
  font-size:11.5px;line-height:1.65;color:#d6f5e3;
  background:#101311;border:1px solid #1f2b23;border-radius:6px;padding:10px}
html[data-theme="light"] .prompt-block{color:#065f46;background:#ecfdf5;border-color:#d1fae5}
.badge{display:inline-block;border-radius:4px;padding:1px 7px;font-size:10.5px;
  font-weight:600;color:#fff;letter-spacing:.3px}
.p-ws{background:var(--badge-ws)}.p-ms{background:var(--badge-ms)}
.p-cu{background:var(--badge-cu)}.p-ecu{background:var(--badge-ecu)}
.p-macro{background:var(--badge-macro)}.p-pan{background:var(--badge-pan)}
.p-os{background:var(--badge-os)}.p-vo{background:var(--badge-vo)}
.p-dis{background:var(--badge-dis)}
.empty-state{text-align:center;color:var(--dim);padding:30px}
.prompt-label{display:flex;align-items:center;gap:8px;margin:10px 0 4px}
.prompt-label b{color:var(--accent)}
.prompt-label span{color:var(--dim);font-size:10px}
.copy-btn{background:#27272a;border:1px solid #3f3f46;color:var(--accent);
  border-radius:4px;padding:1px 8px;font-size:11px;cursor:pointer}
html[data-theme="light"] .copy-btn{background:#e4e4e7;border-color:#d4d4d8}
.copy-btn:hover{border-color:var(--accent)}
.copy-btn.copied{background:var(--accent);color:#fff;border-color:var(--accent)}
@media print{.toolbar,.toc{display:none}body{background:#fff}
  section.scene{break-inside:avoid;border:1px solid #ccc}}
</style>
</head>
<body>
<div class="container">
  <header class="top">
    <h1>分镜看板 — Scenes {SCOPE}<span class="pipeline">{PIPELINE}</span></h1>
    <div class="sub">Prepared for {USERNAME} · {N_SHOTS} shots · {N_SCENES} scenes · {N_PROMPTS} prompts · {N_PLANS} plan types · 中文 Seedance 提示词</div>
    <div class="stats">
      <div class="stat"><div class="v">{N_SCENES}</div><div class="l">场 scenes</div></div>
      <div class="stat"><div class="v">{N_SHOTS}</div><div class="l">镜头 shots</div></div>
      <div class="stat"><div class="v">{N_PROMPTS}</div><div class="l">提示词段 prompts</div></div>
      <div class="stat"><div class="v">{N_PLANS}</div><div class="l">类型 plan types</div></div>
    </div>
  </header>

  <div class="toolbar">
    <input type="text" id="search" placeholder="搜索文字 / 对白 / 地点…">
    <select id="planFilter"><option value="">全部镜头类型</option>{PLAN_OPTIONS}</select>
    <button onclick="window.print()">🖨 打印 / PDF</button>
    <button class="clear" onclick="resetFilters()">重置</button>
  </div>

  <div class="toc"><div class="toc-row"><span class="toc-label">场景：</span>{TOC_LINKS}</div></div>

  {SCENE_BLOCKS}

  <div class="empty-state" id="emptyState" style="display:none;">无匹配结果。试试重置筛选。</div>
</div>

<script>
function resetFilters(){document.getElementById('search').value='';document.getElementById('planFilter').value='';filterRows();}
function filterRows(){
  var q=(document.getElementById('search').value||'').toLowerCase().trim();
  var p=document.getElementById('planFilter').value;
  var rows=document.querySelectorAll('tr[data-scene]');
  var any=false;
  Array.prototype.forEach.call(rows,function(r){
    var txt=(r.textContent||'').toLowerCase();
    var plan=r.getAttribute('data-plan')||'';
    var ok=(!q||txt.indexOf(q)>=0)&&(!p||plan===p);
    r.style.display=ok?'':'none';
    if(ok)any=true;
  });
  var scenes=document.querySelectorAll('section.scene');
  Array.prototype.forEach.call(scenes,function(sc){
    var vis=sc.querySelectorAll('tr[data-scene]');
    var show=false;
    Array.prototype.forEach.call(vis,function(r){if(r.style.display!=='none')show=true;});
    sc.style.display=show?'':'none';
  });
  document.getElementById('emptyState').style.display=any?'':'none';
}
document.addEventListener('input',function(e){if(e.target&&e.target.id==='search')filterRows();});
document.addEventListener('click',function(e){
  if(e.target.classList&&e.target.classList.contains('copy-btn')){
    var btn=e.target;
    var wrap=btn.closest('.prompt-wrap');
    var block=wrap.querySelector('.prompt-block');
    var text=block.textContent.trim();
    navigator.clipboard.writeText(text).then(function(){
      btn.textContent='✓ 已复制'; btn.classList.add('copied');
      setTimeout(function(){btn.textContent='Copy';btn.classList.remove('copied');},1200);
    });
  }
});
document.getElementById('planFilter').addEventListener('change',filterRows);
</script>
</body>
</html>
```

## 二、逐场 section（嵌入 {SCENE_BLOCKS}）

```html
<section class="scene pal-red" id="sc{N}">
  <div class="scene-head">
    <div class="scene-num-row"><span class="scene-num">SCENE {N}</span></div>
    <h2 class="scene-title">{INT_EXT_HEADER}</h2>
    <div class="scene-meta">
      <span><b>地点 Location:</b> {LOCATION_DESC}</span>
      <span><b>情绪 Mood:</b> <i>{MOOD}</i></span>
      <span class="shot-count">{N_SHOTS} 镜</span>
    </div>
  </div>
  <div class="table-wrap">
    <table class="shotlist">
      <colgroup>
        <col style="width:46px"><col style="width:110px"><col style="width:130px">
        <col style="width:auto"><col style="width:26%"><col style="width:32%">
      </colgroup>
      <thead><tr><th>#</th><th>Plan</th><th>Camera</th><th>Action</th><th>场景文本 Scene text</th><th>Seedance 提示词</th></tr></thead>
      <tbody>{SHOT_ROWS_WITH_PROMPTS}</tbody>
    </table>
  </div>
</section>
```

## 三、镜头行 + 提示词格

首行携带 rowspan 的 `c-script`/`c-prompt`；组内后续行只有 `c-num/c-plan/c-cam/c-act`。

```html
<tr data-scene="{N}" data-plan="{PLAN_CODE}">
  <td class="c-num">{SHOT_NUM}</td>
  <td class="c-plan"><span class="badge p-{PLAN_CLASS}">{PLAN_LABEL}</span></td>
  <td class="c-cam">{CAMERA_NOTE}</td>
  <td class="c-act">{ACTION_BEAT_EN}</td>
  <td class="c-script" rowspan="{GROUP_SIZE}"><div class="script-inner">{FULL_SCENE_TEXT_EN}</div></td>
  <td class="c-prompt" rowspan="{GROUP_SIZE}">{PROMPT_BLOCKS}</td>
</tr>
{ADDITIONAL_ROWS_NO_RIGHT_CELLS}
```

## 四、提示词块（每 15 秒 / ≤30 秒一段）

```html
<div class="prompt-wrap">
  <div class="prompt-label"><b>提示词 {N}</b><span>[{TAG}]</span>
    <button class="copy-btn">Copy</button></div>
  <div class="prompt-block">{CHINESE_PROMPT}</div>
</div>
```

`{TAG}` 是一句括号速记，如 `[MS-CU · 门开+靴入门]`、`[ECU · 拍立得滑出+手伸入]`。

## 五、Plan 类型徽章映射（data-plan + 徽章类）

| Code | 全称 | 徽章类 | 用途 |
|---|---|---|---|
| `WS` | Wide shot | `p-ws` | 建立、全身、地点侧重 |
| `MS` | Medium shot | `p-ms` | 半身、对白、双人 |
| `CU` | Close-up | `p-cu` | 头肩、反应 |
| `ECU` | Extreme close-up | `p-ecu` | 眼睛/手/道具/屏幕 |
| `MACRO` | Macro | `p-macro` | 毛孔/水滴/织物 |
| `PAN` | Pan | `p-pan` | 横/纵摇 |
| `OS` | Off-screen sound | `p-os` | 画外音效 |
| `VO` | Voice-over | `p-vo` | 旁白压在前画面 |
| `DISSOLVE` | Dissolve | `p-dis` | 转场 |

筛选下拉 option value 用 Code，显示用全称：
```html
<option value="CU">Close-up</option>
```

## 六、填充清单（交付前核对）

- [ ] `{SCOPE}` / `{PIPELINE}`（如 `P1 · 9:16 · Seedance 2.0 · 中文`）
- [ ] `{USERNAME}` / `{N_SHOTS}` / `{N_SCENES}` / `{N_PROMPTS}` / `{N_PLANS}`
- [ ] `{PLAN_OPTIONS}`：`<option value="{CODE}">{LABEL}</option>` 循环
- [ ] `{TOC_LINKS}`：`<a href="#sc{N}">SC {N}</a>` 循环
- [ ] `{SCENE_BLOCKS}`：逐场 section（含全部 `{SHOT_ROWS_WITH_PROMPTS}`）
- [ ] 每段 `{TAG}` 与 `{CHINESE_PROMPT}` 已填；Copy 逻辑已内嵌
