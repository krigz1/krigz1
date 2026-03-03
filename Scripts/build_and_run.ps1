#!/usr/bin/env pwsh
param(
    [ValidateSet('editor','game','server')]
    [string]$Target = 'editor',
    [string]$Config = 'Development',
    [string]$RunArgs = '',
    [string]$UERoot = $env:UE_ROOT
)

$ErrorActionPreference = 'Stop'

if (-not $UERoot) {
    $UERoot = $env:UE5_ROOT
}

if (-not $UERoot) {
    throw "Set UE_ROOT (or UE5_ROOT), example: `$env:UE_ROOT='C:\UnrealEngine-5.3'"
}

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$UProject = Join-Path $RootDir 'LivingWorldMMO.uproject'
$BuildBat = Join-Path $UERoot 'Engine\Build\BatchFiles\Build.bat'
$EditorExe = Join-Path $UERoot 'Engine\Binaries\Win64\UnrealEditor.exe'

if (-not (Test-Path $BuildBat)) {
    throw "Build.bat not found: $BuildBat"
}

if (-not (Test-Path $EditorExe)) {
    throw "UnrealEditor.exe not found: $EditorExe"
}

switch ($Target) {
    'editor' {
        $TargetName = 'LivingWorldMMOEditor'
        $RunCommand = "`"$EditorExe`" `"$UProject`" $RunArgs"
    }
    'game' {
        $TargetName = 'LivingWorldMMO'
        $RunCommand = "`"$EditorExe`" `"$UProject`" -game $RunArgs"
    }
    'server' {
        $TargetName = 'LivingWorldMMO'
        $RunCommand = "`"$EditorExe`" `"$UProject`" -server -log $RunArgs"
    }
}

Write-Host "[1/3] Generating project files..."
& $EditorExe $UProject -projectfiles -game -engine -progress | Out-Null

Write-Host "[2/3] Building $TargetName ($Config)..."
& $BuildBat $TargetName Win64 $Config $UProject -NoHotReloadFromIDE -Progress

Write-Host "[3/3] Running: $RunCommand"
Invoke-Expression $RunCommand
