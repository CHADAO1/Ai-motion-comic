<#
.SYNOPSIS
  Update all vendored skill sources listed in vendor-manifest.json
  using `git subtree pull --squash`.

.USAGE
  powershell -ExecutionPolicy Bypass -File scripts/sync-vendor.ps1
  powershell -ExecutionPolicy Bypass -File scripts/sync-vendor.ps1 -Only anthropics-skills
  powershell -ExecutionPolicy Bypass -File scripts/sync-vendor.ps1 -DryRun

.NOTE
  git subtree requires a clean worktree. Commit or stash before running.
  After a successful run, commit and push to your own repository.
#>
param(
  [string]$Only = "",
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

$manifestPath = Join-Path $repo "vendor-manifest.json"
if (-not (Test-Path $manifestPath)) { throw "Manifest not found: $manifestPath" }
$manifest = Get-Content $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json

$dirty = git status --porcelain
if ($dirty -and -not $DryRun) {
  Write-Error "Worktree is dirty. Commit or stash first:`n$dirty"
  exit 1
}

foreach ($v in $manifest.vendors) {
  if ($Only -and $v.id -ne $Only) { continue }
  if ($v.strategy -ne "git-subtree-squash") {
    Write-Warning ("{0}: unknown strategy '{1}', skipped" -f $v.id, $v.strategy)
    continue
  }

  $label = "{0}  [{1}  ref={2}]" -f $v.id, $v.url, $v.ref
  Write-Host ("==> " + $label) -ForegroundColor Cyan
  if ($DryRun) {
    $preview = "git subtree pull --prefix={0} {1} {2} --squash" -f $v.prefix, $v.url, $v.ref
    Write-Host ("    [dry-run] " + $preview)
    continue
  }

  git subtree pull --prefix=$($v.prefix) $($v.url) $($v.ref) --squash
  if ($LASTEXITCODE -ne 0) {
    Write-Warning ("{0} failed. Check upstream breaking changes or local conflicts." -f $v.id)
  } else {
    Write-Host ("    OK  " + $v.id) -ForegroundColor Green
  }
}

if (-not $DryRun) {
  $manifest.updated = (Get-Date -Format "yyyy-MM-dd")
  $manifest | ConvertTo-Json -Depth 10 | Set-Content $manifestPath -Encoding UTF8
  Write-Host "`nvendor-manifest.json updated. Please commit / push." -ForegroundColor Green
}
