param (
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet("patch", "minor", "major")]
    [string]$BumpType,

    [Alias("d")]
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Write-Step ([string]$Message) {
    Write-Host "`n>> $Message" -ForegroundColor Cyan
}

function Write-Success ([string]$Message) {
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-WarningMsg ([string]$Message) {
    Write-Host "⚠️ $Message" -ForegroundColor Yellow
}

$PyProjectFile = Join-Path $PSScriptRoot "pyproject.toml"

if (-not (Test-Path $PyProjectFile)) {
    throw "pyproject.toml not found at $PyProjectFile"
}

# 1. Read current version
$Content = Get-Content $PyProjectFile -Raw
if ($Content -match 'version\s*=\s*"([^"]+)"') {
    $CurrentVersion = $Matches[1]
    Write-Step "Current version: $CurrentVersion"
}
else {
    throw "Could not find version in pyproject.toml"
}

# 2. Calculate new version
$v = [version]$CurrentVersion
$Major = $v.Major
$Minor = $v.Minor
$Patch = $v.Build
if ($Patch -lt 0) { $Patch = $v.Revision }
if ($Patch -lt 0) { $Patch = 0 }

switch ($BumpType) {
    "major" { $Major++; $Minor = 0; $Patch = 0 }
    "minor" { $Minor++; $Patch = 0 }
    "patch" { $Patch++ }
}

$NewVersion = "$Major.$Minor.$Patch"
Write-Step "New version: $NewVersion"

if ($DryRun) {
    Write-WarningMsg "DRY RUN: Skipping version update and publication."
}
else {
    # 3. Update pyproject.toml
    $NewContent = $Content -replace '(version\s*=\s*)"[^"]+"', "`$1`"$NewVersion`""
    Set-Content $PyProjectFile $NewContent
    Write-Success "Updated pyproject.toml to version $NewVersion"

    # 4. Build package
    Write-Step "Building package..."
    if (Test-Path "dist") { Remove-Item "dist" -Recurse -Force }
    uv build

    # 5. Publish to PyPI
    Write-Step "Publishing to PyPI..."
    # Using 'uv run' to ensure twine is available even if not in the global env
    uv run --with twine twine upload dist/*
    
    Write-Success "Published version $NewVersion to PyPI!"
}
