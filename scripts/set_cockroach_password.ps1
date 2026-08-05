param(
    [string]$EnvPath = (Join-Path $PSScriptRoot "..\.env")
)

$resolvedEnvPath = [System.IO.Path]::GetFullPath($EnvPath)
if (-not (Test-Path -LiteralPath $resolvedEnvPath)) {
    throw "No .env file found at $resolvedEnvPath"
}

$securePassword = Read-Host "Paste the newly generated engram_app password" -AsSecureString
$passwordPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)

try {
    $plainPassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($passwordPointer)
    $encodedPassword = [Uri]::EscapeDataString($plainPassword)
    $content = [System.IO.File]::ReadAllText($resolvedEnvPath)
    $pattern = '(?m)^DATABASE_URL=postgresql\+psycopg://engram_app:[^@]*@'
    $replacement = 'DATABASE_URL=postgresql+psycopg://engram_app:' + $encodedPassword + '@'
    $updated = [regex]::Replace($content, $pattern, $replacement, 1)

    if ($updated -eq $content) {
        throw "DATABASE_URL was not in the expected engram_app format. Do not modify the file automatically."
    }

    [System.IO.File]::WriteAllText($resolvedEnvPath, $updated, [System.Text.UTF8Encoding]::new($false))
    Write-Host "Updated the local .env password safely. The password was not displayed."
}
finally {
    if ($passwordPointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($passwordPointer)
    }
    Remove-Variable plainPassword, encodedPassword -ErrorAction SilentlyContinue
}
