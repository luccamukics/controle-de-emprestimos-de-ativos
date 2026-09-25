$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

python -m pip install -r requirements.txt "pyinstaller>=6.17,<7"
if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar as dependencias." }

python -m PyInstaller --noconfirm --clean --onedir --windowed --name ControleEmprestimos main.py
if ($LASTEXITCODE -ne 0) { throw "Falha ao gerar o executavel." }

$destino = Join-Path $PSScriptRoot "dist\ControleEmprestimos"
Copy-Item "TERMO_RESPONSABILIDADE_MODELO.docx" $destino -Force
Copy-Item "TERMO_DEVOLUCAO_MODELO.docx" $destino -Force
Copy-Item ".env.exemplo" $destino -Force

if (Test-Path (Join-Path $destino ".env")) {
    throw "Por seguranca, o pacote nao pode conter um .env com credenciais."
}
if (-not (Test-Path (Join-Path $destino "ControleEmprestimos.exe"))) {
    throw "O executavel nao foi criado."
}
$verificacao = Start-Process -FilePath (Join-Path $destino "ControleEmprestimos.exe") `
    -ArgumentList "--verificar-pacote" -Wait -PassThru
if ($verificacao.ExitCode -ne 0) {
    throw "O executavel nao passou na verificacao de recursos."
}
Write-Host "Pronto: $destino\ControleEmprestimos.exe"
Write-Host "Copie .env.exemplo para .env nessa pasta e configure o MySQL."
