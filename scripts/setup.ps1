Write-Host "Setting up Mia..."

# 1. Defender exclusion for Mia folder
$MiaPath = Resolve-Path ".."
Write-Host "Adding Windows Defender exclusion for: $MiaPath"
try {
    Add-MpPreference -ExclusionPath $MiaPath -ErrorAction Stop
    Write-Host "Defender exclusion added successfully."
} catch {
    Write-Host "Failed to add Defender exclusion. Please run this script as Administrator." -ForegroundColor Yellow
}

# 2. Pull Ollama models
Write-Host "Pulling qwen2.5:7b model for fast local routing..."
ollama pull qwen2.5:7b

Write-Host "Pulling qwen2.5vl:7b model for local vision..."
ollama pull qwen2.5vl:7b

Write-Host "Mia setup complete."
