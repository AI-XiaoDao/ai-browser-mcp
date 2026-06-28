# Push local commits to GitHub when git push to github.com:443 fails (api.github.com works).
# Usage: .\release\push-via-api.ps1
param(
    [string]$Repo = "AI-XiaoDao/ai-browser-mcp",
    [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
Set-Location (Split-Path $PSScriptRoot -Parent)

$remoteSha = (git rev-parse "origin/$Branch" 2>$null)
if (-not $remoteSha) { throw "Cannot resolve origin/$Branch" }

$commits = @(git log "$remoteSha..HEAD" --reverse --format=%H)
if ($commits.Count -eq 0) { Write-Host "Nothing to push."; exit 0 }

Write-Host "Pushing $($commits.Count) commit(s) via GitHub API to $Repo..."

function Get-CommitTreeSha([string]$CommitSha) {
    $c = gh api "repos/$Repo/git/commits/$CommitSha" | ConvertFrom-Json
    return $c.tree.sha
}

function Normalize-GitPath([string]$FilePath) {
    return $FilePath.Trim('"').Replace('/', [IO.Path]::DirectorySeparatorChar)
}

function New-GitBlob([string]$FilePath) {
    $rel = Normalize-GitPath $FilePath
    $full = Join-Path (Get-Location) $rel
    if (-not (Test-Path -LiteralPath $full)) { throw "File not found: $full" }
    $bytes = [System.IO.File]::ReadAllBytes($full)
    $b64 = [Convert]::ToBase64String($bytes)
    $payload = @{ encoding = "base64"; content = $b64 } | ConvertTo-Json -Compress
    $blob = $payload | gh api -X POST "repos/$Repo/git/blobs" --input - | ConvertFrom-Json
    return $blob.sha
}

$parentSha = $remoteSha
foreach ($commit in $commits) {
    $msg = ((git log -1 --format=%B $commit) -join "`n").TrimEnd()
    $baseTree = Get-CommitTreeSha $parentSha
    $entries = @()
    $addedModified = @(git -c i18n.logOutputEncoding=utf-8 -c core.quotepath=false diff-tree --no-commit-id -r --name-only --diff-filter=AM $commit)
    $deleted = @(git -c i18n.logOutputEncoding=utf-8 -c core.quotepath=false diff-tree --no-commit-id -r --name-only --diff-filter=D $commit)
    foreach ($path in $addedModified) {
        if ([string]::IsNullOrWhiteSpace($path)) { continue }
        $apiPath = (Normalize-GitPath $path) -replace '\\', '/'
        $sha = New-GitBlob $path
        $entries += @{ path = $apiPath; mode = "100644"; type = "blob"; sha = $sha }
    }
    foreach ($path in $deleted) {
        if ([string]::IsNullOrWhiteSpace($path)) { continue }
        $apiPath = (Normalize-GitPath $path) -replace '\\', '/'
        $entries += @{ path = $apiPath; mode = "100644"; sha = $null }
    }
    if ($entries.Count -eq 0) { throw "No file changes in $commit" }
    $treeBody = @{ base_tree = $baseTree; tree = @($entries) } | ConvertTo-Json -Depth 5 -Compress
    $tree = $treeBody | gh api -X POST "repos/$Repo/git/trees" --input - | ConvertFrom-Json
    $commitBody = @{
        message = $msg
        tree    = $tree.sha
        parents = @($parentSha)
    } | ConvertTo-Json -Compress
    $newCommit = $commitBody | gh api -X POST "repos/$Repo/git/commits" --input - | ConvertFrom-Json
    Write-Host "  + $($newCommit.sha.Substring(0,7)) $(git log -1 --format=%s $commit)"
    $parentSha = $newCommit.sha
}

$refBody = @{ sha = $parentSha; force = $false } | ConvertTo-Json -Compress
$null = $refBody | gh api -X PATCH "repos/$Repo/git/refs/heads/$Branch" --input -
Write-Host "Done. $Branch -> $parentSha"
git fetch origin $Branch 2>$null
git update-ref "refs/remotes/origin/$Branch" $parentSha 2>$null
