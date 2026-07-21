param(
    [switch]$SkipOllamaCheck = $false
)

Write-Host "Mia Model Setup Script" -ForegroundColor Cyan

if (-not $SkipOllamaCheck) {
    if (Get-Command ollama -ErrorAction SilentlyContinue) {
        Write-Host "Ollama is installed." -ForegroundColor Green
    } else {
        Write-Host "Ollama is not installed or not in PATH. Please install it from https://ollama.com/" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`nPulling qwen2.5:7b..." -ForegroundColor Yellow
ollama pull qwen2.5:7b

Write-Host "`nPulling qwen2.5vl:7b..." -ForegroundColor Yellow
ollama pull qwen2.5vl:7b

Write-Host "`nOllama models pulled successfully!" -ForegroundColor Green

Write-Host "`nNote: faster-whisper and piper-tts models will be downloaded automatically on first run." -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
