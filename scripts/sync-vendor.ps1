<#
.SYNOPSIS
  按 vendor-manifest.json 更新所有外部技能方案（git subtree pull --squash）。

.USAGE
  powershell -ExecutionPolicy Bypass -File scripts/sync-vendor.ps1
  powershell -ExecutionPolicy Bypass -File scripts/sync-vendor.ps1 -Only anthropics-skills
  powershell -ExecutionPolicy Bypass -File scripts/sync-vendor.ps1 -DryRun

.NOTE
  git subtree 需要干净的工作区；脚本会先检查。
  更新后记得 commit / push 到你自己的仓库。
#>
param(
  [string]$Only = "",
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

$manifestPath = Join-Path $repo "vendor-manifest.json"
if (-not (Test-Path $manifestPath)) { throw "找不到 $manifestPath" }
$manifest = Get-Content $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json

# 前置检查：工作区必须干净
$dirty = git status --porcelain
if ($dirty -and -not $DryRun) {
  Write-Error "工作区有未提交改动，请先 commit 或 stash：`n$dirty"
  exit 1
}

foreach ($v in $manifest.vendors) {
  if ($Only -and $v.id -ne $Only) { continue }
  if ($v.strategy -ne "git-subtree-squash") {
    Write-Warning "$($v.id)：未知策略 '$($v.strategy)'，跳过"
    continue
  }

  $cmd = "git subtree pull --prefix=$($v.prefix) $($v.url) $($v.ref) --squash"
  Write-Host "==> $($v.id)  [$($v.url) @ $($v.ref)]" -ForegroundColor Cyan
  if ($DryRun) { Write-Host "    [dry-run] $cmd"; continue }

  git subtree pull --prefix=$($v.prefix) $($v.url) $($v.ref) --squash
  if ($LASTEXITCODE -ne 0) {
    Write-Warning "    $($v.id) 更新失败：检查上游破坏性变更或本地冲突"
  } else {
    Write-Host "    OK  $($v.id)" -ForegroundColor Green
  }
}

if (-not $DryRun) {
  $manifest.updated = (Get-Date -Format "yyyy-MM-dd")
  $manifest | ConvertTo-Json -Depth 10 | Set-Content $manifestPath -Encoding UTF8
  Write-Host "`n已更新 vendor-manifest.json 的 updated 字段。请 commit / push。" -ForegroundColor Green
}
