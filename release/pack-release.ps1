#Requires -Version 5.1
<#
.SYNOPSIS
  打包 GitHub Release：运行包（排除 linker/out）+ C++ 对照 zip，并同步 generated-cpp。

.EXAMPLE
  .\release\pack-release.ps1 -Version 2.6.0
#>
param(
    [Parameter(Mandatory = $true)]
    [string] $Version,
    [string] $RepoRoot = (Split-Path $PSScriptRoot -Parent),
    [switch] $SkipCppSync
)

$ErrorActionPreference = 'Stop'

# 定位 CEFbro/AI浏览器 工程目录
$aiDir = Get-ChildItem -Path (Join-Path $RepoRoot 'CEFbro') -Directory -ErrorAction SilentlyContinue |
    Where-Object { (Get-ChildItem $_.FullName -Filter '*.vprj' -ErrorAction SilentlyContinue).Count -gt 0 } |
    Select-Object -First 1
if (-not $aiDir) { throw "找不到含 .vprj 的 CEFbro 子目录" }

$linker = Get-ChildItem -Path $aiDir.FullName -Recurse -Directory -Filter 'linker' |
    Where-Object { $_.FullName -match 'release\\x64\\linker$' } |
    Select-Object -First 1
if (-not $linker) { throw "未找到 _int/.../release/x64/linker，请先编译 Release x64" }

$project = Get-ChildItem -Path $aiDir.FullName -Recurse -Directory -Filter 'project' |
    Where-Object { $_.FullName -match 'release\\x64\\project$' } |
    Select-Object -First 1

$runtimeZip = Join-Path $RepoRoot "AI-Browser-MCP-x64-v$Version.zip"
$cppZip     = Join-Path $RepoRoot "AI-Browser-MCP-cpp-x64-v$Version.zip"
$staging    = Join-Path $RepoRoot "_release_staging"

Write-Host "Linker: $($linker.FullName)"

# --- 运行包（排除 out/）---
if (Test-Path $staging) { Remove-Item $staging -Recurse -Force }
New-Item -ItemType Directory -Path $staging | Out-Null
Get-ChildItem $linker.FullName | Where-Object { $_.Name -ne 'out' } | ForEach-Object {
    Copy-Item $_.FullName -Destination $staging -Recurse -Force
}
if (Test-Path $runtimeZip) { Remove-Item $runtimeZip -Force }
Compress-Archive -Path (Join-Path $staging '*') -DestinationPath $runtimeZip -CompressionLevel Optimal
Remove-Item $staging -Recurse -Force

$rtMb = [math]::Round((Get-Item $runtimeZip).Length / 1MB, 2)
Write-Host "OK runtime zip: $runtimeZip ($rtMb MB)"

# --- C++ 对照 zip + 同步 generated-cpp ---
if ($project) {
    if (-not $SkipCppSync) {
        $genDir = Join-Path $aiDir.FullName 'generated-cpp\release-x64'
        if (Test-Path $genDir) { Remove-Item $genDir -Recurse -Force }
        New-Item -ItemType Directory -Path $genDir -Force | Out-Null
        robocopy $project.FullName $genDir /E /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
        Write-Host "OK synced generated-cpp: $genDir"
    }
    if (Test-Path $cppZip) { Remove-Item $cppZip -Force }
    Compress-Archive -Path (Join-Path $project.FullName '*') -DestinationPath $cppZip -CompressionLevel Optimal
    $cppKb = [math]::Round((Get-Item $cppZip).Length / 1KB, 0)
    Write-Host "OK cpp zip: $cppZip ($cppKb KB)"
} else {
    Write-Warning "未找到 project/，跳过 cpp zip"
}

Write-Host ""
Write-Host "Upload to GitHub Release v$Version :"
Write-Host "  gh release upload v$Version `"$runtimeZip`" `"$cppZip`" -R AI-XiaoDao/ai-browser-mcp --clobber"
