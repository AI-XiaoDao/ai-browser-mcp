#Requires -Version 5.1
<#
.SYNOPSIS
  Pack GitHub Release zips (runtime + C++ reference) and sync generated-cpp.

.EXAMPLE
  .\release\pack-release.ps1 -Version 2.6.0
  .\release\pack-release.ps1 -Version 2.6.0 -Platform win32
  .\release\pack-release.ps1 -Version 2.6.0 -Platform all
#>
param(
    [Parameter(Mandatory = $true)]
    [string] $Version,
    [ValidateSet('x64', 'win32', 'all')]
    [string] $Platform = 'x64',
    [string] $RepoRoot = (Split-Path $PSScriptRoot -Parent),
    [switch] $SkipCppSync
)

$ErrorActionPreference = 'Stop'

$aiDir = Get-ChildItem -Path (Join-Path $RepoRoot 'CEFbro') -Directory -ErrorAction SilentlyContinue |
    Where-Object { (Get-ChildItem $_.FullName -Filter '*.vprj' -ErrorAction SilentlyContinue).Count -gt 0 } |
    Select-Object -First 1
if (-not $aiDir) { throw 'CEFbro project dir with .vprj not found' }

$platforms = if ($Platform -eq 'all') { @('x64', 'win32') } else { @($Platform) }
$uploadZips = @()

foreach ($plat in $platforms) {
    $linker = Get-ChildItem -Path $aiDir.FullName -Recurse -Directory -Filter 'linker' |
        Where-Object { $_.FullName -match "release\\$plat\\linker$" } |
        Select-Object -First 1
    if (-not $linker) { throw "linker not found: release/$plat/linker (compile Release $plat first)" }

    $project = Get-ChildItem -Path $aiDir.FullName -Recurse -Directory -Filter 'project' |
        Where-Object { $_.FullName -match "release\\$plat\\project$" } |
        Select-Object -First 1

    $runtimeZip = Join-Path $RepoRoot "AI-Browser-MCP-$plat-v$Version.zip"
    $cppZip = Join-Path $RepoRoot "AI-Browser-MCP-cpp-$plat-v$Version.zip"
    $staging = Join-Path $RepoRoot "_release_staging_$plat"

    Write-Host "[$plat] Linker: $($linker.FullName)"

    if (Test-Path $staging) { Remove-Item $staging -Recurse -Force }
    New-Item -ItemType Directory -Path $staging | Out-Null
    Get-ChildItem $linker.FullName | Where-Object { $_.Name -ne 'out' } | ForEach-Object {
        Copy-Item $_.FullName -Destination $staging -Recurse -Force
    }
    if (Test-Path $runtimeZip) { Remove-Item $runtimeZip -Force }
    Compress-Archive -Path (Join-Path $staging '*') -DestinationPath $runtimeZip -CompressionLevel Optimal
    Remove-Item $staging -Recurse -Force

    $rtMb = [math]::Round((Get-Item $runtimeZip).Length / 1MB, 2)
    Write-Host ("[$plat] OK runtime zip: {0} ({1} MB)" -f $runtimeZip, $rtMb)
    $uploadZips += $runtimeZip

    if ($project) {
        if (-not $SkipCppSync) {
            $genDir = Join-Path $aiDir.FullName "generated-cpp\release-$plat"
            if (Test-Path $genDir) { Remove-Item $genDir -Recurse -Force }
            New-Item -ItemType Directory -Path $genDir -Force | Out-Null
            robocopy $project.FullName $genDir /E /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
            Write-Host "[$plat] OK synced generated-cpp: $genDir"
        }
        if (Test-Path $cppZip) { Remove-Item $cppZip -Force }
        Compress-Archive -Path (Join-Path $project.FullName '*') -DestinationPath $cppZip -CompressionLevel Optimal
        $cppKb = [math]::Round((Get-Item $cppZip).Length / 1KB, 0)
        Write-Host ("[$plat] OK cpp zip: {0} ({1} KB)" -f $cppZip, $cppKb)
        $uploadZips += $cppZip
    } else {
        Write-Warning "[$plat] project/ not found, skip cpp zip"
    }
}

Write-Host ''
Write-Host "Upload to GitHub Release v$Version :"
Write-Host ("  gh release upload v$Version `"{0}`" -R AI-XiaoDao/ai-browser-mcp --clobber" -f ($uploadZips -join '" "'))
