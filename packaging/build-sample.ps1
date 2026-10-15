# Builds the shareable Windows sample: dist/ESI-Wiki-Sample/ESI-Wiki.exe
# Requires the venv deps plus:  pip install pyinstaller waitress
#
# Two flavours, from the same script:
#   .\packaging\build-sample.ps1                 keys embedded - the folder you hand over by hand
#   .\packaging\build-sample.ps1 -Keyless        bring your own key: reads the runner's environment
param([switch]$Keyless)
$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot/.."

if (-not (Test-Path "frontend/dist/index.html")) {
    Push-Location frontend
    npm run build
    Pop-Location
}

# Picks the repo venv when it exists, so PyInstaller/waitress resolve.
$python = if (Test-Path "backend-venv/Scripts/python.exe") { "backend-venv/Scripts/python.exe" } else { "python" }

# The dev database carries the mirrored EsiHub text. A sample you zip and share must not
# distribute other people's course documents, so PyInstaller bundles the stripped copy.
& $python packaging/strip-corpus.py

# packaging/embedded_keys.py is the file the spec compiles INTO the app when it exists: the .env
# provider keys, in the clear, because this build is the one you send to people you know. It is
# gitignored - staging it would put live keys in a public repo, where secret scanning reports them
# to the provider and they get revoked for everyone. See packaging/keys_embed.py.
$embedded = "packaging/embedded_keys.py"
if ($Keyless) {
    # The build that goes to strangers: your keys travel nowhere, and no account of yours spends
    # its quota on someone else's machine. The launcher leaves the runner's own environment alone,
    # and settings.py loads a .env placed next to the .exe - so whoever runs it brings their key.
    & $python packaging/keys_embed.py clear
    $env:WIKI_SAMPLE_DIR = "ESI-Wiki-Sample-Keyless"
    Write-Host "Keys    : -Keyless, nothing embedded. The sample answers from the local tables until"
    Write-Host "          the recipient sets GEMINI_API_KEY / NVIDIA_API_KEY / OPENROUTER_API_KEY"
    Write-Host "          (or OPENAI_API_KEY, which bills), or drops a .env next to the .exe."
} else {
    & $python packaging/keys_embed.py embed
    if (-not (Test-Path $embedded)) {
        Write-Host "Keys    : NONE embedded - .env is empty. This build will answer from the tables only."
    }
    $env:WIKI_SAMPLE_DIR = "ESI-Wiki-Sample"
}

& $python -m PyInstaller --noconfirm --clean packaging/esi-wiki-sample.spec

# The two flavours land in two folders: rebuilding one must not overwrite the other.
$sample = "dist/$env:WIKI_SAMPLE_DIR"

# A .env beside the .exe is the RECIPIENT'S channel in the -Keyless build, and nothing else. In the
# embedded build it would be a leftover from an older packaging, so it is removed - the folder you
# zip must carry the keys in one place only.
if (Test-Path "$sample/.env") {
    Remove-Item "$sample/.env" -Force
    Write-Host "Cleanup : removed a leftover .env from $sample - this build carries its keys inside."
}

# A recipient needs a file to fill in, not a paragraph in a README. Copy the repo's documented
# template next to the .exe - same file, so the sample can never drift away from the key forms the
# app checks. It stays a .env.EXAMPLE: settings.py only loads ".env", so nothing is read until the
# user copies it, pastes a key and restarts.
if ($Keyless -and (Test-Path ".env.example")) {
    Copy-Item ".env.example" "$sample/.env.example" -Force
    Write-Host "Fill in : $sample/.env.example - copy it to .env, paste one key, restart the .exe."
}

Write-Host ""
Write-Host "Sample  : $sample/ESI-Wiki.exe"
if (Test-Path $embedded) {
    Write-Host "Share   : zip the whole folder - the keys are in the .exe, nothing to configure."
    Write-Host "Recipients: people you hand it to. Whoever holds the folder holds the keys."
} else {
    Write-Host "Share   : keyless build - safe for strangers; they add their own key to use the AI."
}
Write-Host "Never   : git add dist/ or packaging/embedded_keys.py  -  the repo must stay key-free."
Write-Host "PDFs    : copy the repo's courses/ folder next to the .exe to serve the documents too."
