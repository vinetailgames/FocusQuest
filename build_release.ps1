$ErrorActionPreference = "Stop"
$projectRoot = [System.IO.Path]::GetFullPath($PSScriptRoot)
$versionFile = Join-Path $projectRoot "version.json"
$versionInfo = Get-Content -LiteralPath $versionFile -Raw | ConvertFrom-Json
$version = [string]$versionInfo.version
if ([string]::IsNullOrWhiteSpace($version) -or $version -notmatch '^[A-Za-z0-9._-]+$') {
    throw "version.json must contain a safe, non-empty version string."
}

$distRoot = Join-Path $projectRoot "dist"
$appDirectory = Join-Path $distRoot "FocusQuest"

$workRoot = Join-Path $projectRoot "build"
$null = New-Item -ItemType Directory -Path $distRoot -Force
$null = New-Item -ItemType Directory -Path $workRoot -Force
$workDirectory = Join-Path $workRoot (".focusquest-build-" + [guid]::NewGuid().ToString("N"))
$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"

function Remove-GitIgnoredBundleFiles {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$Bundle,
        [Parameter(Mandatory = $true)][string]$IgnorePathPrefix
    )

    $gitCommand = Get-Command git -ErrorAction SilentlyContinue
    if (-not $gitCommand) {
        throw "Git is required to exclude files matched by .gitignore."
    }

    $bundlePrefix = [System.IO.Path]::GetFullPath($Bundle).TrimEnd(
        [System.IO.Path]::DirectorySeparatorChar
    ) + [System.IO.Path]::DirectorySeparatorChar
    $bundleFiles = @(
        Get-ChildItem -LiteralPath $Bundle -Recurse -File -Force |
            ForEach-Object {
                $fullFilePath = [System.IO.Path]::GetFullPath($_.FullName)
                if (-not $fullFilePath.StartsWith(
                    $bundlePrefix,
                    [System.StringComparison]::OrdinalIgnoreCase
                )) {
                    throw "A release file is outside the bundle: $fullFilePath"
                }
                $relativePath = $fullFilePath.Substring($bundlePrefix.Length).Replace('\', '/')
                "$($IgnorePathPrefix.TrimEnd('/'))/$relativePath"
            }
    )
    if ($bundleFiles.Count -eq 0) {
        return
    }

    $gitProcessInfo = New-Object System.Diagnostics.ProcessStartInfo
    $gitProcessInfo.FileName = $gitCommand.Source
    $gitProcessInfo.WorkingDirectory = $Root
    $gitProcessInfo.Arguments = "check-ignore --no-index --stdin -z"
    $gitProcessInfo.UseShellExecute = $false
    $gitProcessInfo.RedirectStandardInput = $true
    $gitProcessInfo.RedirectStandardOutput = $true
    $gitProcessInfo.RedirectStandardError = $true
    $gitProcessInfo.CreateNoWindow = $true
    $gitProcess = New-Object System.Diagnostics.Process
    $gitProcess.StartInfo = $gitProcessInfo
    if (-not $gitProcess.Start()) {
        throw "Git could not evaluate .gitignore rules for the release bundle."
    }
    $stdoutTask = $gitProcess.StandardOutput.ReadToEndAsync()
    $stderrTask = $gitProcess.StandardError.ReadToEndAsync()
    try {
        foreach ($bundleFile in $bundleFiles) {
            $gitProcess.StandardInput.Write($bundleFile)
            $gitProcess.StandardInput.Write([char]0)
        }
    }
    finally {
        $gitProcess.StandardInput.Close()
    }
    $gitProcess.WaitForExit()
    $gitOutput = $stdoutTask.GetAwaiter().GetResult()
    $gitError = $stderrTask.GetAwaiter().GetResult()
    $gitExitCode = $gitProcess.ExitCode
    $gitProcess.Dispose()
    if ($gitExitCode -gt 1) {
        throw "Git could not evaluate .gitignore rules for the release bundle. $gitError"
    }
    $ignoredFiles = @($gitOutput -split [char]0 | Where-Object { $_ })

    $gitBundlePrefix = $IgnorePathPrefix.TrimEnd('/') + '/'
    foreach ($ignoredPath in $ignoredFiles) {
        if (-not $ignoredPath.StartsWith(
            $gitBundlePrefix,
            [System.StringComparison]::Ordinal
        )) {
            throw "Git returned an ignored path outside the release bundle: $ignoredPath"
        }
        $relativePath = $ignoredPath.Substring($gitBundlePrefix.Length)
        $windowsRelativePath = $relativePath.Replace('/', [System.IO.Path]::DirectorySeparatorChar)
        $filePath = [System.IO.Path]::GetFullPath((Join-Path $Bundle $windowsRelativePath))
        if (-not $filePath.StartsWith($bundlePrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Git returned an invalid ignored path for the release bundle: $ignoredPath"
        }
        if (Test-Path -LiteralPath $filePath -PathType Leaf) {
            Remove-Item -LiteralPath $filePath -Force
        }
    }

    if ($ignoredFiles.Count -gt 0) {
        Write-Host "Excluded $($ignoredFiles.Count) .gitignore-matched file(s) from the release bundle."
    }
}

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
        "--icon", (Join-Path $projectRoot "assets\icon\icon.ico"),
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
    if (-not (Test-Path -LiteralPath (Join-Path $appBundle "_internal"))) {
        throw "PyInstaller did not create the _internal runtime folder."
    }
    $pygameBaseExtension = Get-ChildItem `
        -LiteralPath (Join-Path $appBundle "_internal\pygame") `
        -Filter "base*.pyd" -File -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if (-not $pygameBaseExtension) {
        throw "The packaged app is missing pygame's base extension module."
    }

    Copy-Item -LiteralPath $versionFile -Destination (Join-Path $appBundle "version.json")
    Copy-Item -LiteralPath $updaterExecutable -Destination (Join-Path $appBundle "FocusQuestUpdater.exe")

    # Apply the repository's ignore rules to every file in the release bundle,
    # including assets and files added by future build steps.
    Remove-GitIgnoredBundleFiles `
        -Root $projectRoot `
        -Bundle $appBundle `
        -IgnorePathPrefix "dist/FocusQuest"
    if (-not (Test-Path -LiteralPath (Join-Path $appBundle "FocusQuest.exe"))) {
        throw "The release bundle is missing FocusQuest.exe after ignore filtering."
    }
    if (-not (Test-Path -LiteralPath (Join-Path $appBundle "FocusQuestUpdater.exe"))) {
        throw "The release bundle is missing FocusQuestUpdater.exe after ignore filtering."
    }
    if (-not (Test-Path -LiteralPath (Join-Path $appBundle "version.json"))) {
        throw "The release bundle is missing version.json after ignore filtering."
    }
    if (-not (Test-Path -LiteralPath (Join-Path $appBundle "_internal"))) {
        throw "The release bundle is missing _internal after ignore filtering."
    }
    $pygameBaseExtension = Get-ChildItem `
        -LiteralPath (Join-Path $appBundle "_internal\pygame") `
        -Filter "base*.pyd" -File -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if (-not $pygameBaseExtension) {
        throw "The release bundle is missing pygame's base extension module after ignore filtering."
    }

    $backupBundle = Join-Path $workDirectory "previous-FocusQuest"
    $hadPreviousBundle = Test-Path -LiteralPath $appDirectory
    if ($hadPreviousBundle) {
        Move-Item -LiteralPath $appDirectory -Destination $backupBundle
    }
    try {
        Move-Item -LiteralPath $appBundle -Destination $appDirectory
    }
    catch {
        if ($hadPreviousBundle -and (Test-Path -LiteralPath $backupBundle)) {
            Move-Item -LiteralPath $backupBundle -Destination $appDirectory
        }
        throw
    }

    Write-Host "Updated $appDirectory"
    Write-Host "Commit and push dist/FocusQuest together with version.json."
}
finally {
    if (Test-Path -LiteralPath $workDirectory) {
        $resolvedWorkRoot = [System.IO.Path]::GetFullPath($workRoot).TrimEnd('\') + '\'
        $resolvedWorkDirectory = [System.IO.Path]::GetFullPath($workDirectory)
        if ($resolvedWorkDirectory.StartsWith(
            $resolvedWorkRoot,
            [System.StringComparison]::OrdinalIgnoreCase
        )) {
            Remove-Item -LiteralPath $resolvedWorkDirectory -Recurse -Force
        }
    }
}
