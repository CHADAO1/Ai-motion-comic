# 补全角色名标注 + 直角引号规范化（用法: pwsh -File fix_tags.ps1 <文件路径>）
param([string]$f = '<剧本目录>\满月囚笼：我的禁忌 Alpha\《满月囚笼：我的禁忌 Alpha》（小说版）.md')
$t = [System.IO.File]::ReadAllText($f)

# 1) 引号配对规范化（半角 " -> 全角 “ ” 交替）
$q = ([regex]::Matches($t, '"')).Count
"半角引号数量: $q"
if ($q % 2 -eq 0 -and $q -gt 0) {
  $sb = New-Object System.Text.StringBuilder
  $open = $false
  foreach ($ch in $t.ToCharArray()) {
    if ($ch -eq '"') { if ($open) { [void]$sb.Append('”') } else { [void]$sb.Append('“') }; $open = -not $open }
    else { [void]$sb.Append($ch) }
  }
  $t = $sb.ToString()
  "引号已规范化为全角"
}

# 2) 角色名补标（负向先行断言防重复）
$pairs = @(
  @('莱拉(?!（女1）)', '莱拉（女1）'),
  @('凯尔(?!（男1）)', '凯尔（男1）'),
  @('伊蒙(?!（男2）)', '伊蒙（男2）'),
  @('梅拉(?!（女2）)', '梅拉（女2）'),
  @('奥尔登长老(?!（反1）)', '奥尔登长老（反1）'),
  @('奥尔登(?!长老（反1）)(?!长老)', '奥尔登长老（反1）')
)
foreach ($p in $pairs) {
  $n = ([regex]::Matches($t, $p[0])).Count
  $t = [regex]::Replace($t, $p[0], $p[1])
  "{0} -> 补标 {1} 处" -f $p[1], $n
}

[System.IO.File]::WriteAllText($f, $t, (New-Object System.Text.UTF8Encoding($false)))
"已写回文件"
