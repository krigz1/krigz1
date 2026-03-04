$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path

python "$RootDir\Scripts\ci\scan_bidi_unicode.py" "$RootDir" --extensions ".json,.jsonl,.md,.txt,.yml,.yaml"

Write-Host "[validate_repo.ps1] JSON parse check..."

$fail = $false

function Test-JsonFile([string]$path) {
  try {
    $content = Get-Content -Raw -Encoding UTF8 $path
    $null = $content | ConvertFrom-Json
  } catch {
    Write-Host "[JSON ERROR] $path : $($_.Exception.Message)"
    $script:fail = $true
  }
}

function Test-JsonlFile([string]$path) {
  try {
    $lines = Get-Content -Encoding UTF8 $path
    $i = 0
    foreach ($line in $lines) {
      $i++
      $trim = $line.Trim()
      if ([string]::IsNullOrWhiteSpace($trim)) { continue }
      try {
        $null = $trim | ConvertFrom-Json
      } catch {
        Write-Host "[JSONL ERROR] $path:$i : $($_.Exception.Message)"
        $script:fail = $true
      }
    }
  } catch {
    Write-Host "[JSONL READ ERROR] $path : $($_.Exception.Message)"
    $script:fail = $true
  }
}

Get-ChildItem -Path $RootDir -Recurse -File | ForEach-Object {
  $p = $_.FullName
  if ($p.EndsWith(".json")) { Test-JsonFile $p }
  elseif ($p.EndsWith(".jsonl")) { Test-JsonlFile $p }
}

if ($fail) { exit 1 }
Write-Host "[validate_repo.ps1] OK"
