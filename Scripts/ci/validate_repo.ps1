$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $RepoRoot

python3 Scripts/ci/scan_bidi_unicode.py $RepoRoot

Get-ChildItem -Path . -Recurse -File -Include *.json |
  Where-Object { $_.FullName -notmatch '\\.git\\' } |
  ForEach-Object {
    $content = Get-Content -Raw -Encoding UTF8 $_.FullName
    $null = $content | ConvertFrom-Json
    Write-Host "JSON OK: $($_.FullName)"
  }

Get-ChildItem -Path . -Recurse -File -Include *.jsonl |
  Where-Object { $_.FullName -notmatch '\\.git\\' } |
  ForEach-Object {
    $lineNo = 0
    Get-Content -Encoding UTF8 $_.FullName | ForEach-Object {
      $lineNo++
      $line = $_.Trim()
      if ($line.Length -eq 0) { return }
      try {
        $null = $line | ConvertFrom-Json
      }
      catch {
        throw "Invalid JSONL at $($_.FullName):$lineNo"
      }
    }
    Write-Host "JSONL OK: $($_.FullName)"
  }

Write-Host "validate_repo.ps1: PASS"
