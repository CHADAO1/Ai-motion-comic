# script-to-novel S5 校验脚本（用法: pwsh -File check_novel.ps1 <小说文件路径>）
param([string]$f = '<剧本目录>\满月囚笼：我的禁忌 Alpha\《满月囚笼：我的禁忌 Alpha》（小说版）.md')
$t = [System.IO.File]::ReadAllText($f)
"总字符数: $($t.Length)"
"章节数: $(([regex]::Matches($t, '## 第')).Count)"
"--- 制作痕迹残留（应全为0）---"
foreach ($b in '△','【字幕','【闪回','【幻象','OS','VO','人物：','镜头','特写','定格','闪回结束') {
  $c = ([regex]::Matches($t, [regex]::Escape($b))).Count
  "$b : $c"
}
"--- 场景标号(数字-数字+日/夜): $(([regex]::Matches($t, '\d+-\d+\s*[日夜]')).Count) ---"
"--- 续写marker残留: $(([regex]::Matches($t, '<!--待续-->')).Count) ---"
"--- 剧本式括号情绪台词残留 ---"
$bad2 = [regex]::Matches($t, '）：“')
"count: $($bad2.Count)"
$bad3 = [regex]::Matches($t, '）：[“"]')
"count(半角引号): $($bad3.Count)"
"--- 未标注角色名出现次数（应为0）---"
$pairs = @(
  @('莱拉（女1）', '莱拉(?!（女1）)'),
  @('凯尔（男1）', '凯尔(?!（男1）)'),
  @('伊蒙（男2）', '伊蒙(?!（男2）)'),
  @('梅拉（女2）', '梅拉(?!（女2）)'),
  @('奥尔登长老（反1）', '奥尔登(?!长老（反1）)')
)
foreach ($p in $pairs) {
  $total = [regex]::Matches($t, [regex]::Escape($p[0])).Count
  $untag = [regex]::Matches($t, $p[1])
  "{0} 总计:{1} 未标注:{2}" -f $p[0], $total, $untag.Count
  foreach ($m in $untag) { $s = [Math]::Max(0, $m.Index - 15); $len = [Math]::Min(40, $t.Length - $s); "    …$($t.Substring($s, $len).Replace("`n", '/'))…" }
}
"--- BOM检查 ---"
$bytes = [System.IO.File]::ReadAllBytes($f)
if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB) { "有BOM" } else { "无BOM(正确)" }
