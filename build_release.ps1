param()

$ErrorActionPreference = "Stop"
$projectRoot = [System.IO.Path]::GetFullPath($PSScriptRoot)
$versionFile = Join-Path $projectRoot "version.json"
$versionInfo = Get-Content -LiteralPath $versionFile -Raw | ConvertFrom-Json
$version = [string]$versionInfo.version
if ([string]::IsNullOrWhiteSpace($version) -or $version -notmatch '^[A-Za-z0-9._-]+$') {
    throw "version.json must contain a safe, non-empty version string."
}

$outputRoot = Join-Path $projectRoot "release-output"
$releaseDirectory = Join-Path $outputRoot $version
$archiveName = "FocusQuest-$version-windows.zip"
$archivePath = Join-Path $releaseDirectory $archiveName
if (Test-Path -LiteralPath $releaseDirectory) {
    throw "Release output already exists at '$releaseDirectory'. Increment version.json before building another release."
}

$null = New-Item -ItemType Directory -Path $outputRoot -Force
$workDirectory = Join-Path $outputRoot (".build-" + [guid]::NewGuid().ToString("N"))
$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"

try {
    if (-not (Test-Path -LiteralPath $pythonPath)) {
        $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
        if (-not $pythonCommand) {
            throw "Python was not found. Install Python 3.13 and add it to PATH."
        }
        & $pythonCommand.Source -m venv (Join-Path $projectRoot ".venv")
        if ($LASTEXITCODE -ne 0) { throw "Could not create the .venv environment." }
    }

    $null = New-Item -ItemType Directory -Path $workDirectory
    & $pythonPath -m pip install --upgrade pip pygame pyinstaller
    if ($LASTEXITCODE -ne 0) { throw "Could not install the packaging dependencies." }

    $appDist = Join-Path $workDirectory "app-dist"
    $helperDist = Join-Path $workDirectory "helper-dist"
    $commonArgs = @("--noconfirm", "--clean")
    $appArgs = $commonArgs + @(
        "--windowed", "--onedir", "--name", "FocusQuest",
        "--distpath", $appDist,
        "--workpath", (Join-Path $workDirectory "app-work"),
        "--specpath", (Join-Path $workDirectory "app-spec"),
        "--add-data", ((Join-Path $projectRoot "assets") + ";assets"),
        (Join-Path $projectRoot "main.py")
    )
    & $pythonPath -m PyInstaller @appArgs
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller could not package FocusQuest." }

    $updaterArgs = $commonArgs + @(
        "--windowed", "--onefile", "--name", "FocusQuestUpdater",
        "--distpath", $helperDist,
        "--workpath", (Join-Path $workDirectory "updater-work"),
        "--specpath", (Join-Path $workDirectory "updater-spec"),
        (Join-Path $projectRoot "updater.py")
    )
    & $pythonPath -m PyInstaller @updaterArgs
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller could not package the update helper." }

    $appBundle = Join-Path $appDist "FocusQuest"
    $updaterExecutable = Join-Path $helperDist "FocusQuestUpdater.exe"
    if (-not (Test-Path -LiteralPath (Join-Path $appBundle "FocusQuest.exe"))) {
        throw "PyInstaller did not create FocusQuest.exe."
    }
    if (-not (Test-Path -LiteralPath $updaterExecutable)) {
        throw "PyInstaller did not create FocusQuestUpdater.exe."
    }

    Copy-Item -LiteralPath $versionFile -Destination (Join-Path $appBundle "version.json")
    Copy-Item -LiteralPath $updaterExecutable -Destination (Join-Path $appBundle "FocusQuestUpdater.exe")

    # Zip a parent directory so the archive contains FocusQuest/ at its root.
    $packageRoot = Join-Path $workDirectory "package"
    $null = New-Item -ItemType Directory -Path $packageRoot
    Copy-Item -LiteralPath $appBundle -Destination $packageRoot -Recurse
    $temporaryArchive = Join-Path $workDirectory $archiveName
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::CreateFromDirectory(
        $packageRoot,
        $temporaryArchive,
        [System.IO.Compression.CompressionLevel]::Optimal,
        $false
    )

    $null = New-Item -ItemType Directory -Path $releaseDirectory
    Move-Item -LiteralPath $temporaryArchive -Destination $archivePath
    Write-Host "Created $archivePath"
    Write-Host "This ZIP contains the Windows app folder and is ready for GitHub release upload."
}
finally {
    if (Test-Path -LiteralPath $workDirectory) {
        $resolvedOutputRoot = [System.IO.Path]::GetFullPath($outputRoot).TrimEnd('\') + '\'
        $resolvedWorkDirectory = [System.IO.Path]::GetFullPath($workDirectory)
        if ($resolvedWorkDirectory.StartsWith(
            $resolvedOutputRoot,
            [System.StringComparison]::OrdinalIgnoreCase
        )) {
            Remove-Item -LiteralPath $resolvedWorkDirectory -Recurse -Force
        }
    }
}
